from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel
from app.schemas.monitoring import ChannelRead, MonitoringSourceRead


class ProductContentSettingsRead(ORMModel):
    id: UUID
    autopilot_enabled: bool
    articles_per_month: int
    publish_days: list[int]
    publish_time_utc: str
    preferred_article_types: list[str]
    forbidden_topics: list[str]
    forbidden_phrases: list[str]
    target_keywords: list[str]
    vk_group_id: str | None
    social_posting_enabled: bool
    carousel_enabled: bool
    default_theme: str | None
    created_at: datetime
    updated_at: datetime


class ProductRead(ORMModel):
    id: UUID
    name: str
    slug: str
    category: str | None
    lifecycle_stage: str | None
    short_description: str | None
    full_description: str | None
    target_audience: str | None
    audience_segments: list[str]
    pain_points: list[str]
    value_proposition: str | None
    key_features: list[str]
    content_pillars: list[str]
    strategic_goals: list[str]
    primary_channels: list[str]
    tone_of_voice: str | None
    cta_strategy: str | None
    website_url: str | None
    blog_base_url: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    content_settings: ProductContentSettingsRead | None
    channels: list[ChannelRead] = Field(default_factory=list)
    monitoring_sources: list[MonitoringSourceRead] = Field(default_factory=list)


class ProductContentSettingsPayload(BaseModel):
    autopilot_enabled: bool = True
    articles_per_month: int = Field(default=8, ge=1, le=60)
    publish_days: list[int] = Field(default_factory=lambda: [1, 4])
    publish_time_utc: str = "07:00"
    preferred_article_types: list[str] = Field(default_factory=list)
    forbidden_topics: list[str] = Field(default_factory=list)
    forbidden_phrases: list[str] = Field(default_factory=list)
    target_keywords: list[str] = Field(default_factory=list)
    vk_group_id: str | None = None
    social_posting_enabled: bool = True
    carousel_enabled: bool = True
    default_theme: str | None = None


class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=2, max_length=255, pattern=r"^[a-z0-9-]+$")
    category: str | None = Field(default=None, max_length=100)
    lifecycle_stage: str | None = Field(default=None, max_length=50)
    short_description: str | None = Field(default=None, max_length=500)
    full_description: str | None = None
    target_audience: str | None = None
    audience_segments: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    value_proposition: str | None = None
    key_features: list[str] = Field(default_factory=list)
    content_pillars: list[str] = Field(default_factory=list)
    strategic_goals: list[str] = Field(default_factory=list)
    primary_channels: list[str] = Field(default_factory=list)
    tone_of_voice: str | None = None
    cta_strategy: str | None = None
    website_url: str | None = None
    blog_base_url: str | None = None
    is_active: bool = True
    content_settings: ProductContentSettingsPayload = Field(default_factory=ProductContentSettingsPayload)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    category: str | None = Field(default=None, max_length=100)
    lifecycle_stage: str | None = Field(default=None, max_length=50)
    short_description: str | None = Field(default=None, max_length=500)
    full_description: str | None = None
    target_audience: str | None = None
    audience_segments: list[str] | None = None
    pain_points: list[str] | None = None
    value_proposition: str | None = None
    key_features: list[str] | None = None
    content_pillars: list[str] | None = None
    strategic_goals: list[str] | None = None
    primary_channels: list[str] | None = None
    tone_of_voice: str | None = None
    cta_strategy: str | None = None
    website_url: str | None = None
    blog_base_url: str | None = None
    is_active: bool | None = None


class ProductContentSettingsUpdate(BaseModel):
    autopilot_enabled: bool | None = None
    articles_per_month: int | None = Field(default=None, ge=1, le=60)
    publish_days: list[int] | None = None
    publish_time_utc: str | None = None
    preferred_article_types: list[str] | None = None
    forbidden_topics: list[str] | None = None
    forbidden_phrases: list[str] | None = None
    target_keywords: list[str] | None = None
    vk_group_id: str | None = None
    social_posting_enabled: bool | None = None
    carousel_enabled: bool | None = None
    default_theme: str | None = None
