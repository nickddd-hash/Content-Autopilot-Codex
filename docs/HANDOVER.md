# Handover

## Where To Continue

- Local workspace: `codex-workspace`
- Main live environment: `https://content.flowsmart.ru`
- Deploy only from repo via `infra/deploy_server.ps1`
- Do not keep server-only UI changes in `/opt/athena-content`
- Server project root: `/opt/athena-content`
- Make point fixes only; do not rewrite whole files for local fixes.
- After edits, compare changed files with the previous version and verify only the intended parts changed.
- Read `docs/MEMORY.md` and `docs/HANDOVER.md` at the start of each session.

## Latest Snapshot

- Content plan page now has:
  - background plan pipeline polling
  - plan calendar by day
  - day drill-down for scheduled posts
- Item page now has:
  - regenerate text from current draft
  - readable publish errors
  - publish now
  - archive / restore
- Telegram publishing constraint:
  - a post with illustration must fit one Telegram caption
  - new plan-generated Telegram posts are created in illustration mode by default
  - backend now enforces a shorter publishable Telegram draft size

## What Is Already Working

- Product dashboard and product page
- Content plans
- Plan mix configuration by directions:
  - practical
  - educational
  - news
  - opinion
  - critical
- Quick custom post modal
- Manual generation for item:
  - text
  - illustration
- Item page with editable post and illustration flow
- Server deployment through Docker Compose

## Important Current UX Logic

- Dashboard shows active products only
- Product page:
  - compact channels
  - plans block
  - collapsible strategy block
- Plan page:
  - `Сгенерировать темы`
  - `Настроить план`
  - `Написать пост`
  - per-item `Генерация`
- Quick post now supports:
  - thematic direction
  - channel checkboxes from current product

## Important Current Backend Logic

- `ContentPlan.settings_json.content_mix` controls plan generation proportions
- Quick post stores:
  - `manual_brief`
  - `content_direction`
  - `channel_targets`
- Generation prompt respects:
  - selected direction
  - selected channels
- `opinion` is explicitly allowed to be reflective and not product-driven
- `pool_pre_ping` is enabled for SQLAlchemy

## Server Security Status

- On `2026-04-22` a suspicious high-CPU process was found inside the `postgres` container
- The stack was recreated and the suspicious process disappeared
- External port exposure was reduced:
  - `postgres` is no longer published outside Docker
  - `redis` is no longer published outside Docker
  - `api` is now bound to `127.0.0.1:8000`
  - `web` is now bound to `127.0.0.1:3000`
- Publicly reachable ports should now effectively be only:
  - `80`
  - `443`
  - `22`
- Server env was hardened:
  - `ENVIRONMENT=production`
  - `AUTO_CREATE_TABLES=false`
- Internal credentials were rotated:
  - `postgres` password
  - `athena_app` password
  - `redis` password

## Important Follow-Up

- External provider keys still need manual rotation outside the server:
  - OpenAI
  - KIE
  - any other third-party keys if present

## Most Likely Next Steps

1. Add a plan-level action that generates materials for the whole plan, not only topics.
2. Add a clearer flow for “material already ready, now add/publish”.
3. Build real autoposting after plan generation.
4. Add reviewer personas that score plans before final approval.

## Latest Automation State

- `content-plans` now exposes:
  - `POST /{plan_id}/build-materials`
  - `POST /{plan_id}/items/{item_id}/generate`
  - `GET /{plan_id}/items/{item_id}/latest-job`
  - `POST /{plan_id}/items/{item_id}/publish`
- Plan page now has `Собрать материалы`.
- Item page now publishes to Telegram via `Запостить`.
- API startup runs a lightweight in-process autopost loop for due `review-ready` items.
- Autoposting only fires when both product switches are on:
  - `autopilot_enabled`
  - `social_posting_enabled`
- Scheduling currently uses product settings:
  - `publish_days`
  - `publish_time_utc`

## Warning

- Do not use repository root side folders like `master-ai` for this project.
- Work only inside `codex-workspace`.
## Session 2026-04-23

- Added `/settings` page in the web app.
- Added `/api/settings/system` for reading and saving system settings.
- Fixed the API startup error introduced by upload support by adding `python-multipart`.
- Fixed Next upload body limit by setting `20mb`.
- Compact settings layout now groups:
  - provider
  - keys
  - text / image / video selectors
- Text provider routing now uses:
  - `LLM_PROVIDER`
  - `TEXT_MODEL`
- Image provider routing now uses:
  - `LLM_PROVIDER`
  - `IMAGE_MODEL`
- OpenRouter text support was added in `apps/api/app/services/llm_client.py`.
- OpenRouter image support was added in `apps/api/app/services/media_generator.py`.
- UI includes OpenRouter image options:
  - `google/gemini-2.5-flash-image`
  - `google/gemini-3.1-flash-image-preview`
- Important stop point:
  - code path is wired
  - still run a real generation test after saving OpenRouter settings in production UI

## Session 2026-04-24

- Settings now autosave without an explicit save button.
- OpenRouter text/image routing is live in code and production has already been tested through image regeneration.
- User-uploaded illustrations are supported from the item page.
- Telegram publishing now:
  - keeps the title bold
  - fails gracefully when caption length is too long for an image post
- One production scheduled Telegram post had to be shortened and then was published successfully.
- Important UI cleanup happened:
  - helper text was reduced across dashboard/product/plan/item/settings
  - several actions were simplified to reduce noise
- Important caution:
  - the plan page and item page are sensitive to encoding regressions
  - do not do broad rewrites there
  - apply only small targeted diffs and verify the rendered route after deploy
- Current stop point:
  - plan page calendar is being reshaped into a compact left-column calendar plus right-column post list
  - date editing belongs inside the item page
  - next session should continue from that layout, not re-open broad UI cleanup across the whole app

## Session 2026-04-30 Stop Point

- Practical generation prompts were tightened:
  - require concrete examples
  - require real scenarios
  - require specific applied detail instead of abstract recommendations
- Plan generation now looks at recent product topics from roughly the last 30 days and skips near-duplicates.
- If duplicate filtering leaves the plan short, fallback topics are appended but still pass the same similarity check.
- Plan page has a display fallback for broken titles:
  - `generated_draft_title` can replace a visibly corrupted `item.title` in the plan list.

## Session 2026-05-03 Stop Point

- Channel strategy discussion saved in `docs/SESSION_2026-05-03_CHANNEL_STRATEGY.md`.
- Marketing recommendation: shift `AI bez slozhnosti` toward business and lead generation.
- Decision: accept business focus, but keep the simple/human brand instead of becoming a dry IT-services channel.
- Product implication: content plans should mix publication roles instead of producing only daily business cases.
- Prompt implication: every business-facing post should reveal a recognizable situation, remove an illusion and lead toward Nikolay's audit/implementation help.
- Future feature idea: add a research layer for automation cases, small-business pains, trends, and rejected-topic memory.
