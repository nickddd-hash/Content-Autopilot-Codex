from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import ORMModel

PLAN_DIRECTION_KEYS = ("practical", "educational", "news", "opinion", "critical")


class ContentMixSettings(BaseModel):
    practical: int = Field(default=60, ge=0, le=100)
    educational: int = Field(default=20, ge=0, le=100)
    news: int = Field(default=10, ge=0, le=100)
    opinion: int = Field(default=5, ge=0, le=100)
    critical: int = Field(default=5, ge=0, le=100)

    @model_validator(mode="after")
    def validate_sum(self) -> "ContentMixSettings":
        total = self.practical + self.educational + self.news + self.opinion + self.critical
        if total > 100:
            raise ValueError("content_mix total must not exceed 100")
        return self


class ContentPlanSettings(BaseModel):
    content_mix: ContentMixSettings = Field(default_factory=ContentMixSettings)
    auto_generate_illustrations: bool = True
    needs_reschedule: bool = False
    reschedule_reason: str | None = None
    reschedule_source_item_id: UUID | None = None


class ContentPlanItemRead(ORMModel):
    id: UUID
    plan_id: UUID
    order: int
    title: str
    generated_draft_title: str | None = None
    angle: str | None
    target_keywords: list[str]
    article_type: str
    cta_type: str
    status: str
    scheduled_at: datetime | None
    published_at: datetime | None
    telegraph_url: str | None
    research_data: dict
    article_review: dict
    error_message: str | None
    retry_count: int
    vk_post_id: str | None
    vk_posted_at: datetime | None
    vk_adaptation: dict
    vk_carousel: dict
    created_at: datetime
    updated_at: datetime


class ContentPlanItemDetailRead(ContentPlanItemRead):
    generated_draft_title: str | None = None
    generated_draft_markdown: str | None = None
    generated_summary: str | None = None
    generated_hook: str | None = None
    generated_cta: str | None = None
    channel_adaptations: dict = Field(default_factory=dict)
    generation_mode: str | None = None


class ArchivedContentItemRead(ORMModel):
    id: UUID
    plan_id: UUID
    product_id: UUID
    product_name: str
    plan_month: str
    plan_theme: str
    title: str
    angle: str | None
    article_type: str
    status: str
    target_keywords: list[str]
    scheduled_at: datetime | None
    published_at: datetime | None
    updated_at: datetime
    generated_draft_title: str | None = None
    generated_draft_markdown: str | None = None


class ContentPlanRead(ORMModel):
    id: UUID
    product_id: UUID
    month: str
    theme: str
    status: str
    settings_json: ContentPlanSettings = Field(default_factory=ContentPlanSettings)
    created_at: datetime
    items: list[ContentPlanItemRead]


class ContentPlanItemCreate(BaseModel):
    order: int = Field(default=0, ge=0)
    title: str = Field(min_length=3, max_length=255)
    angle: str | None = None
    target_keywords: list[str] = Field(default_factory=list)
    article_type: str = Field(default="educational", min_length=2, max_length=50)
    cta_type: str = Field(default="soft", min_length=2, max_length=50)
    status: str = Field(default="draft", min_length=2, max_length=50)
    scheduled_at: datetime | None = None
    published_at: datetime | None = None
    telegraph_url: str | None = None
    research_data: dict = Field(default_factory=dict)
    article_review: dict = Field(default_factory=dict)
    error_message: str | None = None
    retry_count: int = Field(default=0, ge=0)
    vk_post_id: str | None = None
    vk_posted_at: datetime | None = None
    vk_adaptation: dict = Field(default_factory=dict)
    vk_carousel: dict = Field(default_factory=dict)


class ContentPlanCreate(BaseModel):
    product_id: UUID
    month: str = Field(pattern=r"^\d{4}-\d{2}$")
    theme: str | None = Field(default=None, max_length=255)
    status: str = Field(default="draft", min_length=2, max_length=50)
    settings_json: ContentPlanSettings = Field(default_factory=ContentPlanSettings)
    items: list[ContentPlanItemCreate] = Field(default_factory=list)


class ContentPlanUpdate(BaseModel):
    month: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}$")
    theme: str | None = Field(default=None, max_length=255)
    status: str | None = Field(default=None, min_length=2, max_length=50)
    settings_json: ContentPlanSettings | None = None


class ContentPlanItemUpdate(BaseModel):
    order: int | None = Field(default=None, ge=0)
    title: str | None = Field(default=None, min_length=3, max_length=255)
    angle: str | None = None
    target_keywords: list[str] | None = None
    article_type: str | None = Field(default=None, min_length=2, max_length=50)
    cta_type: str | None = Field(default=None, min_length=2, max_length=50)
    status: str | None = Field(default=None, min_length=2, max_length=50)
    scheduled_at: datetime | None = None
    published_at: datetime | None = None
    telegraph_url: str | None = None
    research_data: dict | None = None
    article_review: dict | None = None
    error_message: str | None = None
    retry_count: int | None = Field(default=None, ge=0)
    vk_post_id: str | None = None
    vk_posted_at: datetime | None = None
    vk_adaptation: dict | None = None
    vk_carousel: dict | None = None


class ContentPlanItemStatusUpdate(BaseModel):
    status: str = Field(min_length=2, max_length=50)


class GeneratePlanItemsPayload(BaseModel):
    theme: str | None = Field(default=None, max_length=255)
    num_items: int | None = Field(default=None, ge=1, le=30)


class RunPlanPipelinePayload(BaseModel):
    generate_items: bool = False
    theme: str | None = Field(default=None, max_length=255)
    num_items: int | None = Field(default=None, ge=1, le=30)


class QuickPostPayload(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    text: str = Field(min_length=3)
    content_direction: str | None = Field(default=None, max_length=50)
    channel_targets: list[str] = Field(default_factory=list)
    include_illustration: bool = False
    generate_now: bool = False
