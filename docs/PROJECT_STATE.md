# Project State

## Current Status

Проект развернут как отдельная рабочая область `codex-workspace` внутри основного репозитория.

На текущий момент готовы:

- каркас backend на FastAPI;
- каркас frontend на Next.js;
- Docker Compose стек для `postgres`, `redis`, `api`, `web`;
- базовые ORM-модели;
- первая Alembic migration;
- API для:
  - health;
  - dashboard summary;
  - products CRUD;
  - product settings;
  - brand profile.

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
- OpenAPI содержит `brand-profile` и `product settings` endpoints

## Not Done Yet

- заполнение первого продукта реальными данными;
- content plan CRUD;
- генерация контент-плана через LLM;
- article pipeline;
- VK integration;
- Celery workers and scheduler;
- production reverse proxy and domain setup;
- secrets and production env hardening.

