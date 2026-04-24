from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ProductChannel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "channels"

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    secrets_json: Mapped[dict] = mapped_column("credentials", JSON, nullable=False, default=dict)
    settings_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    external_id: Mapped[str | None] = mapped_column(String(255), index=True)
    external_name: Mapped[str | None] = mapped_column(String(255))
    validation_status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    validation_message: Mapped[str | None] = mapped_column(Text())
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    product: Mapped["Product"] = relationship(back_populates="channels")

    @property
    def configured_secret_keys(self) -> list[str]:
        if not isinstance(self.secrets_json, dict):
            return []
        return [str(key) for key, value in self.secrets_json.items() if str(value).strip()]
