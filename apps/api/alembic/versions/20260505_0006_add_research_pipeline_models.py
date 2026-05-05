"""Add research-first pipeline models.

Revision ID: 20260505_0006
Revises: 20260422_0005
Create Date: 2026-05-05 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260505_0006"
down_revision = "20260422_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "research_sources",
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("raw_snippet", sa.Text(), nullable=True),
        sa.Column("raw_payload_json", sa.JSON(), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], name=op.f("fk_research_sources_product_id_products"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_research_sources")),
        sa.UniqueConstraint("product_id", "source_type", "url", name="uq_research_sources_product_type_url"),
    )
    op.create_index(op.f("ix_research_sources_domain"), "research_sources", ["domain"], unique=False)
    op.create_index(op.f("ix_research_sources_product_id"), "research_sources", ["product_id"], unique=False)
    op.create_index(op.f("ix_research_sources_source_type"), "research_sources", ["source_type"], unique=False)
    op.create_index(op.f("ix_research_sources_status"), "research_sources", ["status"], unique=False)

    op.create_table(
        "research_candidates",
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("pain_cluster", sa.String(length=100), nullable=False),
        sa.Column("audience_segment", sa.String(length=100), nullable=False),
        sa.Column("business_process", sa.String(length=100), nullable=False),
        sa.Column("solution_type", sa.String(length=100), nullable=False),
        sa.Column("implementation_model", sa.String(length=100), nullable=False),
        sa.Column("angle", sa.String(length=100), nullable=False),
        sa.Column("freshness_reason", sa.Text(), nullable=False),
        sa.Column("signal_type", sa.String(length=50), nullable=False),
        sa.Column("tools_mentioned_json", sa.JSON(), nullable=False),
        sa.Column("keywords_json", sa.JSON(), nullable=False),
        sa.Column("source_urls_json", sa.JSON(), nullable=False),
        sa.Column("strategy_fit_score", sa.Integer(), nullable=False),
        sa.Column("business_relevance_score", sa.Integer(), nullable=False),
        sa.Column("novelty_score", sa.Integer(), nullable=False),
        sa.Column("priority_score", sa.Integer(), nullable=False),
        sa.Column("duplicate_group_key", sa.String(length=500), nullable=False),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], name=op.f("fk_research_candidates_product_id_products"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["research_sources.id"], name=op.f("fk_research_candidates_source_id_research_sources"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_research_candidates")),
    )
    op.create_index(op.f("ix_research_candidates_angle"), "research_candidates", ["angle"], unique=False)
    op.create_index(op.f("ix_research_candidates_audience_segment"), "research_candidates", ["audience_segment"], unique=False)
    op.create_index(op.f("ix_research_candidates_business_process"), "research_candidates", ["business_process"], unique=False)
    op.create_index(op.f("ix_research_candidates_duplicate_group_key"), "research_candidates", ["duplicate_group_key"], unique=False)
    op.create_index(op.f("ix_research_candidates_implementation_model"), "research_candidates", ["implementation_model"], unique=False)
    op.create_index(op.f("ix_research_candidates_pain_cluster"), "research_candidates", ["pain_cluster"], unique=False)
    op.create_index(op.f("ix_research_candidates_priority_score"), "research_candidates", ["priority_score"], unique=False)
    op.create_index(op.f("ix_research_candidates_product_id"), "research_candidates", ["product_id"], unique=False)
    op.create_index(op.f("ix_research_candidates_signal_type"), "research_candidates", ["signal_type"], unique=False)
    op.create_index(op.f("ix_research_candidates_solution_type"), "research_candidates", ["solution_type"], unique=False)
    op.create_index(op.f("ix_research_candidates_source_id"), "research_candidates", ["source_id"], unique=False)
    op.create_index(op.f("ix_research_candidates_status"), "research_candidates", ["status"], unique=False)

    op.create_table(
        "topic_memory",
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("content_plan_id", sa.Uuid(), nullable=True),
        sa.Column("content_plan_item_id", sa.Uuid(), nullable=True),
        sa.Column("research_candidate_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("pain_cluster", sa.String(length=100), nullable=False),
        sa.Column("audience_segment", sa.String(length=100), nullable=False),
        sa.Column("business_process", sa.String(length=100), nullable=False),
        sa.Column("solution_type", sa.String(length=100), nullable=False),
        sa.Column("implementation_model", sa.String(length=100), nullable=False),
        sa.Column("angle", sa.String(length=100), nullable=False),
        sa.Column("trigger_type", sa.String(length=50), nullable=False),
        sa.Column("tools_mentioned_json", sa.JSON(), nullable=False),
        sa.Column("novelty_signature", sa.JSON(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("planned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("performance_score", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["content_plan_id"], ["content_plans.id"], name=op.f("fk_topic_memory_content_plan_id_content_plans"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["content_plan_item_id"], ["content_plan_items.id"], name=op.f("fk_topic_memory_content_plan_item_id_content_plan_items"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], name=op.f("fk_topic_memory_product_id_products"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["research_candidate_id"], ["research_candidates.id"], name=op.f("fk_topic_memory_research_candidate_id_research_candidates"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_topic_memory")),
    )
    op.create_index(op.f("ix_topic_memory_angle"), "topic_memory", ["angle"], unique=False)
    op.create_index(op.f("ix_topic_memory_audience_segment"), "topic_memory", ["audience_segment"], unique=False)
    op.create_index(op.f("ix_topic_memory_business_process"), "topic_memory", ["business_process"], unique=False)
    op.create_index(op.f("ix_topic_memory_content_plan_id"), "topic_memory", ["content_plan_id"], unique=False)
    op.create_index(op.f("ix_topic_memory_content_plan_item_id"), "topic_memory", ["content_plan_item_id"], unique=False)
    op.create_index(op.f("ix_topic_memory_implementation_model"), "topic_memory", ["implementation_model"], unique=False)
    op.create_index(op.f("ix_topic_memory_pain_cluster"), "topic_memory", ["pain_cluster"], unique=False)
    op.create_index(op.f("ix_topic_memory_product_id"), "topic_memory", ["product_id"], unique=False)
    op.create_index(op.f("ix_topic_memory_research_candidate_id"), "topic_memory", ["research_candidate_id"], unique=False)
    op.create_index(op.f("ix_topic_memory_solution_type"), "topic_memory", ["solution_type"], unique=False)
    op.create_index(op.f("ix_topic_memory_status"), "topic_memory", ["status"], unique=False)
    op.create_index(op.f("ix_topic_memory_trigger_type"), "topic_memory", ["trigger_type"], unique=False)

    op.create_table(
        "plan_research_links",
        sa.Column("content_plan_id", sa.Uuid(), nullable=False),
        sa.Column("content_plan_item_id", sa.Uuid(), nullable=True),
        sa.Column("research_candidate_id", sa.Uuid(), nullable=False),
        sa.Column("link_role", sa.String(length=50), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["content_plan_id"], ["content_plans.id"], name=op.f("fk_plan_research_links_content_plan_id_content_plans"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["content_plan_item_id"], ["content_plan_items.id"], name=op.f("fk_plan_research_links_content_plan_item_id_content_plan_items"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["research_candidate_id"], ["research_candidates.id"], name=op.f("fk_plan_research_links_research_candidate_id_research_candidates"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_plan_research_links")),
        sa.UniqueConstraint("content_plan_item_id", "research_candidate_id", "link_role", name="uq_plan_research_links_item_candidate_role"),
    )
    op.create_index(op.f("ix_plan_research_links_content_plan_id"), "plan_research_links", ["content_plan_id"], unique=False)
    op.create_index(op.f("ix_plan_research_links_content_plan_item_id"), "plan_research_links", ["content_plan_item_id"], unique=False)
    op.create_index(op.f("ix_plan_research_links_research_candidate_id"), "plan_research_links", ["research_candidate_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_plan_research_links_research_candidate_id"), table_name="plan_research_links")
    op.drop_index(op.f("ix_plan_research_links_content_plan_item_id"), table_name="plan_research_links")
    op.drop_index(op.f("ix_plan_research_links_content_plan_id"), table_name="plan_research_links")
    op.drop_table("plan_research_links")

    op.drop_index(op.f("ix_topic_memory_trigger_type"), table_name="topic_memory")
    op.drop_index(op.f("ix_topic_memory_status"), table_name="topic_memory")
    op.drop_index(op.f("ix_topic_memory_solution_type"), table_name="topic_memory")
    op.drop_index(op.f("ix_topic_memory_research_candidate_id"), table_name="topic_memory")
    op.drop_index(op.f("ix_topic_memory_product_id"), table_name="topic_memory")
    op.drop_index(op.f("ix_topic_memory_pain_cluster"), table_name="topic_memory")
    op.drop_index(op.f("ix_topic_memory_implementation_model"), table_name="topic_memory")
    op.drop_index(op.f("ix_topic_memory_content_plan_item_id"), table_name="topic_memory")
    op.drop_index(op.f("ix_topic_memory_content_plan_id"), table_name="topic_memory")
    op.drop_index(op.f("ix_topic_memory_business_process"), table_name="topic_memory")
    op.drop_index(op.f("ix_topic_memory_audience_segment"), table_name="topic_memory")
    op.drop_index(op.f("ix_topic_memory_angle"), table_name="topic_memory")
    op.drop_table("topic_memory")

    op.drop_index(op.f("ix_research_candidates_status"), table_name="research_candidates")
    op.drop_index(op.f("ix_research_candidates_source_id"), table_name="research_candidates")
    op.drop_index(op.f("ix_research_candidates_solution_type"), table_name="research_candidates")
    op.drop_index(op.f("ix_research_candidates_signal_type"), table_name="research_candidates")
    op.drop_index(op.f("ix_research_candidates_product_id"), table_name="research_candidates")
    op.drop_index(op.f("ix_research_candidates_priority_score"), table_name="research_candidates")
    op.drop_index(op.f("ix_research_candidates_pain_cluster"), table_name="research_candidates")
    op.drop_index(op.f("ix_research_candidates_implementation_model"), table_name="research_candidates")
    op.drop_index(op.f("ix_research_candidates_duplicate_group_key"), table_name="research_candidates")
    op.drop_index(op.f("ix_research_candidates_business_process"), table_name="research_candidates")
    op.drop_index(op.f("ix_research_candidates_audience_segment"), table_name="research_candidates")
    op.drop_index(op.f("ix_research_candidates_angle"), table_name="research_candidates")
    op.drop_table("research_candidates")

    op.drop_index(op.f("ix_research_sources_status"), table_name="research_sources")
    op.drop_index(op.f("ix_research_sources_source_type"), table_name="research_sources")
    op.drop_index(op.f("ix_research_sources_product_id"), table_name="research_sources")
    op.drop_index(op.f("ix_research_sources_domain"), table_name="research_sources")
    op.drop_table("research_sources")
