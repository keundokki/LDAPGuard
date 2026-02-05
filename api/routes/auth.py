from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.config import settings
from api.core.database import get_db
from api.core.security import (
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
)
from api.models.models import User
from api.schemas.schemas import (
    LoginRequest,
    Token,
    UserCreate,
    UserResponse,
    UserUpdate,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
@limiter.limit("3/hour")
async def register(
    request: Request, user_data: UserCreate, db: AsyncSession = Depends(get_db)
):
    """Register a new user. Rate limited to 3 registrations per hour."""
    # Check if username exists
    result = await db.execute(select(User).where(User.username == user_data.username))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_email = result.scalar_one_or_none()

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role,
        ldap_auth=user_data.ldap_auth,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(
    request: Request, login_data: LoginRequest, db: AsyncSession = Depends(get_db)
):
    """Login and get access token. Rate limited to 5 attempts per minute."""
    # Get user
    result = await db.execute(select(User).where(User.username == login_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled"
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value},
        expires_delta=access_token_expires,
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information."""
    return current_user


@router.get("/users/", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """List all users (admin only)."""
    # Only admins can list users
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can list users",
        )

    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return users


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a user (admin only)."""
    # Only admins can update users
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update users",
        )

    # Get user to update
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Prevent admin from disabling themselves
    if user.id == current_user.id and user_data.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot disable your own account",
        )

    # Update fields if provided
    if user_data.email is not None:
        # Check if email is already taken by another user
        result = await db.execute(
            select(User).where(User.email == user_data.email, User.id != user_id)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use"
            )
        user.email = user_data.email

    if user_data.full_name is not None:
        user.full_name = user_data.full_name

    if user_data.role is not None:
        # Prevent admin from demoting themselves
        if user.id == current_user.id and user_data.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change your own role",
            )
        user.role = user_data.role

    if user_data.is_active is not None:
        user.is_active = user_data.is_active

    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a user (admin only)."""
    # Only admins can delete users
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete users",
        )

    # Get user to delete
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Prevent admin from deleting themselves
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    await db.delete(user)
    await db.commit()
    return None
