from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class BrandProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "brand_profiles"

    brand_name: Mapped[str | None] = mapped_column(Text())
    brand_summary: Mapped[str | None] = mapped_column(Text())
    user_style_description: Mapped[str | None] = mapped_column(Text())
    audience_notes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    core_messages: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    allowed_tone: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    disallowed_tone: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    anti_slop_rules: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    compliance_rules: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    cta_rules: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    vocabulary_preferences: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    formatting_rules: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    channel_strategy: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    image_style_rules: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

