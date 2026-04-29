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

## Session 2026-04-26 Stop Point

Repository:

- Local workspace: `C:\Users\nickd\.gemini\antigravity\scratch\Content-Autopilot-Codex`
- GitHub: `https://github.com/nickddd-hash/Content-Autopilot-Codex`
- Branch: `main`
- Production: `https://content.flowsmart.ru`
- Server: `82.21.72.233`, remote path `/opt/athena-content`
- Deploy command:
  `powershell -ExecutionPolicy Bypass -File infra\deploy_server.ps1 -HostName root@82.21.72.233 -KeyPath $HOME\.ssh\master_deploy -RemotePath /opt/athena-content`

Latest deployed code commit before this handover update:

- `2dd301e fix: compact schedule after manual publish`
- Production health after deploy:
  - `/` returned `200`
  - `/api/health` returned `{"status":"ok"}`

What changed in this work block:

- Product page no longer generates a content plan immediately. The create button opens/creates the plan settings flow first.
- Actual plan generation now requires double confirmation and has a stop/cancel action.
- Each product now has one main content plan. New generations add posts into that main plan instead of creating many competing monthly plans.
- Plan title is editable.
- Plan generation can skip illustrations. Default is no immediate illustration generation, but posts still reserve space/format for an illustration.
- Active counters now exclude archived items, so archived posts do not make the plan look inconsistent.
- The post page has a regeneration comment field. User can explain how to improve the draft before regenerating text.
- The old top `Regenerate post` draft button was removed; regeneration lives in the text editing/regeneration block.
- Global prompts now assume the blog is for Russia/CIS. Western services can be mentioned as global trend examples, but not as default everyday-use recommendations.
- `Publish now` now publishes the selected future item immediately and compacts the future schedule: later unpublished posts shift up into the freed slot so regularity is preserved.

Current product decisions to preserve:

- All channels in a product are important. Do not choose one "main" channel. Generate/adapt content according to the full channel set.
- For "AI bez slozhnosti", the audience is broad and non-technical: people who heard about AI/automation, are curious, but do not actively search for solutions yet.
- Content should stay practical, light, and useful: small everyday AI tricks, simple explanations, AI news, and occasional stronger SaaS/automation examples.
- The system should support maximum automation, while preserving manual editing and override paths.

Known cautions:

- Some older memory/docs and terminal output show mojibake. Avoid broad rewrites of UTF-8-heavy frontend files.
- Plan and item pages are sensitive to encoding regressions. Make small targeted patches and verify rendered pages after deploy.
- The latest publish-now compaction compiled and deployed, but it still deserves one real manual publish test when the user is ready.

Likely next tasks:

- Test publish-now compaction with a real scheduled post.
- Improve prompt quality for detailed practical posts, e.g. AI model comparisons: Gemini, Claude, DeepSeek, ChatGPT, etc.
- Consider moving generation/publishing jobs to a more durable background worker instead of lightweight in-process tasks.
- Later, carefully clean corrupted docs/strings if needed, but only with encoding-safe tooling.

## Session 2026-04-27 Stop Point

- Dzen is now implemented as a second real project channel.
- Dzen channel supports mode:
  - `auto`
  - `post`
  - `article`
- Existing plans can now be extended by selected channels only, instead of acting like a brand new plan every time.
- Scheduling is now parallel by channel signature:
  - Telegram-only and Dzen-only materials can share the same dates.
- The right-side `Адаптации по каналам` block is hidden from the main item UI.
- Generated user-facing text is cleaned from obvious markdown junk.

Critical editorial rule added:

- For automation / bot topics, do not drift into:
  - DIY
  - no-code / constructors
  - fake first-person founder stories
  - self-assembly tutorials
- Default framing must lead toward the author's implementation help:
  - bot production
  - automation under the client's task
  - done-for-you setup

Important caution:

- If an item already has a bad semantic anchor in:
  - title
  - angle
  - keywords
  - manual brief
  then prompt fixes alone may not be enough.
- In that case, clean the item inputs first and only then regenerate.

Next continuation point:

- Review Dzen materials in UI after regeneration.
- Strengthen Dzen CTA wording toward:
  - audit / discovery call
  - bot production
  - implementation under the client's workflow
- Then continue with broader multi-channel plan UX.

## Session 2026-04-29 Stop Point

- Content-plan page right column was refactored into grouped publication slots.
- Same-time materials for different channels should appear under one date/time slot instead of as a flat appended list.
- This was done as a small targeted patch in:
  - `apps/web/src/app/content-plans/[planId]/page.tsx`
- Local `next build` still cannot be run on this machine because `next` is unavailable locally; verify by server deploy/render when continuing.
