# Data Model Outline

## Product

- `id`
- `name`
- `slug`
- `short_description`
- `full_description`
- `target_audience`
- `pain_points`
- `value_proposition`
- `key_features`
- `tone_of_voice`
- `cta_strategy`
- `website_url`
- `blog_base_url`
- `is_active`
- `created_at`
- `updated_at`

## ProductContentSettings

- `id`
- `product_id`
- `autopilot_enabled`
- `articles_per_month`
- `publish_days`
- `publish_time_utc`
- `preferred_article_types`
- `forbidden_topics`
- `forbidden_phrases`
- `target_keywords`
- `vk_group_id`
- `social_posting_enabled`
- `carousel_enabled`
- `default_theme`
- `created_at`
- `updated_at`

## BrandProfile

- `id`
- `user_style_description`
- `allowed_tone`
- `disallowed_tone`
- `anti_slop_rules`
- `cta_rules`
- `vocabulary_preferences`
- `formatting_rules`
- `image_style_rules`
- `created_at`
- `updated_at`

## ContentPlan

- `id`
- `product_id`
- `month`
- `theme`
- `status`
- `created_at`

## ContentPlanItem

- `id`
- `plan_id`
- `order`
- `title`
- `angle`
- `target_keywords`
- `article_type`
- `cta_type`
- `status`
- `scheduled_at`
- `published_at`
- `blog_post_id`
- `telegraph_url`
- `research_data`
- `article_review`
- `error_message`
- `retry_count`
- `vk_post_id`
- `vk_posted_at`
- `vk_adaptation`
- `vk_carousel`
- `created_at`

## BlogPost

- `id`
- `product_id`
- `slug`
- `title`
- `description`
- `content`
- `category`
- `tags`
- `og_image_url`
- `hero_image_url`
- `published`
- `views`
- `content_plan_item_id`
- `created_at`
- `updated_at`
- `published_at`

## SocialAccount

- `id`
- `platform`
- `access_token`
- `refresh_token`
- `group_id`
- `group_name`
- `group_photo`
- `is_active`

## ContentCost

- `id`
- `model`
- `purpose`
- `input_tokens`
- `output_tokens`
- `cost_usd`
- `content_plan_item_id`
- `created_at`

## JobRun

- `id`
- `job_type`
- `status`
- `product_id`
- `content_plan_item_id`
- `started_at`
- `finished_at`
- `error_message`
- `meta_json`

