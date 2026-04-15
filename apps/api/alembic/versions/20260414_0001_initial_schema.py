"""Initial schema for athena content autopilot."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260414_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "brand_profiles",
        sa.Column("user_style_description", sa.Text(), nullable=True),
        sa.Column("allowed_tone", sa.JSON(), nullable=False),
        sa.Column("disallowed_tone", sa.JSON(), nullable=False),
        sa.Column("anti_slop_rules", sa.JSON(), nullable=False),
        sa.Column("cta_rules", sa.JSON(), nullable=False),
        sa.Column("vocabulary_preferences", sa.JSON(), nullable=False),
        sa.Column("formatting_rules", sa.JSON(), nullable=False),
        sa.Column("image_style_rules", sa.JSON(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_brand_profiles")),
    )
    op.create_table(
        "social_accounts",
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("access_token", sa.String(length=500), nullable=False),
        sa.Column("refresh_token", sa.String(length=500), nullable=True),
        sa.Column("group_id", sa.String(length=255), nullable=True),
        sa.Column("group_name", sa.String(length=255), nullable=True),
        sa.Column("group_photo", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_social_accounts")),
    )
    op.create_index(op.f("ix_social_accounts_group_id"), "social_accounts", ["group_id"], unique=False)
    op.create_index(op.f("ix_social_accounts_is_active"), "social_accounts", ["is_active"], unique=False)
    op.create_index(op.f("ix_social_accounts_platform"), "social_accounts", ["platform"], unique=False)
    op.create_table(
        "products",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("short_description", sa.String(length=500), nullable=True),
        sa.Column("full_description", sa.Text(), nullable=True),
        sa.Column("target_audience", sa.Text(), nullable=True),
        sa.Column("pain_points", sa.JSON(), nullable=False),
        sa.Column("value_proposition", sa.Text(), nullable=True),
        sa.Column("key_features", sa.JSON(), nullable=False),
        sa.Column("tone_of_voice", sa.Text(), nullable=True),
        sa.Column("cta_strategy", sa.Text(), nullable=True),
        sa.Column("website_url", sa.String(length=500), nullable=True),
        sa.Column("blog_base_url", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_products")),
    )
    op.create_index(op.f("ix_products_is_active"), "products", ["is_active"], unique=False)
    op.create_index(op.f("ix_products_slug"), "products", ["slug"], unique=True)
    op.create_table(
        "content_plans",
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("month", sa.String(length=7), nullable=False),
        sa.Column("theme", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], name=op.f("fk_content_plans_product_id_products"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_content_plans")),
    )
    op.create_index(op.f("ix_content_plans_month"), "content_plans", ["month"], unique=False)
    op.create_index(op.f("ix_content_plans_product_id"), "content_plans", ["product_id"], unique=False)
    op.create_index(op.f("ix_content_plans_status"), "content_plans", ["status"], unique=False)
    op.create_table(
        "product_content_settings",
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("autopilot_enabled", sa.Boolean(), nullable=False),
        sa.Column("articles_per_month", sa.Integer(), nullable=False),
        sa.Column("publish_days", sa.JSON(), nullable=False),
        sa.Column("publish_time_utc", sa.String(length=5), nullable=False),
        sa.Column("preferred_article_types", sa.JSON(), nullable=False),
        sa.Column("forbidden_topics", sa.JSON(), nullable=False),
        sa.Column("forbidden_phrases", sa.JSON(), nullable=False),
        sa.Column("target_keywords", sa.JSON(), nullable=False),
        sa.Column("vk_group_id", sa.String(length=255), nullable=True),
        sa.Column("social_posting_enabled", sa.Boolean(), nullable=False),
        sa.Column("carousel_enabled", sa.Boolean(), nullable=False),
        sa.Column("default_theme", sa.String(length=255), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], name=op.f("fk_product_content_settings_product_id_products"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_product_content_settings")),
    )
    op.create_index(op.f("ix_product_content_settings_autopilot_enabled"), "product_content_settings", ["autopilot_enabled"], unique=False)
    op.create_index(op.f("ix_product_content_settings_product_id"), "product_content_settings", ["product_id"], unique=True)
    op.create_table(
        "blog_posts",
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("og_image_url", sa.String(length=500), nullable=True),
        sa.Column("hero_image_url", sa.String(length=500), nullable=True),
        sa.Column("published", sa.Boolean(), nullable=False),
        sa.Column("views", sa.Integer(), nullable=False),
        sa.Column("content_plan_item_id", sa.Uuid(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], name=op.f("fk_blog_posts_product_id_products"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_blog_posts")),
    )
    op.create_index(op.f("ix_blog_posts_content_plan_item_id"), "blog_posts", ["content_plan_item_id"], unique=True)
    op.create_index(op.f("ix_blog_posts_product_id"), "blog_posts", ["product_id"], unique=False)
    op.create_index(op.f("ix_blog_posts_published"), "blog_posts", ["published"], unique=False)
    op.create_index(op.f("ix_blog_posts_slug"), "blog_posts", ["slug"], unique=True)
    op.create_table(
        "content_plan_items",
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("angle", sa.Text(), nullable=True),
        sa.Column("target_keywords", sa.JSON(), nullable=False),
        sa.Column("article_type", sa.String(length=50), nullable=False),
        sa.Column("cta_type", sa.String(length=50), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("telegraph_url", sa.String(length=500), nullable=True),
        sa.Column("research_data", sa.JSON(), nullable=False),
        sa.Column("article_review", sa.JSON(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("vk_post_id", sa.String(length=255), nullable=True),
        sa.Column("vk_posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("vk_adaptation", sa.JSON(), nullable=False),
        sa.Column("vk_carousel", sa.JSON(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["content_plans.id"], name=op.f("fk_content_plan_items_plan_id_content_plans"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_content_plan_items")),
    )
    op.create_index(op.f("ix_content_plan_items_article_type"), "content_plan_items", ["article_type"], unique=False)
    op.create_index(op.f("ix_content_plan_items_plan_id"), "content_plan_items", ["plan_id"], unique=False)
    op.create_index(op.f("ix_content_plan_items_status"), "content_plan_items", ["status"], unique=False)
    op.create_foreign_key(
        op.f("fk_blog_posts_content_plan_item_id_content_plan_items"),
        "blog_posts",
        "content_plan_items",
        ["content_plan_item_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_table(
        "content_costs",
        sa.Column("model", sa.String(length=150), nullable=False),
        sa.Column("purpose", sa.String(length=100), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("cost_usd", sa.Float(), nullable=False),
        sa.Column("content_plan_item_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["content_plan_item_id"], ["content_plan_items.id"], name=op.f("fk_content_costs_content_plan_item_id_content_plan_items"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_content_costs")),
    )
    op.create_index(op.f("ix_content_costs_content_plan_item_id"), "content_costs", ["content_plan_item_id"], unique=False)
    op.create_index(op.f("ix_content_costs_purpose"), "content_costs", ["purpose"], unique=False)
    op.create_table(
        "job_runs",
        sa.Column("job_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=True),
        sa.Column("content_plan_item_id", sa.Uuid(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("meta_json", sa.JSON(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["content_plan_item_id"], ["content_plan_items.id"], name=op.f("fk_job_runs_content_plan_item_id_content_plan_items"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], name=op.f("fk_job_runs_product_id_products"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_job_runs")),
    )
    op.create_index(op.f("ix_job_runs_content_plan_item_id"), "job_runs", ["content_plan_item_id"], unique=False)
    op.create_index(op.f("ix_job_runs_job_type"), "job_runs", ["job_type"], unique=False)
    op.create_index(op.f("ix_job_runs_product_id"), "job_runs", ["product_id"], unique=False)
    op.create_index(op.f("ix_job_runs_status"), "job_runs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_job_runs_status"), table_name="job_runs")
    op.drop_index(op.f("ix_job_runs_product_id"), table_name="job_runs")
    op.drop_index(op.f("ix_job_runs_job_type"), table_name="job_runs")
    op.drop_index(op.f("ix_job_runs_content_plan_item_id"), table_name="job_runs")
    op.drop_table("job_runs")
    op.drop_index(op.f("ix_content_costs_purpose"), table_name="content_costs")
    op.drop_index(op.f("ix_content_costs_content_plan_item_id"), table_name="content_costs")
    op.drop_table("content_costs")
    op.drop_constraint(op.f("fk_blog_posts_content_plan_item_id_content_plan_items"), "blog_posts", type_="foreignkey")
    op.drop_index(op.f("ix_content_plan_items_status"), table_name="content_plan_items")
    op.drop_index(op.f("ix_content_plan_items_plan_id"), table_name="content_plan_items")
    op.drop_index(op.f("ix_content_plan_items_article_type"), table_name="content_plan_items")
    op.drop_table("content_plan_items")
    op.drop_index(op.f("ix_blog_posts_slug"), table_name="blog_posts")
    op.drop_index(op.f("ix_blog_posts_published"), table_name="blog_posts")
    op.drop_index(op.f("ix_blog_posts_product_id"), table_name="blog_posts")
    op.drop_index(op.f("ix_blog_posts_content_plan_item_id"), table_name="blog_posts")
    op.drop_table("blog_posts")
    op.drop_index(op.f("ix_product_content_settings_product_id"), table_name="product_content_settings")
    op.drop_index(op.f("ix_product_content_settings_autopilot_enabled"), table_name="product_content_settings")
    op.drop_table("product_content_settings")
    op.drop_index(op.f("ix_content_plans_status"), table_name="content_plans")
    op.drop_index(op.f("ix_content_plans_product_id"), table_name="content_plans")
    op.drop_index(op.f("ix_content_plans_month"), table_name="content_plans")
    op.drop_table("content_plans")
    op.drop_index(op.f("ix_products_slug"), table_name="products")
    op.drop_index(op.f("ix_products_is_active"), table_name="products")
    op.drop_table("products")
    op.drop_index(op.f("ix_social_accounts_platform"), table_name="social_accounts")
    op.drop_index(op.f("ix_social_accounts_is_active"), table_name="social_accounts")
    op.drop_index(op.f("ix_social_accounts_group_id"), table_name="social_accounts")
    op.drop_table("social_accounts")
    op.drop_table("brand_profiles")
