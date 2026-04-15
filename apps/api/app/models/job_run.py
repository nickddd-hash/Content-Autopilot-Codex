from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class JobRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "job_runs"

    job_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    product_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), index=True)
    content_plan_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("content_plan_items.id", ondelete="SET NULL"),
        index=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text())
    meta_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    product: Mapped["Product | None"] = relationship(back_populates="job_runs")
    content_plan_item: Mapped["ContentPlanItem | None"] = relationship(back_populates="job_runs")


class ContentCost(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "content_costs"

    model: Mapped[str] = mapped_column(String(150), nullable=False)
    purpose: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    input_tokens: Mapped[int] = mapped_column(nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(nullable=False, default=0)
    cost_usd: Mapped[float] = mapped_column(nullable=False, default=0.0)
    content_plan_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("content_plan_items.id", ondelete="SET NULL"),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    content_plan_item: Mapped["ContentPlanItem | None"] = relationship(back_populates="costs")
