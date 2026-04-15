from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models import BrandProfile
from app.schemas.brand_profile import BrandProfileRead, BrandProfileUpsert


router = APIRouter()


@router.get("", response_model=BrandProfileRead | None)
async def get_brand_profile(
    session: AsyncSession = Depends(get_db_session),
) -> BrandProfile | None:
    return await session.scalar(select(BrandProfile).limit(1))


@router.put("", response_model=BrandProfileRead, status_code=status.HTTP_200_OK)
async def upsert_brand_profile(
    payload: BrandProfileUpsert,
    session: AsyncSession = Depends(get_db_session),
) -> BrandProfile:
    profile = await session.scalar(select(BrandProfile).limit(1))
    if profile is None:
        profile = BrandProfile(**payload.model_dump())
        session.add(profile)
    else:
        for field_name, value in payload.model_dump().items():
            setattr(profile, field_name, value)

    await session.commit()
    await session.refresh(profile)
    return profile

