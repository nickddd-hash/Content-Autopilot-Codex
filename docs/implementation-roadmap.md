# План реализации

## Этап 1. Основа

- Каркас `FastAPI + Next.js`.
- Конфиг окружения.
- Docker Compose для `api`, `web`, `postgres`, `redis`.
- Health-check и базовый dashboard.

## Этап 2. Данные

- `Product`
- `ProductContentSettings`
- `BrandProfile`
- `ContentPlan`
- `ContentPlanItem`
- `BlogPost`
- `SocialAccount`
- `ContentCost`
- `JobRun`

## Этап 3. Генерация

- OpenRouter client
- трекинг стоимости
- генерация контент-плана
- research
- draft + self-review + rewrite
- генерация изображений

## Этап 4. Публикация

- блог
- Telegraph
- IndexNow
- VK single-image
- VK carousel

## Этап 5. Автопилот

- планировщик задач
- автоматическая публикация по времени
- retries и backoff
- idempotency на job level

## Этап 6. Интерфейс

- dashboard
- products
- calendar
- content item details
- social settings
- logs and costs

## Правило разработки

Сначала доводим каждый этап до рабочего состояния, затем идем дальше. Приоритет - надежный автопилот, а не декоративная универсальность.

