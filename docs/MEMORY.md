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

## Session 2026-04-26 Memory

Stop state:

- Work is on `main` in `C:\Users\nickd\.gemini\antigravity\scratch\Content-Autopilot-Codex`.
- Production is `https://content.flowsmart.ru` on server `82.21.72.233`, remote path `/opt/athena-content`.
- Latest deployed code commit before this docs handover is `2dd301e fix: compact schedule after manual publish`.
- Production responded successfully after deploy: site `200`, health `{"status":"ok"}`.

Implemented and deployed:

- Explicit content-plan creation flow: product page opens plan settings instead of generating immediately.
- Double confirmation before actual generation.
- Stop/cancel generation button and backend cancel endpoint.
- Editable plan title.
- One main content plan per product. New generated posts are appended into that plan.
- Optional illustration generation for plan generation, default off.
- Posts still assume an illustration slot by default even when image generation is skipped.
- Archived posts are excluded from visible active counters.
- Image generation button moved into the visual block.
- Draft text regeneration now has a user comment/notes field.
- RU/CIS localization was added to prompts so examples fit Russian-speaking users first.
- Top draft `Regenerate post` button was removed to reduce duplicate actions.
- Manual `Publish now` now compacts the future schedule by shifting later unpublished posts into the freed slot.

Important user/business context:

- User is Nikolay, not Nikita.
- Blog/channel name chosen: `AI bez slozhnosti`.
- The blog is broad, not for technical AI people.
- Core audience: people in Russia/CIS who have heard about AI and automation, are interested in theory, but postpone action or wait until someone trusted shows them a simple path.
- Also include unexpected adjacent audiences: astrologers, architects, freelancers, small experts, small business owners, consultants, and people who could benefit from automation but do not know what to ask for yet.
- Tone: simple, practical, calm, friendly, without technical show-off.

Operational reminders:

- Deploy after code changes unless the user explicitly says not to.
- Docs-only commits do not need deploy.
- Use small targeted frontend patches; avoid broad rewrites of plan/item pages because encoding issues have happened before.
- If testing generation, remember that immediate illustration generation can spend extra provider tokens.
