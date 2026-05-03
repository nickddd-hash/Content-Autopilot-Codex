# TODO

## Now

Current focus additions:

- Add manual date editing for scheduled posts from plan or item page
- Add a clearer monthly calendar experience on the plan page
- Recheck Telegram publication flow after automatic shortening of plan-generated drafts
- Make publishable length constraints visible earlier in the editing flow, not only at publish time

- Сделать на уровне плана действие, которое генерирует не только темы, но и сами материалы по всему плану
- Превратить текущий flow в более автоматический: тема -> пост -> иллюстрация без ручного клика по каждому item
- Ещё сильнее упростить страницу плана и убрать остаточные лишние состояния

## Product UX

- Добавить более явный flow для “материал готов, можно публиковать”
- Продумать кнопку уровня плана вроде `Собрать материалы`
- Сделать более понятный переход от плана к публикации
- Привести оставшиеся экраны к чистому русскому UI без артефактов кодировки

## Automation

- Реализовать настоящий автопостинг:
  - система сама собирает темы
  - система сама генерирует материалы
  - система сама публикует по расписанию
- Сохранить возможность ручного редактирования и удаления материалов даже в автопилоте

## Plan Intelligence

- Добавить персонажей-проверяющих для оценки плана
- Базовые роли для старта:
  - обычный нетехнический читатель
  - предприниматель-фрилансер
  - эксперт / частная практика
  - владелец малого бизнеса
- На основе их оценок пересобирать или докручивать план
- Делать это на этапе финальной отладки, не раньше

## Security Follow-Up

- Ротировать внешние ключи провайдеров после инцидента:
  - OpenAI
  - KIE
  - другие сторонние API-ключи, если используются
- Отдельно пройтись по серверу на предмет признаков повторной компрометации
- При желании добавить ещё один уровень защиты:
  - fail2ban
  - docker hardening
  - отдельные Docker networks без лишней публикации портов

## Technical

- Нормализовать persistence для медиа, чтобы иллюстрации не зависели от пересборки контейнера
- При необходимости вынести публикацию и автогенерацию в фоновые задачи
- Держать серверный деплой как основное окружение, а localhost только для локальных правок
## Session 2026-04-23 Follow-Up

- Run live end-to-end OpenRouter text test after saving production settings.
- Run live end-to-end OpenRouter image regeneration test after saving production settings.
- If OpenRouter image results are good, decide whether to keep OpenAI only as fallback.
- Add clearer settings/help text so it is obvious that provider choice affects both text and image generation.

## Session 2026-04-24 Follow-Up

- Finish the content plan page redesign:
  - compact current-month + next-month calendar on the left
  - selected-day post list on the right
  - no date editing controls inside the plan page
- Keep item page as the single place for:
  - date changes
  - editing
  - regenerate text
  - regenerate image
  - publish now
- Recheck the live rendered plan page after the calendar redesign and verify there are no encoding regressions.
- Keep future UI cleanup point-sized; avoid broad file rewrites on plan/item routes.

## Session 2026-04-26 Follow-Up

- Run one real publish-now test on a future scheduled post and confirm:
  - selected post publishes immediately
  - its old future calendar slot is freed
  - later unpublished posts shift up
  - archived/published items do not distort active plan counters
- Improve post-generation depth for broad non-technical AI education:
  - avoid vague "AI is useful" posts
  - prefer concrete examples and named tools/models where relevant
  - for model-comparison topics, cover Gemini, Claude, DeepSeek, ChatGPT, and practical strengths/limits
- Keep default plan generation without immediate illustration generation unless the user enables it.
- Preserve all-channel planning:
  - do not pick a single main channel
  - plan topics and formats around the whole product channel set
  - adapt the same idea per channel when needed
- Later technical hardening:
  - move long generation/publish jobs to a durable worker/queue
  - clean corrupted docs/UI strings only with encoding-safe tooling
  - keep deploy verification after every code change

## Session 2026-04-27 Follow-Up

- Review regenerated Dzen materials in UI and tighten CTA wording so they more clearly lead to:
  - audit / discovery call
  - bot production
  - implementation under the client's workflow
- Remove remaining bad semantic anchors from legacy Dzen items where needed:
  - title
  - angle
  - keywords
  - manual brief
- Keep automation-topic generation away from:
  - constructors
  - no-code DIY
  - first-person fake experience
  - self-assembly advice

## Session 2026-05-03 Follow-Up

- Update global/content-plan prompts using `docs/SESSION_2026-05-03_CHANNEL_STRATEGY.md`.
- Add business-centered content mix logic instead of generating only one type of business case.
- Add prompt checks:
  - who recognizes themselves
  - what illusion is removed
  - why the reader should come to Nikolay
- Add or design research layer for practical automation/business examples.
- Later add rejected-topic memory and analytics feedback into planning.
