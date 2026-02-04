from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db
from api.models.models import LDAPServer
from api.schemas.schemas import LDAPServerCreate, LDAPServerResponse, LDAPServerUpdate

router = APIRouter(prefix="/ldap-servers", tags=["LDAP Servers"])


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
    server_data: LDAPServerCreate, db: AsyncSession = Depends(get_db)
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

    new_server = LDAPServer(**server_data.model_dump())
    db.add(new_server)
    await db.commit()
    await db.refresh(new_server)

    return new_server


@router.put("/{server_id}", response_model=LDAPServerResponse)
async def update_ldap_server(
    server_id: int, server_data: LDAPServerUpdate, db: AsyncSession = Depends(get_db)
):
    """Update LDAP server configuration."""
    result = await db.execute(select(LDAPServer).where(LDAPServer.id == server_id))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="LDAP server not found"
        )

    # Update fields
    for field, value in server_data.model_dump(exclude_unset=True).items():
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
