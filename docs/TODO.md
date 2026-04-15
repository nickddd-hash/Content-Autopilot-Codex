# TODO

## Immediate

- Зафиксировать `Content Autopilot v1` как ядро: `Product -> BrandProfile -> ContentPlan -> ContentPlanItem -> Dashboard`.
- Поднять первое живое состояние через `POST /api/setup/bootstrap-first-workspace`.
- Проверить, что bootstrap корректно создает `Product`, `BrandProfile` и стартовый `ContentPlan`.
- Довести CRUD для `ContentPlan` и `ContentPlanItem` до рабочего состояния.
- Прогнать первый ручной generation run для `ContentPlanItem`.
- Отобразить последние `JobRun` в dashboard.
- Прогнать lifecycle `planned -> draft -> review-ready` на реальных данных.
- Собрать минимальный dashboard состояния.
- Подготовить seed / bootstrap flow для первого пользователя.
- Проверить generation layer на `fallback`, `openrouter`, `openai` и `gemini`.

## Backend Next

- Alembic upgrade workflow вместо `auto_create_tables`.
- Endpoints для `JobRun` и логов.
- Сервис OpenRouter client.
- Cost tracking service.

## Automation Next

- Генерация плана по продукту.
- Research -> draft -> review -> rewrite pipeline.
- Генерация изображений.
- Scheduler / autopilot rules.

## Ingestion Later

- Parser залетевших постов.
- Parser видео / reels / shorts.
- Trend / viral monitoring.
- Rewrite и adaptation чужого контента под наш tone of voice.

## Deployment Next

- Production `.env` с реальными секретами.
- Домен и reverse proxy.
- HTTPS.
- Backups for Postgres.

