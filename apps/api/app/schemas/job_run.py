from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class JobRunRead(ORMModel):
    id: UUID
    job_type: str
    status: str
    product_id: UUID | None
    content_plan_item_id: UUID | None
    started_at: datetime | None
    finished_at: datetime | None
    error_message: str | None
    meta_json: dict
    created_at: datetime
    updated_at: datetime


class StartGenerationPayload(BaseModel):
    notes: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional operator notes for the manual generation run.",
    )


class StartGenerationResponse(BaseModel):
    job_run: JobRunRead
    item_status: str
