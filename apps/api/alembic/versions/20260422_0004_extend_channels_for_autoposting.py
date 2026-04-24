"""Extend channels for autoposting validation."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260422_0004"
down_revision = "d3c297b7f0dd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("channels", sa.Column("settings_json", sa.JSON(), nullable=False, server_default="{}"))
    op.add_column("channels", sa.Column("external_id", sa.String(length=255), nullable=True))
    op.add_column("channels", sa.Column("external_name", sa.String(length=255), nullable=True))
    op.add_column("channels", sa.Column("validation_status", sa.String(length=50), nullable=False, server_default="pending"))
    op.add_column("channels", sa.Column("validation_message", sa.Text(), nullable=True))
    op.add_column("channels", sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_channels_external_id"), "channels", ["external_id"], unique=False)
    op.create_index(op.f("ix_channels_validation_status"), "channels", ["validation_status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_channels_validation_status"), table_name="channels")
    op.drop_index(op.f("ix_channels_external_id"), table_name="channels")
    op.drop_column("channels", "validated_at")
    op.drop_column("channels", "validation_message")
    op.drop_column("channels", "validation_status")
    op.drop_column("channels", "external_name")
    op.drop_column("channels", "external_id")
    op.drop_column("channels", "settings_json")
