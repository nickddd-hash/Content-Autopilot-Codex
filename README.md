# Content Autopilot

Персональный инструмент для автоматического контент-маркетинга и автопубликации по нескольким продуктам.

## Что строим

- `apps/api` - backend на FastAPI, очереди, интеграции, автопилот.
- `apps/web` - dashboard и кабинет управления на Next.js.
- `docs` - живое ТЗ, архитектура и рабочая память проекта.
- `infra` - docker-compose и окружение.

## Принципы проекта

- Это личный рабочий инструмент, а не массовый SaaS.
- Ручной контроль сведен к минимуму.
- Все важные шаги автоматизированы.
- Вмешательство нужно только при ошибках или явной неудачной генерации.

## Scope V1

На текущем этапе строим не весь автопилот сразу, а рабочее ядро:

1. `Product` и его стратегия.
2. `BrandProfile`.
3. `ContentPlan` и `ContentPlanItem`.
4. Минимальный dashboard состояния.
5. Ручной запуск базового generation flow поверх живых данных.

## Что пока не входит в V1

- parser залетевших постов и видео;
- trend / viral monitoring;
- rewrite внешнего контента как отдельный pipeline;
- автопостинг в Instagram;
- production scheduler и full autopilot orchestration.

## Bootstrap для первого рабочего состояния

Чтобы быстро поднять первое живое состояние системы, в API добавлен идемпотентный endpoint:

- `POST /api/setup/bootstrap-first-workspace`

Он создает или переиспользует:

- первый продукт `Health Concilium`;
- глобальный `BrandProfile`;
- стартовый `ContentPlan` на текущий месяц с начальными элементами плана.

## Первый generation contour

После bootstrap в системе есть первый ручной рабочий контур:

- `GET /api/job-runs` - посмотреть последние job runs;
- `POST /api/job-runs/content-plans/{plan_id}/items/{item_id}/start-generation` - вручную запустить generation job для элемента плана.
- `GET /api/content-plans/{plan_id}/items/{item_id}` - получить detail item-а вместе с generated draft/result.
- `POST /api/content-plans/{plan_id}/items/{item_id}/status` - перевести item по lifecycle-статусам.

Текущая версия этого flow уже умеет работать в двух режимах:

- если настроен выбранный LLM provider (`openrouter`, `openai` или `gemini`), собирает prompt из `Product + BrandProfile + ContentPlanItem` и просит модель вернуть structured draft package;
- если ключа нет, провайдер недоступен или внешний вызов не удался, не ломает пайплайн, а использует безопасный fallback generation.

В обоих случаях flow:

- фиксирует `JobRun`;
- переводит `ContentPlanItem` в `draft`;
- записывает generation payload в `research_data`;
- записывает review-метаданные в `article_review`.

Базовый lifecycle `ContentPlanItem` сейчас такой:

- `planned -> draft`
- `draft -> review-ready`
- `review-ready -> draft | published | failed`
- `failed -> planned | draft`

## LLM providers

Generation layer не зашит на одного провайдера. Сейчас поддерживаются:

- `LLM_PROVIDER=openrouter`
- `LLM_PROVIDER=openai`
- `LLM_PROVIDER=gemini`
- `LLM_PROVIDER=fallback`

Для каждого варианта используются свои env-переменные:

- OpenRouter: `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`
- OpenAI: `OPENAI_API_KEY`, `OPENAI_MODEL`
- Gemini: `GEMINI_API_KEY`, `GEMINI_MODEL`

`fallback` полезен для локальной разработки, когда мы хотим проверять workflow и статусы без реального внешнего LLM-вызова.

