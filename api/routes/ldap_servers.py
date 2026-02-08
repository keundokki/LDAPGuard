import logging
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

logger = logging.getLogger(__name__)

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
    current_user=Depends(get_current_user),
):
    """Create a new LDAP server configuration."""
    # Only admins and operators can create LDAP servers
    if current_user.role.value not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and operators can create LDAP servers",
        )

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
            detail="Failed to connect to LDAP server. "
            "Please check your credentials and connection settings.",
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
    current_user=Depends(get_current_user),
):
    """Update LDAP server configuration."""
    # Only admins and operators can update LDAP servers
    if current_user.role.value not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and operators can update LDAP servers",
        )

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
async def delete_ldap_server(
    server_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete LDAP server configuration."""
    # Only admins and operators can delete LDAP servers
    if current_user.role.value not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and operators can delete LDAP servers",
        )

    try:
        from sqlalchemy import text

        # First check if server exists using raw SQL to avoid loading into session
        check_result = await db.execute(
            text("SELECT id FROM ldap_servers WHERE id = :server_id"),
            {"server_id": server_id},
        )
        if not check_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="LDAP server not found"
            )

        # Delete restore jobs first
        await db.execute(
            text("DELETE FROM restore_jobs WHERE ldap_server_id = :server_id"),
            {"server_id": server_id},
        )
        # Delete scheduled backups
        await db.execute(
            text("DELETE FROM scheduled_backups WHERE ldap_server_id = :server_id"),
            {"server_id": server_id},
        )
        # Delete backups
        await db.execute(
            text("DELETE FROM backups WHERE ldap_server_id = :server_id"),
            {"server_id": server_id},
        )
        # Delete the LDAP server
        await db.execute(
            text("DELETE FROM ldap_servers WHERE id = :server_id"),
            {"server_id": server_id},
        )

        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        logger.exception(f"Error deleting LDAP server {server_id}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete LDAP server: {str(e)}",
        )

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

        # Try to connect and bind; avoid search to keep test lightweight
        if not ldap_service.test_connection():
            raise Exception("LDAP bind failed")

        return {
            "status": "success",
            "message": "Successfully connected to LDAP server.",
        }

    except Exception as e:
        logger.exception("LDAP connection test failed")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Connection test failed: {str(e)}",
        )
