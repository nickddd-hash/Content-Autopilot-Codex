from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, NamedStatusMixin, TimestampMixin, UUIDPrimaryKeyMixin


class ResearchSource(UUIDPrimaryKeyMixin, TimestampMixin, NamedStatusMixin, Base):
    __tablename__ = "research_sources"
    __table_args__ = (
        UniqueConstraint("product_id", "source_type", "url", name="uq_research_sources_product_type_url"),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255), index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    raw_snippet: Mapped[str | None] = mapped_column(Text())
    raw_payload_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    language: Mapped[str | None] = mapped_column(String(16))

    product: Mapped["Product"] = relationship(back_populates="research_sources")
    candidates: Mapped[list["ResearchCandidate"]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
    )


class ResearchCandidate(UUIDPrimaryKeyMixin, TimestampMixin, NamedStatusMixin, Base):
    __tablename__ = "research_candidates"

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("research_sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text(), nullable=False)
    pain_cluster: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    audience_segment: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    business_process: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    solution_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    implementation_model: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    angle: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    freshness_reason: Mapped[str] = mapped_column(Text(), nullable=False)
    signal_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    tools_mentioned_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    keywords_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    source_urls_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    strategy_fit_score: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    business_relevance_score: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    novelty_score: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    priority_score: Mapped[int] = mapped_column(Integer, nullable=False, default=50, index=True)
    duplicate_group_key: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text())

    product: Mapped["Product"] = relationship(back_populates="research_candidates")
    source: Mapped[ResearchSource | None] = relationship(back_populates="candidates")
    plan_links: Mapped[list["PlanResearchLink"]] = relationship(
        back_populates="research_candidate",
        cascade="all, delete-orphan",
    )
    topic_memories: Mapped[list["TopicMemory"]] = relationship(back_populates="research_candidate")


class TopicMemory(UUIDPrimaryKeyMixin, TimestampMixin, NamedStatusMixin, Base):
    __tablename__ = "topic_memory"

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content_plan_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("content_plans.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    content_plan_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("content_plan_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    research_candidate_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("research_candidates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    pain_cluster: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    audience_segment: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    business_process: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    solution_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    implementation_model: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    angle: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False, default="evergreen", index=True)
    tools_mentioned_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    novelty_signature: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    planned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(Text())
    performance_score: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text())

    product: Mapped["Product"] = relationship(back_populates="topic_memory_entries")
    content_plan: Mapped["ContentPlan | None"] = relationship(back_populates="topic_memory_entries")
    content_plan_item: Mapped["ContentPlanItem | None"] = relationship()
    research_candidate: Mapped[ResearchCandidate | None] = relationship(back_populates="topic_memories")


class PlanResearchLink(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "plan_research_links"
    __table_args__ = (
        UniqueConstraint(
            "content_plan_item_id",
            "research_candidate_id",
            "link_role",
            name="uq_plan_research_links_item_candidate_role",
        ),
    )

    content_plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("content_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content_plan_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("content_plan_items.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    research_candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("research_candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    link_role: Mapped[str] = mapped_column(String(50), nullable=False, default="primary_basis")

    content_plan: Mapped["ContentPlan"] = relationship(back_populates="research_links")
    content_plan_item: Mapped["ContentPlanItem | None"] = relationship()
    research_candidate: Mapped[ResearchCandidate] = relationship(back_populates="plan_links")
