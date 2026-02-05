from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.config import settings
from api.core.database import get_db
from api.core.encryption import AESEncryption
from api.core.security import get_current_user
from api.models.models import LDAPServer
from api.schemas.schemas import LDAPServerCreate, LDAPServerResponse, LDAPServerUpdate
from api.services.ldap_service import LDAPService

router = APIRouter(prefix="/ldap-servers", tags=["LDAP Servers"])

# Initialize encryption service
encryption = AESEncryption(settings.ENCRYPTION_KEY)


class LDAPTestConnection(BaseModel):
    """Schema for testing LDAP connection."""

    host: str
    port: int
    use_ssl: bool = False
    base_dn: str
    bind_dn: str | None = None
    bind_password: str | None = None


@router.get("/", response_model=List[LDAPServerResponse])
async def list_ldap_servers(db: AsyncSession = Depends(get_db)):
    """List all LDAP servers."""
    result = await db.execute(select(LDAPServer))
    servers = result.scalars().all()
    return servers


@router.get("/{server_id}", response_model=LDAPServerResponse)
async def get_ldap_server(server_id: int, db: AsyncSession = Depends(get_db)):
    """Get LDAP server by ID."""
    result = await db.execute(select(LDAPServer).where(LDAPServer.id == server_id))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="LDAP server not found"
        )

    return server


@router.post(
    "/", response_model=LDAPServerResponse, status_code=status.HTTP_201_CREATED
)
async def create_ldap_server(
    server_data: LDAPServerCreate,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Create a new LDAP server configuration."""
    # Check if name exists
    result = await db.execute(
        select(LDAPServer).where(LDAPServer.name == server_data.name)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LDAP server with this name already exists",
        )

    # Test connection before saving
    ldap_service = LDAPService(
        host=server_data.host,
        port=server_data.port,
        use_ssl=server_data.use_ssl,
        bind_dn=server_data.bind_dn,
        bind_password=server_data.bind_password,
        base_dn=server_data.base_dn,
    )

    if not ldap_service.test_connection():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to connect to LDAP server. Check credentials and settings.",
        )

    # Encrypt bind password if provided
    server_dict = server_data.model_dump()
    if server_dict.get("bind_password"):
        encrypted_password = encryption.encrypt(server_dict["bind_password"].encode())
        server_dict["bind_password"] = encrypted_password
        server_dict["password_encrypted"] = True
    else:
        server_dict["password_encrypted"] = False

    new_server = LDAPServer(**server_dict)
    db.add(new_server)
    await db.commit()
    await db.refresh(new_server)

    return new_server


@router.put("/{server_id}", response_model=LDAPServerResponse)
async def update_ldap_server(
    server_id: int,
    server_data: LDAPServerUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Update LDAP server configuration."""
    result = await db.execute(select(LDAPServer).where(LDAPServer.id == server_id))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="LDAP server not found"
        )

    # Update fields with encryption for password
    update_data = server_data.model_dump(exclude_unset=True)

    # Encrypt password if provided
    if "bind_password" in update_data and update_data["bind_password"]:
        encrypted_password = encryption.encrypt(update_data["bind_password"].encode())
        update_data["bind_password"] = encrypted_password
        update_data["password_encrypted"] = True

    for field, value in update_data.items():
        setattr(server, field, value)

    await db.commit()
    await db.refresh(server)

    return server


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ldap_server(server_id: int, db: AsyncSession = Depends(get_db)):
    """Delete LDAP server configuration."""
    result = await db.execute(select(LDAPServer).where(LDAPServer.id == server_id))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="LDAP server not found"
        )

    await db.delete(server)
    await db.commit()

    return None


@router.post("/test")
async def test_ldap_connection(
    test_data: LDAPTestConnection,
    _current_user=Depends(get_current_user),
):
    """Test LDAP connection with provided credentials."""
    try:
        # Create a temporary service instance to test the connection
        ldap_service = LDAPService(
            host=test_data.host,
            port=test_data.port,
            use_ssl=test_data.use_ssl,
            base_dn=test_data.base_dn,
            bind_dn=test_data.bind_dn,
            bind_password=test_data.bind_password,
        )

        # Try to connect and get basic info
        entries = ldap_service.search_all_entries(
            search_filter="(objectClass=*)"
        )

        entry_count = len(entries) if entries else 0

        return {
            "status": "success",
            "message": f"Successfully connected. Found {entry_count} entries.",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Connection test failed: {str(e)}",
        )
