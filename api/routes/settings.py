import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db
from api.core.security import get_current_user
from api.models.models import SystemSetting, User
from api.schemas.schemas import SystemSettingResponse, SystemSettingUpdate

router = APIRouter(prefix="/settings", tags=["System Settings"])


@router.get("/", response_model=List[SystemSettingResponse])
async def list_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all system settings. Admin only."""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view settings"
        )
    
    result = await db.execute(select(SystemSetting))
    settings = result.scalars().all()
    return settings


@router.get("/{key}", response_model=SystemSettingResponse)
async def get_setting(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific setting by key. Admin only."""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view settings"
        )
    
    result = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
    setting = result.scalar_one_or_none()
    
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting '{key}' not found"
        )
    
    return setting


@router.put("/", response_model=SystemSettingResponse)
async def update_setting(
    setting_data: SystemSettingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create or update a system setting. Admin only."""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update settings"
        )
    
    # Check if setting exists
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == setting_data.key)
    )
    setting = result.scalar_one_or_none()
    
    if setting:
        # Update existing setting
        setting.value = setting_data.value
    else:
        # Create new setting
        setting = SystemSetting(
            key=setting_data.key,
            value=setting_data.value
        )
        db.add(setting)
    
    await db.commit()
    await db.refresh(setting)
    
    return setting


@router.post("/batch", response_model=List[SystemSettingResponse])
async def batch_update_settings(
    settings: List[SystemSettingUpdate],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update multiple settings at once. Admin only."""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update settings"
        )
    
    updated_settings = []
    
    for setting_data in settings:
        # Check if setting exists
        result = await db.execute(
            select(SystemSetting).where(SystemSetting.key == setting_data.key)
        )
        setting = result.scalar_one_or_none()
        
        if setting:
            setting.value = setting_data.value
        else:
            setting = SystemSetting(
                key=setting_data.key,
                value=setting_data.value
            )
            db.add(setting)
        
        updated_settings.append(setting)
    
    await db.commit()
    
    # Refresh all settings
    for setting in updated_settings:
        await db.refresh(setting)
    
    return updated_settings


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_setting(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a system setting. Admin only."""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete settings"
        )
    
    result = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
    setting = result.scalar_one_or_none()
    
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting '{key}' not found"
        )
    
    await db.delete(setting)
    await db.commit()
    
    return None
