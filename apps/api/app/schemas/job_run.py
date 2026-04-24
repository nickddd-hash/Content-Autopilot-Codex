from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.schemas.common import ORMModel


class JobRunRead(ORMModel):
    id: UUID
    job_type: str
    status: str
    product_id: UUID | None
    content_plan_id: UUID | None
    content_plan_item_id: UUID | None
    started_at: datetime | None
    finished_at: datetime | None
    error_message: str | None
    meta_json: dict
    created_at: datetime
    updated_at: datetime


class StartGenerationResponse(ORMModel):
    job_run: JobRunRead
    item_status: str
