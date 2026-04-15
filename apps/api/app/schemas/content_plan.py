from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class ContentPlanItemRead(ORMModel):
    id: UUID
    plan_id: UUID
    order: int
    title: str
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
    generated_draft_title: str | None
    generated_draft_markdown: str | None
    generated_summary: str | None
    generated_hook: str | None
    generated_cta: str | None
    generation_mode: str | None


class ContentPlanRead(ORMModel):
    id: UUID
    product_id: UUID
    month: str
    theme: str
    status: str
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
    theme: str = Field(min_length=3, max_length=255)
    status: str = Field(default="draft", min_length=2, max_length=50)
    items: list[ContentPlanItemCreate] = Field(default_factory=list)


class ContentPlanUpdate(BaseModel):
    month: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}$")
    theme: str | None = Field(default=None, min_length=3, max_length=255)
    status: str | None = Field(default=None, min_length=2, max_length=50)


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
