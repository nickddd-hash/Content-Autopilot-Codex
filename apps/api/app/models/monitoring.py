import uuid

from sqlalchemy import Boolean, ForeignKey, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Channel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "channels"

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., 'instagram', 'youtube', 'tiktok'
    name: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g., '@health_concilium'
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    credentials: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # Stores per-project tokens if any
    
    product: Mapped["Product"] = relationship(back_populates="channels")


class MonitoringSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "monitoring_sources"

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False) # e.g. https://instagram.com/hubermanlab
    source_type: Mapped[str] = mapped_column(String(50), nullable=False) # e.g., 'profile', 'hashtag', 'search'
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    product: Mapped["Product"] = relationship(back_populates="monitoring_sources")
    ingested_contents: Mapped[list["IngestedContent"]] = relationship(back_populates="source")


class IngestedContent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ingested_content"

    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("monitoring_sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True) # ID from the platform
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False) # video, image, text
    text_content: Mapped[str | None] = mapped_column(Text())
    media_urls: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    engagement_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    raw_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict) # full raw JSON
    is_processed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    source: Mapped[MonitoringSource] = relationship(back_populates="ingested_contents")
