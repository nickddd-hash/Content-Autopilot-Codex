# Memory

## Product Direction

- Это не массовый SaaS.
- Это личный рабочий инструмент для владельца нескольких продуктов.
- Главный приоритет: максимум автоматизации и минимум ручного контроля.
- Ручное участие допустимо только как аварийное вмешательство.
- Текущее рабочее имя проекта: `Content Autopilot`.
- `Olympus` / `Athena` больше не использовать как бренд этого проекта, потому что это названия ресторанной системы.

## Technical Direction

- Отдельный сервер под проект.
- База: PostgreSQL.
- Очереди: Redis + Celery.
- Backend: FastAPI.
- Frontend: Next.js.
- Инфраструктура: Docker Compose.
- Supabase и n8n не являются обязательной частью ядра проекта.
- LLM layer должен быть сменным, а не привязанным к одному вендору.
- Поддерживаемые LLM providers: `fallback`, `openrouter`, `openai`, `gemini`.

## Important Constraints

- Не смешивать проект с ресторанным репозиторием.
- Работать внутри отдельного репозитория `Content-Autopilot-Codex`.
- Не коммитить `.env` и локальные временные файлы.
- Не трогать `master-ai`, если это не отдельная задача пользователя.

## User Context

- Пользователь не позиционирует себя как программист.
- Пользователю нужен результат и рабочий инструмент, а не сложная ручная настройка.
- Систему нужно делать понятной и управляемой, но без обязательной ежедневной модерации.

## Current Working Shape

- У проекта уже есть рабочий backend lifecycle:
  - bootstrap первого workspace;
  - `ContentPlan` / `ContentPlanItem`;
  - manual generation jobs;
  - item detail endpoint;
  - lifecycle transitions `planned -> draft -> review-ready -> ...`
- У проекта уже есть рабочий web contour:
  - dashboard;
  - content plan page;
  - content item page;
  - operator actions для generation и status transitions.

## Important Practical Notes

- `apps/web` пока не проверялся через реальную сборку в этой среде, потому что локально не установлены зависимости Next.
- В backend generation service сначала пытается использовать выбранный LLM provider, а при ошибке уходит в fallback вместо падения пайплайна.

