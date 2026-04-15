# План реализации

## Этап 1. V1 ядро

- Каркас `FastAPI + Next.js`.
- Конфиг окружения.
- Docker Compose для `api`, `web`, `postgres`, `redis`.
- `Product`, `BrandProfile`, `ContentPlan`, `ContentPlanItem`.
- Базовый dashboard состояния.
- Первый ручной flow поверх живых данных.

## Этап 2. Автоматизация ядра

- OpenRouter client
- трекинг стоимости
- генерация контент-плана
- research
- draft + self-review + rewrite
- генерация изображений

## Этап 3. Публикация

- блог
- Telegraph
- IndexNow
- VK single-image
- VK carousel

## Этап 4. Автопилот

- планировщик задач
- автоматическая публикация по времени
- retries и backoff
- idempotency на job level

## Этап 5. Ingestion и trend layer

- parser залетевших постов;
- parser видео / reels / shorts;
- trend / viral monitoring;
- rewrite и adaptation внешнего контента;
- раскладка одной идеи в post / carousel / reel / article / channel adaptation.

## Правило разработки

Сначала доводим каждый этап до рабочего состояния, затем идем дальше. Приоритет - надежный автопилот, а не декоративная универсальность.

