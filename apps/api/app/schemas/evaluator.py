from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import ORMModel


class ContentEvaluatorRead(ORMModel):
    id: UUID
    name: str
    role_key: str
    description: str | None = None
    avatar_url: str | None = None


class ContentEvaluationResultRead(ORMModel):
    id: UUID
    evaluator_id: UUID
    score: int
    feedback_text: str
    metrics_json: dict | None = None
    created_at: datetime
    evaluator: ContentEvaluatorRead


class ContentPlanAuditRead(ORMModel):
    id: UUID
    evaluator_id: UUID
    score: int
    feedback_text: str
    metrics_json: dict | None = None
    created_at: datetime
    evaluator: ContentEvaluatorRead
