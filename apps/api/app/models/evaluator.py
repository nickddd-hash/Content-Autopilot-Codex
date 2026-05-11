from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ContentEvaluator(Base):
    __tablename__ = "content_evaluators"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255))
    role_key: Mapped[str] = mapped_column(String(50), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    system_prompt: Mapped[str] = mapped_column(Text)
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # One evaluator can have many evaluation results
    evaluations: Mapped[list["ContentEvaluationResult"]] = relationship(back_populates="evaluator", cascade="all, delete-orphan")
    plan_audits: Mapped[list["ContentPlanAudit"]] = relationship(back_populates="evaluator", cascade="all, delete-orphan")


class ContentEvaluationResult(Base):
    __tablename__ = "content_evaluation_results"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    content_plan_item_id: Mapped[UUID] = mapped_column(ForeignKey("content_plan_items.id", ondelete="CASCADE"), index=True)
    evaluator_id: Mapped[UUID] = mapped_column(ForeignKey("content_evaluators.id", ondelete="CASCADE"), index=True)
    
    score: Mapped[int] = mapped_column()  # 1-10 or 1-100
    feedback_text: Mapped[str] = mapped_column(Text)
    metrics_json: Mapped[dict | None] = mapped_column(JSON)  # clarity, relevance, interest, etc.
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    item: Mapped["ContentPlanItem"] = relationship(back_populates="evaluation_results")
    evaluator: Mapped["ContentEvaluator"] = relationship(back_populates="evaluations")


class ContentPlanAudit(Base):
    __tablename__ = "content_plan_audits"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    plan_id: Mapped[UUID] = mapped_column(ForeignKey("content_plans.id", ondelete="CASCADE"), index=True)
    evaluator_id: Mapped[UUID] = mapped_column(ForeignKey("content_evaluators.id", ondelete="CASCADE"), index=True)

    score: Mapped[int] = mapped_column()
    feedback_text: Mapped[str] = mapped_column(Text)
    metrics_json: Mapped[dict | None] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    plan: Mapped["ContentPlan"] = relationship(back_populates="plan_audits")
    evaluator: Mapped["ContentEvaluator"] = relationship(back_populates="plan_audits")
