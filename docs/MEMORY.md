# Memory

## Working Rules

- Make point fixes only when the task is local.
- Do not rewrite whole files for small fixes.
- After each edit, compare the changed file with the previous version and confirm that only the intended lines changed.
- At the start of each session, read memory and handover files before making changes.

## Latest Session Snapshot

- Plan page now has a clickable per-project calendar based on `scheduled_at`.
- Clicking a date shows all posts scheduled for that project on that day.
- Full plan assembly now runs through a background pipeline with latest-job polling.
- Archive screen exists and archived materials are hidden from active plan lists.
- Item page supports save, regenerate text, regenerate illustration, publish now, archive and restore.
- Text regeneration must preserve:
  - `content_direction`
  - `channel_targets`
  - `include_illustration`
  and regenerate the title too.
- Telegram publish rule is now explicit in product behavior:
  - image posts must fit one Telegram message with caption
  - new plan-generated Telegram posts are created with illustration mode enabled
  - backend additionally shortens generated Telegram drafts to a caption-safe size when needed
  - publish errors must be shown in UI instead of crashing the page

## Product Direction

- Это не массовый SaaS.
- Это личный AI-автопилот для управления контентом по своим продуктам и личному бренду.
- Главный сценарий сейчас: личный блог `My PR` с упором на Telegram как основной канал.
- Система должна быть понятной нетехническому пользователю и не требовать постоянной ручной модерации.

## Audience And Positioning

- Основная аудитория: предприниматели, владельцы малого бизнеса, частные практики, эксперты, консультанты и операционные специалисты.
- Это люди, которые уже слышали про AI, но не хотят глубоко разбираться в инструментах, стеках и интеграциях.
- Контент должен делать AI понятным, спокойным и прикладным, без пафоса и без техно-снобизма.
- При этом контент не должен сводиться только к бизнесу и автоматизации. Нужны:
  - practical
  - educational
  - news
  - opinion
  - critical

## Current Content Rules

- План должен уметь смешивать направления через проценты.
- Быстрый кастомный пост должен уметь выбирать:
  - тематику
  - каналы из текущего проекта
- Для `opinion` допустим более свободный, жизненный и философский угол, без скатывания в продуктовые советы.
- Для Telegram нужен именно готовый пост, а не статья.
- Иллюстрация должна быть компактной, а не огромной.

## Current UX Direction

- Дашборд должен быть максимально простым: только активные продукты.
- На странице продукта:
  - компактный блок каналов
  - контент-планы под каналами
  - стратегия продукта в сворачиваемом блоке
- На странице плана:
  - одна главная кнопка `Генерация`
  - возможность быстро добавить свой пост
  - минимум лишних статусов и лишних действий
- В интерфейсе не должно быть дёргания карточек и прочих раздражающих hover-эффектов.

## Automation Direction

- Сейчас реализована генерация тем, быстрых постов, генерация текста и иллюстрации по item.
- Следующий важный шаг: генерация материалов по всему плану одним действием, а не по одному item вручную.
- Ещё один следующий шаг: режим автопостинга, где система сама:
  - собирает темы
  - генерирует материалы
  - публикует их по плану
- При этом пользователь всё равно должен иметь возможность удалять и редактировать материалы.

## Planned But Not Implemented Yet

- Оценка контент-плана через персонажей-аудиторов.
- Идея: несколько проверяющих ролей из ЦА, например:
  - домохозяйка / обычный нетехнический читатель
  - предприниматель-фрилансер
  - эксперт / частная практика
  - владелец малого бизнеса
- Они должны оценивать понятность и релевантность плана, а потом влиять на финальную сборку.
- Это не текущая задача.
- Внедрять этот слой нужно на этапе финальной отладки продукта, а не раньше.

## Technical Direction

- Backend: FastAPI
- Frontend: Next.js
- Database: PostgreSQL
- Queue foundation: Redis
- Infra: Docker Compose
- Основное окружение сейчас не localhost, а сервер `content.flowsmart.ru`

## Current Server Notes

- Домен: `https://content.flowsmart.ru`
- Серверный проект: `/opt/athena-content`
- Контейнеры: `postgres`, `redis`, `api`, `web`
- Production web работает через `next build && next start`
- Во время пересборки `web` сайт временно отдаёт `502`, пока не завершится build
- Для приложения используется отдельный пользователь БД `athena_app`, чтобы не упираться в дрейф пароля `postgres`

## Latest Automation Update

- Plan page now has `Собрать материалы`.
- Item page now has manual Telegram publish through `Запостить`.
- API now exposes:
  - `POST /content-plans/{plan_id}/build-materials`
  - `POST /content-plans/{plan_id}/items/{item_id}/generate`
  - `GET /content-plans/{plan_id}/items/{item_id}/latest-job`
  - `POST /content-plans/{plan_id}/items/{item_id}/publish`
- The API startup now runs a lightweight in-process autopost loop.
- Due items in status `review-ready` are published automatically to validated Telegram channels when the product has:
  - `autopilot_enabled = true`
  - `social_posting_enabled = true`
- Scheduling uses:
  - `publish_days`
  - `publish_time_utc`
- Generation now filters stale `channel_targets` through the product's real active channels so old `blog/vk` traces do not distort Telegram prompts.

## Important Constraints

- Работать только внутри `codex-workspace`
- Не коммитить `.env` и локальные временные файлы
- Не трогать `master-ai`, если это не отдельная задача пользователя
## Session 2026-04-23

- Added a real `/settings` page and `/api/settings/system`.
- Fixed the settings 404.
- Fixed API startup after upload support by adding `python-multipart`.
- Fixed image upload crashes by raising Next server action body limit to `20mb`.
- Added compact settings UI:
  - provider
  - provider keys
  - text / image / video model selectors
- Added OpenRouter text support in `llm_client.py`.
- Unified model selection:
  - `TEXT_MODEL`
  - `IMAGE_MODEL`
  - `VIDEO_MODEL`
- Text now uses `LLM_PROVIDER + TEXT_MODEL`.
- Images now use `LLM_PROVIDER + IMAGE_MODEL`.
- Added OpenRouter image path in `media_generator.py`.
- Added image model options for:
  - `google/gemini-2.5-flash-image`
  - `google/gemini-3.1-flash-image-preview`
- Latest stop point:
  - server code is ready for provider-based text/image routing
  - live OpenRouter generation still needs a manual end-to-end test after saving settings in UI

## Session 2026-04-24

- Settings UI now autosaves:
  - provider
  - keys
  - text / image / video model selectors
- OpenRouter image regeneration is wired and working when production settings are actually set to:
  - `LLM_PROVIDER=openrouter`
  - `IMAGE_MODEL=google/gemini-3.1-flash-image-preview`
- A browser cache issue made regenerated images look unchanged; image regeneration now uses a new media URL/version so the browser does not reuse the old file.
- User image upload is supported on the item page and can replace generated illustrations.
- Telegram publishing now forces bold titles and published a previously blocked scheduled post after shortening it to fit one image caption.
- Plan page and item page were aggressively cleaned up for less helper text and less visual noise.
- Important caution from this session:
  - keep frontend edits point-sized
  - do not broad-rewrite UTF-8-heavy UI files
  - after UI edits, compare the diff and check the live route, because encoding regressions can slip in fast
- Latest stop point:
  - content plan page now uses a more compact calendar layout
  - goal is calendar on the left, posts for selected day on the right
  - editing publication date should stay inside the post page, not inside the plan page

## Session 2026-04-30

- Practical content generation must now contain concrete examples, concrete scenarios and specific applied details.
- Plan generation now tries to avoid repeating or lightly rephrasing topics used during roughly the last 30 days for the same product.
- If duplicate filtering removes too many generated items, the backend tops the plan up with fallback topics that are also checked against recent-topic similarity.
- The plan page now has a safe title fallback for broken data:
  - if `item.title` looks corrupted like `???`, use `generated_draft_title` if it is clean.

## Session 2026-05-04 Strategy Reset

- The current content strategy is now explicitly centered on `AI bez slozhnosti` as a business-oriented channel about:
  - AI for small business
  - bots
  - CRM
  - automation
  - content systems
- The channel should not compete as a generic AI-news or prompt-tips blog.
- Main positioning:
  - Nikolay helps entrepreneurs, experts, marketers and small teams understand where AI is actually useful in their business
  - then helps diagnose, design and implement a working system
- The core audience is Russia/CIS non-technical business users who:
  - heard about AI
  - tried ChatGPT or analogs superficially
  - got weak results
  - concluded AI is vague, overhyped or not for their business
  - still suspect there is real value somewhere

- Main lead magnet / entry point:
  - free `AI business audit/helper`
  - bot asks 7 short business questions
  - returns:
    - diagnosis
    - 3 automation priorities
    - quick win for this week
    - suitable tools
    - approximate ROI
- The desired funnel is:
  - post
  - interest / recognition
  - free AI business audit
  - personal result
  - dialogue with Nikolay
  - consultation / automation map / MVP / implementation

- The product strategy for content now is:
  - not "teach AI in general"
  - but show where business loses time, money, leads and manual effort
  - and how AI, bots, CRM and automation can solve that in practical terms

- Recommended content mix for the current strategy:
  - `practical`: 60
  - `educational`: 20
  - `news`: 10
  - `opinion`: 5
  - `critical`: 5
- This is intentionally more business-centered than the older broader AI-public-education mix.

- Hardcoded prompt strategy was updated in code:
  - plan generation now includes base strategy rules about:
    - business orientation
    - real business situations
    - movement toward free AI audit
  - post generation now includes the same base strategy plus stronger anti-rules
- Hardcoded anti-rules now explicitly push the model away from:
  - DIY framing
  - no-code evangelism as the default answer
  - fake first-person stories
  - abstract AI hype
  - technical overload for non-technical readers
  - generic AI news without practical value
  - random-tool enthusiasm without process diagnosis

- The plan UI defaults were updated to the new mix.
- The plan generation defaults were updated to the new mix.
- The mix descriptions in UI were clarified:
  - `practical` now explicitly covers business situations, automation, cases and applied scenarios
  - `educational` now covers simple AI explanations and useful work/business tricks
  - `critical` now maps well to `AI without illusions`

- Important product principle confirmed:
  - the strategy/research/memory logic should not live only in manual product settings
  - it should be partly hardcoded as the base operating principle of the content factory
- Current hardcoded principle:
  - generate content as a practical translator between AI and business
  - prefer recognizable business situations
  - prefer diagnosis and implementation help over self-assembly
  - use soft CTA logic toward audit / consultation / implementation

- Immediate next continuation point:
  - continue configuring the May content plan from this strategy base
  - if needed, add a stronger `research-first` layer before plan generation
  - later, add memory of rejected topics / angles as a real filtering mechanism instead of prompt-only guidance

## Session 2026-05-05 Research-First Pipeline

- A real `research-first` foundation was added to the content factory instead of relying only on prompt rules.
- The plan-generation flow is no longer conceptually:
  - product context
  - prompt
  - generated topics
- It is now conceptually:
  - collect external signals
  - normalize them into structured research candidates
  - filter them through topic memory and diversity logic
  - then generate plan topics from the cleaned pool

- Added new DB models:
  - `ResearchSource`
  - `ResearchCandidate`
  - `TopicMemory`
  - `PlanResearchLink`
- Added Alembic migration:
  - `20260505_0006_add_research_pipeline_models.py`

- Added service:
  - `app/services/research_pipeline.py`
- Main responsibilities:
  - collect external signals
  - normalize them into:
    - pain cluster
    - audience segment
    - business process
    - solution type
    - implementation model
    - angle
    - freshness reason
  - keep a duplicate-group key
  - filter by topic memory
  - limit over-concentration of one pain cluster
  - link research candidates to generated plan items
  - write/update topic memory for generated or manually created content items

- Research-first logic now lives in code, not only in docs/prompts.
- `plan_generation.py` now:
  - collects research candidates before generating plan topics
  - passes research candidate pool into plan-generation prompt
  - expects `research_candidate_ids` in generated items
  - stores research metadata into item `research_data`
  - writes `PlanResearchLink`
  - writes `TopicMemory`

- `content_plans.py` and `plan_execution.py` now update topic memory in additional flows:
  - manual item creation
  - quick post creation
  - item updates
  - item status changes
  - publish-now / autopost status sync

- Diversity logic now exists on two layers:
  - prompt rules
  - research candidate selection layer
- Current implemented practical rule:
  - one familiar pain should not monopolize the next several posts
  - candidate selection limits too many items from the same pain cluster in the same pool

- Important environment note:
  - local Docker is not available in this shell
  - server hardening previously removed public Postgres exposure
  - database access for verification was restored through a safe SSH tunnel:
    - local `127.0.0.1:5433`
    - tunneled to server Docker Postgres container
- Current working server-side DB credentials were confirmed from `/opt/athena-content/.env`
- Alembic migration was successfully applied to the server-backed database through the tunnel.

- Verification completed:
  - Python compile/import checks passed
  - Alembic migration passed
  - research-source / research-candidate DB writes passed
  - end-to-end smoke test with mocked external fetch and mocked LLM plan output passed:
    - generated plan items were created
    - `TopicMemory` entries were written
    - `PlanResearchLink` entries were written

- Bugs found and fixed during verification:
  - two async lazy-loading bugs in `research_pipeline.py` caused `MissingGreenlet`
  - both were removed by replacing relationship access with explicit SQL checks
  - production smoke-test then exposed a `varchar(100)` overflow from LLM-normalized labels
  - this was fixed by clamping normalized labels with `_fit_label(...)` before DB insert
  - a later production smoke-test exposed another bug in `_candidate_memory_key`
  - the helper assumed only `ResearchCandidate | dict`, but real DB memory entries are `TopicMemory`
  - this was fixed by letting `_candidate_memory_key` handle `TopicMemory` objects directly

- Still true:
  - real external fetch is not testable from this local shell because outbound `httpx` requests are blocked here
  - production API container is still on older deployed code until next deploy

- Immediate next continuation point:
  - update `HANDOVER.md`
  - deploy fresh backend code to production
  - run one real production-side plan generation check after deploy
