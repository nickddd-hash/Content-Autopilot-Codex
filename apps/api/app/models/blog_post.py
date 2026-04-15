from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class BlogPost(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "blog_posts"

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text(), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    og_image_url: Mapped[str | None] = mapped_column(String(500))
    hero_image_url: Mapped[str | None] = mapped_column(String(500))
    published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    content_plan_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("content_plan_items.id", ondelete="SET NULL"),
        unique=True,
        index=True,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    product: Mapped["Product"] = relationship(back_populates="blog_posts")
    content_plan_item: Mapped["ContentPlanItem | None"] = relationship(
        foreign_keys=[content_plan_item_id],
    )
