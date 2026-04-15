from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SocialAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "social_accounts"

    platform: Mapped[str] = mapped_column(String(50), nullable=False, default="vk", index=True)
    access_token: Mapped[str] = mapped_column(String(500), nullable=False)
    refresh_token: Mapped[str | None] = mapped_column(String(500))
    group_id: Mapped[str | None] = mapped_column(String(255), index=True)
    group_name: Mapped[str | None] = mapped_column(String(255))
    group_photo: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

