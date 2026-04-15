# Handover

## Where Things Live

- Local project root: repo root
- Server project root: `/opt/athena-content`

## Key Files

- Backend entry: `apps/api/app/main.py`
- API router: `apps/api/app/api/router.py`
- Schemas: `apps/api/app/schemas/`
- Services: `apps/api/app/services/`
- Migrations: `apps/api/alembic/`
- Web dashboard: `apps/web/src/app/page.tsx`
- Content plan page: `apps/web/src/app/content-plans/[planId]/page.tsx`
- Content item page: `apps/web/src/app/content-plans/[planId]/items/[itemId]/page.tsx`

## Current Deploy Notes

- Server already has Docker and Docker Compose.
- Running stack includes `postgres`, `redis`, `api`, `web`.
- Historical deploy path on server is still `/opt/athena-content`.

## Next Safe Step

1. Run `POST /api/setup/bootstrap-first-workspace`.
2. Open the dashboard and content plan pages against a live API.
3. Test manual generation via `POST /api/job-runs/content-plans/{plan_id}/items/{item_id}/start-generation`.
4. Inspect `GET /api/content-plans/{plan_id}/items/{item_id}`.
5. Move the item through `POST /api/content-plans/{plan_id}/items/{item_id}/status`.
6. Next product step after validation: improve operator UX around last job, errors, and result summary.

## LLM Notes

- Provider is selected through `LLM_PROVIDER`.
- Supported values: `fallback`, `openrouter`, `openai`, `gemini`.
- This keeps generation logic independent from a single vendor.

## Important Repo Notes

- This repository is the continuation point.
- If resuming from another computer, start from `docs/MEMORY.md`, `docs/PROJECT_STATE.md`, and `docs/SESSION_2026-04-15_CONTEXT.md`.

