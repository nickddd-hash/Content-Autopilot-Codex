from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class BrandProfileRead(ORMModel):
    id: UUID
    brand_name: str | None
    brand_summary: str | None
    user_style_description: str | None
    audience_notes: list[str]
    core_messages: list[str]
    allowed_tone: list[str]
    disallowed_tone: list[str]
    anti_slop_rules: list[str]
    compliance_rules: list[str]
    cta_rules: list[str]
    vocabulary_preferences: list[str]
    formatting_rules: list[str]
    channel_strategy: dict
    image_style_rules: list[str]
    created_at: datetime
    updated_at: datetime


class BrandProfileUpsert(BaseModel):
    brand_name: str | None = None
    brand_summary: str | None = None
    user_style_description: str | None = None
    audience_notes: list[str] = Field(default_factory=list)
    core_messages: list[str] = Field(default_factory=list)
    allowed_tone: list[str] = Field(default_factory=list)
    disallowed_tone: list[str] = Field(default_factory=list)
    anti_slop_rules: list[str] = Field(default_factory=list)
    compliance_rules: list[str] = Field(default_factory=list)
    cta_rules: list[str] = Field(default_factory=list)
    vocabulary_preferences: list[str] = Field(default_factory=list)
    formatting_rules: list[str] = Field(default_factory=list)
    channel_strategy: dict = Field(default_factory=dict)
    image_style_rules: list[str] = Field(default_factory=list)

