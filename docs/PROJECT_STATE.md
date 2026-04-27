# Project State

## Current Status

Проект живёт как отдельная рабочая область `codex-workspace` и используется на сервере `content.flowsmart.ru`.

Сейчас в рабочем состоянии есть:

- FastAPI backend
- Next.js frontend
- PostgreSQL
- Redis
- Docker Compose деплой
- nginx + HTTPS на сервере

## What Works In Product Terms

Additional working pieces:

- Background plan pipeline with latest job polling
- Plan calendar grouped by day inside each content plan
- Archive page with published and archived materials
- Manual Telegram publish from the item page
- Readable UI error for Telegram publish conflicts

- Дашборд с активными продуктами
- Продукт `My PR`
- Страница продукта с каналами, контент-планами и контекстом
- Создание и удаление контент-планов
- Генерация тем для плана
- Настройка mix по направлениям
- Быстрое создание кастомного поста
- Генерация текста и иллюстрации по item
- Редактирование поста на странице item

## Current Plan Generation Model

План умеет смешивать типы контента:

- practical
- educational
- news
- opinion
- critical

Эти доли задаются на уровне плана и учитываются при генерации тем.

## Current Quick Post Model

Быстрый пост поддерживает:

- ввод готового текста или тезисов
- выбор тематики
- выбор каналов из текущего проекта

Если запускать генерацию через ИИ:

- генерируется заголовок и текст
- item сохраняется в план
- учитываются выбранные тематика и каналы

## Security State

На `2026-04-22` сервер прошёл аварийную зачистку после подозрительной нагрузки внутри контейнера `postgres`.

Сделано:

- стек пересоздан
- наружу больше не публикуются `postgres` и `redis`
- `api` и `web` привязаны к `127.0.0.1`
- внутренние пароли ротированы
- серверное приложение переведено в production-режим

Публичная поверхность сейчас должна быть сведена к:

- `80`
- `443`
- `22`

## Known Product Gaps

- План пока в основном формирует темы, а не весь набор материалов автоматически
- Нет одной кнопки, которая собирает все посты и визуалы по плану целиком
- Автопостинг как полный рабочий контур ещё не реализован
- Персонажи-проверяющие пока только идея, не код

## Known Operational Notes

- Во время `docker compose up -d --build web` домен может временно отдавать `502`
- Это нормально, пока `next build` не завершится
- После сборки `web` снова поднимается через `next start`
- Внешние API-ключи провайдеров нужно будет ротировать отдельно вручную
## Session 2026-04-23 Additions

- System settings now have a real UI and API:
  - `/settings`
  - `/api/settings/system`
- Upload support is stable after:
  - adding `python-multipart`
  - increasing Next server action body limit to `20mb`
- Provider routing is now moving to shared settings:
  - `LLM_PROVIDER`
  - `TEXT_MODEL`
  - `IMAGE_MODEL`
  - `VIDEO_MODEL`
- Text generation supports OpenRouter.
- Image generation supports provider-based routing and now includes an OpenRouter path.
- New OpenRouter image model options are present in settings UI.
- Still required:
  - confirm real OpenRouter text generation in production
  - confirm real OpenRouter image regeneration in production

## Session 2026-04-24 Additions

- API settings now autosave on change/blur.
- Production image regeneration has already been verified through OpenRouter after the provider/model were saved in settings.
- Item page supports replacing generated illustrations with a user-uploaded image.
- Telegram publish behavior now includes bold titles by default.
- The content plan page is being simplified toward:
  - compact calendar
  - clearer selected-day list
  - less inline editing noise
- Main current product direction for the plan page:
  - calendar on the left
  - posts for selected day on the right
  - date changes inside the post page, not inside the plan page

## Session 2026-04-26 State

Current architecture/product state:

- A product should have one main content plan.
- New plan generation appends active posts into the main plan instead of creating many simultaneous plans.
- Plan generation is intentionally explicit:
  - product page create/open action
  - settings page
  - double confirmation before real generation
  - stop/cancel generation action
- Plan generation defaults to text/topics/schedule without generating images immediately.
- Visuals are still part of the expected content structure, but image generation can happen later from the item visual block.
- Draft regeneration supports a user instruction/comment so weak drafts can be redirected without manual rewriting.
- Publish-now behavior now preserves schedule regularity by compacting future unpublished posts after a future slot is emptied.

Production state:

- Latest deployed code commit before docs handover: `2dd301e fix: compact schedule after manual publish`.
- Production URL: `https://content.flowsmart.ru`.
- Server path: `/opt/athena-content`.
- Health was OK after deploy.

Product voice state:

- The project is being shaped around Nikolay's personal/broad AI blog, `AI bez slozhnosti`.
- Target is broad Russia/CIS audience, not technical AI practitioners.
- Content should make people feel that AI/automation is approachable and useful today.
- Recommended editorial direction: practical tips, simple explanations, Russian/CIS-relevant examples, and occasional deeper SaaS/automation case studies.

## Session 2026-04-27 State

New working pieces:

- Dzen is now supported as a second real content channel.
- Dzen channel supports generation mode:
  - `auto`
  - `post`
  - `article`
- Existing plans can be extended with channel-selected materials.
- Scheduling is now parallel by channel group instead of one global queue.

Important editorial correction:

- Automation and bot topics must not drift into:
  - constructors
  - no-code DIY
  - fake first-person founder stories
  - self-assembly tutorials
- Default framing must lead to the author as implementer:
  - bot production
  - implementation under the client's process
  - done-for-you automation help

Current caution:

- If an item already contains bad semantic anchors in its title, angle, keywords or manual brief, model regeneration can inherit that drift.
- In such cases, clean the item inputs first, then regenerate.
