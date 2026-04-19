from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models.system import SystemSetting
from app.schemas.system import SystemSettingResponse, SystemSettingsBulkUpdate

router = APIRouter()

@router.get("/", response_model=list[SystemSettingResponse])
async def get_settings(db: AsyncSession = Depends(get_db_session)) -> list[SystemSetting]:
    """Get all system settings."""
    result = await db.execute(select(SystemSetting))
    return list(result.scalars().all())

@router.post("/", response_model=list[SystemSettingResponse])
async def update_settings(
    update_data: SystemSettingsBulkUpdate,
    db: AsyncSession = Depends(get_db_session)
) -> list[SystemSetting]:
    """Bulk update or create system settings."""
    # Fetch existing
    result = await db.execute(select(SystemSetting).where(SystemSetting.key.in_(update_data.settings.keys())))
    existing_settings = {s.key: s for s in result.scalars().all()}
    
    updated_or_created = []
    
    for key, value in update_data.settings.items():
        if key in existing_settings:
            existing_settings[key].value = value
            updated_or_created.append(existing_settings[key])
        else:
            new_setting = SystemSetting(key=key, value=value)
            db.add(new_setting)
            updated_or_created.append(new_setting)
            
    await db.commit()
    
    # Return updated list for the requested keys
    result = await db.execute(select(SystemSetting).where(SystemSetting.key.in_(update_data.settings.keys())))
    return list(result.scalars().all())
