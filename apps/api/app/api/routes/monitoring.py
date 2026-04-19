from __future__ import annotations

import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models import Product
from app.models.monitoring import Channel, IngestedContent, MonitoringSource
from app.schemas.monitoring import (
    ChannelCreate,
    ChannelRead,
    MonitoringSourceCreate,
    MonitoringSourceRead,
)
from app.services.monitoring import run_apify_scraper

router = APIRouter()


# ── Channels ──────────────────────────────────────────────────────────────────

@router.get("/{product_id}/channels", response_model=list[ChannelRead])
async def list_channels(
    product_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> list[Channel]:
    result = await session.execute(
        select(Channel).where(Channel.product_id == product_id)
    )
    return list(result.scalars().all())


@router.post("/{product_id}/channels", response_model=ChannelRead, status_code=status.HTTP_201_CREATED)
async def create_channel(
    product_id: UUID,
    payload: ChannelCreate,
    session: AsyncSession = Depends(get_db_session),
) -> Channel:
    product = await session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    channel = Channel(
        product_id=product_id,
        platform=payload.platform,
        name=payload.name,
        credentials=payload.credentials,
    )
    session.add(channel)
    await session.commit()
    await session.refresh(channel)
    return channel


@router.delete("/{product_id}/channels/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(
    product_id: UUID,
    channel_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> None:
    channel = await session.get(Channel, channel_id)
    if not channel or channel.product_id != product_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found.")
    await session.delete(channel)
    await session.commit()


# ── Monitoring Sources ─────────────────────────────────────────────────────────

@router.get("/{product_id}/monitoring-sources", response_model=list[MonitoringSourceRead])
async def list_monitoring_sources(
    product_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> list[MonitoringSource]:
    result = await session.execute(
        select(MonitoringSource).where(MonitoringSource.product_id == product_id)
    )
    return list(result.scalars().all())


@router.post("/{product_id}/monitoring-sources", response_model=MonitoringSourceRead, status_code=status.HTTP_201_CREATED)
async def create_monitoring_source(
    product_id: UUID,
    payload: MonitoringSourceCreate,
    session: AsyncSession = Depends(get_db_session),
) -> MonitoringSource:
    product = await session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    source = MonitoringSource(
        product_id=product_id,
        platform=payload.platform,
        source_url=payload.source_url,
        source_type=payload.source_type,
    )
    session.add(source)
    await session.commit()
    await session.refresh(source)
    return source


@router.delete("/{product_id}/monitoring-sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_monitoring_source(
    product_id: UUID,
    source_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> None:
    source = await session.get(MonitoringSource, source_id)
    if not source or source.product_id != product_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitoring source not found.")
    await session.delete(source)
    await session.commit()


# ── Monitoring Run ─────────────────────────────────────────────────────────────

@router.post("/{product_id}/monitoring-sources/{source_id}/run", response_model=list[dict])
async def run_monitoring_for_source(
    product_id: UUID,
    source_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    """Trigger a monitoring run for a specific source (calls Apify scraper)."""
    source = await session.get(MonitoringSource, source_id)
    if not source or source.product_id != product_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitoring source not found.")

    ingested = await run_apify_scraper(session, source)
    return [{"id": str(item.id), "platform": item.platform, "engagement_score": item.engagement_score} for item in ingested]


# ── Ingested Content ───────────────────────────────────────────────────────────

@router.get("/{product_id}/ingested-content", response_model=list[dict])
async def list_ingested_content(
    product_id: UUID,
    unprocessed_only: bool = False,
    session: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    """Get ingested viral content for a product (across all its monitoring sources)."""
    subquery = select(MonitoringSource.id).where(MonitoringSource.product_id == product_id)
    stmt = select(IngestedContent).where(IngestedContent.source_id.in_(subquery))
    if unprocessed_only:
        stmt = stmt.where(IngestedContent.is_processed == False)  # noqa: E712
    stmt = stmt.order_by(IngestedContent.engagement_score.desc())

    result = await session.execute(stmt)
    items = result.scalars().all()
    return [
        {
            "id": str(item.id),
            "platform": item.platform,
            "text_content": item.text_content,
            "engagement_score": item.engagement_score,
            "is_processed": item.is_processed,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in items
    ]
