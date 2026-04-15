# Handover

## Where Things Live

- Local project root: `codex-workspace`
- Server project root: `/opt/athena-content`

## Key Files

- Backend entry: `apps/api/app/main.py`
- API router: `apps/api/app/api/router.py`
- Models: `apps/api/app/models/`
- Schemas: `apps/api/app/schemas/`
- Migrations: `apps/api/alembic/`
- Deployment: `docker-compose.yml`

## Current Deploy Notes

- Server already has Docker and Docker Compose.
- Running stack includes `postgres`, `redis`, `api`, `web`.
- Web is running in production-style `build + start`.

## Next Safe Step

- Add `ContentPlan` CRUD and first product bootstrap flow.

