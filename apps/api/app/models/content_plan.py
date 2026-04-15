from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, NamedStatusMixin, TimestampMixin, UUIDPrimaryKeyMixin


class ContentPlan(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "content_plans"

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    month: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    theme: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    product: Mapped["Product"] = relationship(back_populates="content_plans")
    items: Mapped[list["ContentPlanItem"]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="ContentPlanItem.order",
    )


class ContentPlanItem(UUIDPrimaryKeyMixin, TimestampMixin, NamedStatusMixin, Base):
    __tablename__ = "content_plan_items"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("content_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    angle: Mapped[str | None] = mapped_column(Text())
    target_keywords: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    article_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    cta_type: Mapped[str] = mapped_column(String(50), nullable=False, default="soft")
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    telegraph_url: Mapped[str | None] = mapped_column(String(500))
    research_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    article_review: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text())
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    vk_post_id: Mapped[str | None] = mapped_column(String(255))
    vk_posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    vk_adaptation: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    vk_carousel: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    plan: Mapped["ContentPlan"] = relationship(back_populates="items")
    costs: Mapped[list["ContentCost"]] = relationship(back_populates="content_plan_item")
    job_runs: Mapped[list["JobRun"]] = relationship(back_populates="content_plan_item")
