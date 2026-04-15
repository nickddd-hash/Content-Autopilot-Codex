# Project State

## Current Status

Проект уже вынесен в отдельный репозиторий `Content-Autopilot-Codex` и больше не должен рассматриваться как вложенная рабочая область старой ресторанной системы.

На текущий момент готовы:

- каркас backend на FastAPI;
- каркас frontend на Next.js;
- Docker Compose стек для `postgres`, `redis`, `api`, `web`;
- базовые ORM-модели;
- Alembic migrations;
- API для:
  - health;
  - dashboard summary;
  - products CRUD;
  - brand profile.
  - content plans;
  - setup/bootstrap;
  - job runs.
- manual generation contour c provider-based LLM layer;
- content item lifecycle transitions;
- operator UI:
  - dashboard;
  - content plan page;
  - content item page.

## Server Status

Сервер подготовлен и доступен по SSH-ключу.

На сервере:

- настроен firewall;
- активирован swap;
- загружен проект в `/opt/athena-content`;
- контейнеры успешно стартуют.

## Verified Working

- `GET /`
- `GET /api/health`
- `GET /api/dashboard/summary`
- `GET /api/products`
- OpenAPI содержит `brand-profile`, `content-plans`, `setup`, `job-runs`

## Not Done Yet

- прогон bootstrap и generation flow на реально поднятом окружении;
- реальная проверка web build/run после установки зависимостей;
- полноценный review/editor UX поверх generated drafts;
- генерация контент-плана как отдельный flow поверх существующего generation engine;
- article pipeline после `review-ready`;
- VK integration;
- Celery workers and scheduler;
- production reverse proxy and domain setup;
- secrets and production env hardening.

