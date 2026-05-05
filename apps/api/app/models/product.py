from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Product(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "products"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    category: Mapped[str | None] = mapped_column(String(100), index=True)
    lifecycle_stage: Mapped[str | None] = mapped_column(String(50), index=True)
    short_description: Mapped[str | None] = mapped_column(String(500))
    full_description: Mapped[str | None] = mapped_column(Text())
    target_audience: Mapped[str | None] = mapped_column(Text())
    audience_segments: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    pain_points: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    value_proposition: Mapped[str | None] = mapped_column(Text())
    key_features: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    content_pillars: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    strategic_goals: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    primary_channels: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    tone_of_voice: Mapped[str | None] = mapped_column(Text())
    cta_strategy: Mapped[str | None] = mapped_column(Text())
    website_url: Mapped[str | None] = mapped_column(String(500))
    blog_base_url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    content_settings: Mapped["ProductContentSettings | None"] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        uselist=False,
    )
    channels: Mapped[list["ProductChannel"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
    content_plans: Mapped[list["ContentPlan"]] = relationship(back_populates="product")
    blog_posts: Mapped[list["BlogPost"]] = relationship(back_populates="product")
    job_runs: Mapped[list["JobRun"]] = relationship(back_populates="product")
    research_sources: Mapped[list["ResearchSource"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
    research_candidates: Mapped[list["ResearchCandidate"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
    topic_memory_entries: Mapped[list["TopicMemory"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )


class ProductContentSettings(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "product_content_settings"

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    autopilot_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    articles_per_month: Mapped[int] = mapped_column(Integer, nullable=False, default=8)
    publish_days: Mapped[list[int]] = mapped_column(JSON, nullable=False, default=lambda: [1, 4])
    publish_time_utc: Mapped[str] = mapped_column(String(5), nullable=False, default="07:00")
    preferred_article_types: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    forbidden_topics: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    forbidden_phrases: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    target_keywords: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    vk_group_id: Mapped[str | None] = mapped_column(String(255))
    social_posting_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    carousel_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    default_theme: Mapped[str | None] = mapped_column(String(255))

    product: Mapped[Product] = relationship(back_populates="content_settings")

