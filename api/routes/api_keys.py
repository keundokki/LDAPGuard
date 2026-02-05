import secrets
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db
from api.core.security import get_current_user
from api.models.models import APIKey, User
from api.schemas.schemas import APIKeyCreate, APIKeyResponse, APIKeyWithSecret

router = APIRouter(prefix="/api-keys", tags=["API Keys"])

# For hashing API keys
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_api_key() -> str:
    """Generate a secure API key."""
    return f"ldapg_{secrets.token_urlsafe(32)}"


@router.get("/", response_model=List[APIKeyResponse])
async def list_api_keys(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all API keys. Admin only."""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manage API keys",
        )

    result = await db.execute(
        select(APIKey).offset(skip).limit(limit).order_by(APIKey.created_at.desc())
    )
    keys = result.scalars().all()
    return keys


@router.post("/", response_model=APIKeyWithSecret, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new API key. Admin only."""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create API keys",
        )

    # Generate API key
    api_key = generate_api_key()
    key_hash = pwd_context.hash(api_key)
    key_prefix = api_key[:10]  # Store prefix for display

    # Calculate expiration
    expires_at = None
    if key_data.expires_days:
        expires_at = datetime.utcnow() + timedelta(days=key_data.expires_days)

    # Create API key record
    new_key = APIKey(
        name=key_data.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        permissions=key_data.permissions,
        created_by=current_user.id,
        expires_at=expires_at,
        is_active=True,
    )

    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)

    # Return response with the actual API key (only shown once)
    response = APIKeyWithSecret(
        id=new_key.id,
        name=new_key.name,
        key_prefix=new_key.key_prefix,
        permissions=new_key.permissions,
        created_by=new_key.created_by,
        expires_at=new_key.expires_at,
        last_used_at=new_key.last_used_at,
        is_active=new_key.is_active,
        created_at=new_key.created_at,
        api_key=api_key,  # Only shown on creation
    )

    return response


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an API key. Admin only."""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete API keys",
        )

    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
        )

    await db.delete(api_key)
    await db.commit()

    return None


@router.patch("/{key_id}/revoke", response_model=APIKeyResponse)
async def revoke_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revoke (deactivate) an API key. Admin only."""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can revoke API keys",
        )

    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
        )

    api_key.is_active = False
    await db.commit()
    await db.refresh(api_key)

    return api_key
