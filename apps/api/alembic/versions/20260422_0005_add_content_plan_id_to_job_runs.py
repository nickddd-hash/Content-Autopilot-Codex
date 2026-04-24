"""Add content_plan_id to job runs."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260422_0005"
down_revision = "20260422_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("job_runs", sa.Column("content_plan_id", sa.UUID(), nullable=True))
    op.create_index(op.f("ix_job_runs_content_plan_id"), "job_runs", ["content_plan_id"], unique=False)
    op.create_foreign_key(
        "fk_job_runs_content_plan_id_content_plans",
        "job_runs",
        "content_plans",
        ["content_plan_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_job_runs_content_plan_id_content_plans", "job_runs", type_="foreignkey")
    op.drop_index(op.f("ix_job_runs_content_plan_id"), table_name="job_runs")
    op.drop_column("job_runs", "content_plan_id")
