"""Add content evaluator models.

Revision ID: 20260512_0007
Revises: 20260505_0006
Create Date: 2026-05-12 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260512_0007"
down_revision = "20260505_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "content_evaluators",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("role_key", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_content_evaluators")),
        sa.UniqueConstraint("role_key", name=op.f("uq_content_evaluators_role_key")),
    )

    op.create_table(
        "content_evaluation_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("content_plan_item_id", sa.Uuid(), nullable=False),
        sa.Column("evaluator_id", sa.Uuid(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("feedback_text", sa.Text(), nullable=False),
        sa.Column("metrics_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.ForeignKeyConstraint(
            ["content_plan_item_id"],
            ["content_plan_items.id"],
            name=op.f("fk_content_evaluation_results_content_plan_item_id_content_plan_items"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["evaluator_id"],
            ["content_evaluators.id"],
            name=op.f("fk_content_evaluation_results_evaluator_id_content_evaluators"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_content_evaluation_results")),
    )
    op.create_index(
        op.f("ix_content_evaluation_results_content_plan_item_id"),
        "content_evaluation_results",
        ["content_plan_item_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_content_evaluation_results_evaluator_id"),
        "content_evaluation_results",
        ["evaluator_id"],
        unique=False,
    )

    op.create_table(
        "content_plan_audits",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("evaluator_id", sa.Uuid(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("feedback_text", sa.Text(), nullable=False),
        sa.Column("metrics_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["content_plans.id"],
            name=op.f("fk_content_plan_audits_plan_id_content_plans"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["evaluator_id"],
            ["content_evaluators.id"],
            name=op.f("fk_content_plan_audits_evaluator_id_content_evaluators"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_content_plan_audits")),
    )
    op.create_index(
        op.f("ix_content_plan_audits_plan_id"),
        "content_plan_audits",
        ["plan_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_content_plan_audits_evaluator_id"),
        "content_plan_audits",
        ["evaluator_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("content_plan_audits")
    op.drop_table("content_evaluation_results")
    op.drop_table("content_evaluators")
