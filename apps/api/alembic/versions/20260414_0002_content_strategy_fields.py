"""Add configurable product and brand strategy fields.

Revision ID: 20260414_0002
Revises: 20260414_0001
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260414_0002"
down_revision = "20260414_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("category", sa.String(length=100), nullable=True))
    op.add_column("products", sa.Column("lifecycle_stage", sa.String(length=50), nullable=True))
    op.add_column("products", sa.Column("audience_segments", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("products", sa.Column("content_pillars", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("products", sa.Column("strategic_goals", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("products", sa.Column("primary_channels", sa.JSON(), nullable=False, server_default="[]"))
    op.create_index(op.f("ix_products_category"), "products", ["category"], unique=False)
    op.create_index(op.f("ix_products_lifecycle_stage"), "products", ["lifecycle_stage"], unique=False)

    op.add_column("brand_profiles", sa.Column("brand_name", sa.Text(), nullable=True))
    op.add_column("brand_profiles", sa.Column("brand_summary", sa.Text(), nullable=True))
    op.add_column("brand_profiles", sa.Column("audience_notes", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("brand_profiles", sa.Column("core_messages", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("brand_profiles", sa.Column("compliance_rules", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("brand_profiles", sa.Column("channel_strategy", sa.JSON(), nullable=False, server_default="{}"))


def downgrade() -> None:
    op.drop_column("brand_profiles", "channel_strategy")
    op.drop_column("brand_profiles", "compliance_rules")
    op.drop_column("brand_profiles", "core_messages")
    op.drop_column("brand_profiles", "audience_notes")
    op.drop_column("brand_profiles", "brand_summary")
    op.drop_column("brand_profiles", "brand_name")

    op.drop_index(op.f("ix_products_lifecycle_stage"), table_name="products")
    op.drop_index(op.f("ix_products_category"), table_name="products")
    op.drop_column("products", "primary_channels")
    op.drop_column("products", "strategic_goals")
    op.drop_column("products", "content_pillars")
    op.drop_column("products", "audience_segments")
    op.drop_column("products", "lifecycle_stage")
    op.drop_column("products", "category")
