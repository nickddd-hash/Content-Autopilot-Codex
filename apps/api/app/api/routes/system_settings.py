from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models.system import SystemSetting
from app.schemas.system import SystemSettingRead, SystemSettingsUpdatePayload


router = APIRouter()


@router.get("/system", response_model=list[SystemSettingRead])
async def get_system_settings(
    session: AsyncSession = Depends(get_db_session),
) -> list[SystemSettingRead]:
    statement = select(SystemSetting).order_by(SystemSetting.key.asc())
    settings = (await session.scalars(statement)).all()
    return [
        SystemSettingRead(
            key=setting.key,
            value=setting.value,
            description=setting.description,
        )
        for setting in settings
    ]


@router.patch("/system", response_model=list[SystemSettingRead])
async def update_system_settings(
    payload: SystemSettingsUpdatePayload,
    session: AsyncSession = Depends(get_db_session),
) -> list[SystemSettingRead]:
    for item in payload.settings:
        normalized_key = item.key.strip()
        if not normalized_key:
            continue

        existing = await session.scalar(select(SystemSetting).where(SystemSetting.key == normalized_key))
        if existing is None:
            existing = SystemSetting(
                key=normalized_key,
                value=item.value,
                description=item.description,
            )
            session.add(existing)
        else:
            existing.value = item.value
            if item.description is not None:
                existing.description = item.description

    await session.commit()

    statement = select(SystemSetting).order_by(SystemSetting.key.asc())
    settings = (await session.scalars(statement)).all()
    return [
        SystemSettingRead(
            key=setting.key,
            value=setting.value,
            description=setting.description,
        )
        for setting in settings
    ]
