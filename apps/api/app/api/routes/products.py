from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db_session
from app.models import Product, ProductContentSettings
from app.schemas.product import (
    ProductContentSettingsRead,
    ProductContentSettingsUpdate,
    ProductCreate,
    ProductRead,
    ProductUpdate,
)


router = APIRouter()


@router.get("", response_model=list[ProductRead])
async def list_products(
    session: AsyncSession = Depends(get_db_session),
) -> list[Product]:
    statement = select(Product).options(
        selectinload(Product.content_settings),
        selectinload(Product.channels),
        selectinload(Product.monitoring_sources)
    ).order_by(Product.created_at.desc())
    result = await session.execute(statement)
    return list(result.scalars().unique().all())


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    session: AsyncSession = Depends(get_db_session),
) -> Product:
    existing = await session.scalar(select(Product).where(Product.slug == payload.slug))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Product slug already exists.")

    product = Product(
        name=payload.name,
        slug=payload.slug,
        category=payload.category,
        lifecycle_stage=payload.lifecycle_stage,
        short_description=payload.short_description,
        full_description=payload.full_description,
        target_audience=payload.target_audience,
        audience_segments=payload.audience_segments,
        pain_points=payload.pain_points,
        value_proposition=payload.value_proposition,
        key_features=payload.key_features,
        content_pillars=payload.content_pillars,
        strategic_goals=payload.strategic_goals,
        primary_channels=payload.primary_channels,
        tone_of_voice=payload.tone_of_voice,
        cta_strategy=payload.cta_strategy,
        website_url=payload.website_url,
        blog_base_url=payload.blog_base_url,
        is_active=payload.is_active,
    )
    product.content_settings = ProductContentSettings(**payload.content_settings.model_dump())
    session.add(product)
    await session.commit()
    await session.refresh(product, attribute_names=["content_settings", "channels", "monitoring_sources"])
    return product


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> Product:
    statement = (
        select(Product)
        .where(Product.id == product_id)
        .options(
            selectinload(Product.content_settings),
            selectinload(Product.channels),
            selectinload(Product.monitoring_sources)
        )
    )
    product = await session.scalar(statement)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return product


@router.patch("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: UUID,
    payload: ProductUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> Product:
    statement = (
        select(Product)
        .where(Product.id == product_id)
        .options(
            selectinload(Product.content_settings),
            selectinload(Product.channels),
            selectinload(Product.monitoring_sources)
        )
    )
    product = await session.scalar(statement)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    for field_name, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field_name, value)

    await session.commit()
    await session.refresh(product, attribute_names=["content_settings", "channels", "monitoring_sources"])
    return product


@router.get("/{product_id}/settings", response_model=ProductContentSettingsRead)
async def get_product_settings(
    product_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> ProductContentSettings:
    statement = select(ProductContentSettings).where(ProductContentSettings.product_id == product_id)
    settings = await session.scalar(statement)
    if settings is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product settings not found.")
    return settings


@router.patch("/{product_id}/settings", response_model=ProductContentSettingsRead)
async def update_product_settings(
    product_id: UUID,
    payload: ProductContentSettingsUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> ProductContentSettings:
    statement = select(ProductContentSettings).where(ProductContentSettings.product_id == product_id)
    settings = await session.scalar(statement)
    if settings is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product settings not found.")

    for field_name, value in payload.model_dump(exclude_unset=True).items():
        setattr(settings, field_name, value)

    await session.commit()
    await session.refresh(settings)
    return settings
