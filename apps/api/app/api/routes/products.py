from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db_session
from app.models import Product, ProductChannel, ProductContentSettings
from app.schemas.product import (
    ProductChannelCreate,
    ProductChannelRead,
    ProductChannelUpdate,
    ProductContentSettingsRead,
    ProductContentSettingsUpdate,
    ProductCreate,
    ProductRead,
    ProductUpdate,
)
from app.services.channel_validation import ChannelValidationError, validate_channel_connection


router = APIRouter()


@router.get("", response_model=list[ProductRead])
async def list_products(
    session: AsyncSession = Depends(get_db_session),
) -> list[Product]:
    statement = select(Product).options(selectinload(Product.content_settings), selectinload(Product.channels)).order_by(Product.created_at.desc())
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
    await session.refresh(product, attribute_names=["content_settings", "channels"])
    return product


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> Product:
    statement = (
        select(Product)
        .where(Product.id == product_id)
        .options(selectinload(Product.content_settings), selectinload(Product.channels))
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
        .options(selectinload(Product.content_settings), selectinload(Product.channels))
    )
    product = await session.scalar(statement)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    for field_name, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field_name, value)

    await session.commit()
    await session.refresh(product, attribute_names=["content_settings", "channels"])
    return product


@router.get("/{product_id}/channels", response_model=list[ProductChannelRead])
async def list_product_channels(
    product_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> list[ProductChannel]:
    statement = select(ProductChannel).where(ProductChannel.product_id == product_id).order_by(ProductChannel.created_at.asc())
    result = await session.execute(statement)
    return list(result.scalars().all())


@router.post("/{product_id}/channels", response_model=ProductChannelRead, status_code=status.HTTP_201_CREATED)
async def create_product_channel(
    product_id: UUID,
    payload: ProductChannelCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ProductChannel:
    product = await session.scalar(select(Product).where(Product.id == product_id).options(selectinload(Product.channels)))
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    normalized_platform = payload.platform.strip().lower()
    if normalized_platform not in {"telegram", "vk"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only Telegram and VK are supported for channel connection now.")

    existing_channel = next((channel for channel in product.channels if channel.platform == normalized_platform), None)
    if existing_channel is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This platform is already connected for the product.")

    channel = ProductChannel(
        product_id=product.id,
        platform=normalized_platform,
        name=(payload.name or normalized_platform).strip(),
        secrets_json=payload.secrets,
        settings_json=payload.settings,
        validation_status="pending",
        is_active=True,
    )
    session.add(channel)
    product.primary_channels = sorted({*(product.primary_channels or []), normalized_platform})
    await session.commit()
    await session.refresh(channel)
    return channel


@router.patch("/{product_id}/channels/{channel_id}", response_model=ProductChannelRead)
async def update_product_channel(
    product_id: UUID,
    channel_id: UUID,
    payload: ProductChannelUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> ProductChannel:
    statement = select(ProductChannel).where(ProductChannel.id == channel_id, ProductChannel.product_id == product_id)
    channel = await session.scalar(statement)
    if channel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found.")

    if payload.name is not None:
        channel.name = payload.name.strip() or channel.name
    if payload.secrets is not None:
        channel.secrets_json = payload.secrets
    if payload.settings is not None:
        channel.settings_json = payload.settings

    channel.validation_status = "pending"
    channel.validation_message = "Данные обновлены. Канал ждёт повторной проверки."
    channel.validated_at = None
    channel.external_id = None
    channel.external_name = None

    await session.commit()
    await session.refresh(channel)
    return channel


@router.post("/{product_id}/channels/{channel_id}/validate", response_model=ProductChannelRead)
async def validate_product_channel(
    product_id: UUID,
    channel_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> ProductChannel:
    statement = select(ProductChannel).where(ProductChannel.id == channel_id, ProductChannel.product_id == product_id)
    channel = await session.scalar(statement)
    if channel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found.")

    try:
        external_id, external_name = await validate_channel_connection(channel.platform, channel.secrets_json, channel.settings_json)
        channel.external_id = external_id
        channel.external_name = external_name
        channel.validation_status = "valid"
        channel.validation_message = "Связь установлена. Канал готов к автопостингу."
        channel.validated_at = datetime.now(timezone.utc)
    except ChannelValidationError as error:
        channel.validation_status = "invalid"
        channel.validation_message = str(error)
        channel.validated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(channel)
    return channel


@router.delete("/{product_id}/channels/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_channel(
    product_id: UUID,
    channel_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> None:
    product = await session.scalar(select(Product).where(Product.id == product_id).options(selectinload(Product.channels)))
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    channel = next((item for item in product.channels if item.id == channel_id), None)
    if channel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found.")

    await session.delete(channel)
    remaining_platforms = [item.platform for item in product.channels if item.id != channel_id and item.is_active]
    product.primary_channels = sorted(set(remaining_platforms))
    await session.commit()


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
