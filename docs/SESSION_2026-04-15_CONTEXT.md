# Session Context — 2026-04-15

## What happened in this session

This session moved the project from "scaffold plus docs" into a first real operator-ready V1 workflow.

The biggest changes were:

- the project was treated as a standalone repository, not as part of the restaurant codebase;
- the active product name was normalized to `Content Autopilot`;
- a concrete `v1 scope` was fixed in docs;
- the backend gained bootstrap, generation, job, and lifecycle layers;
- the frontend gained operator pages for dashboard, content plan, and content item.


## Product decisions fixed in this session

- Do not use `Olympus` / `Athena` as the product brand for this repository.
- Keep the current project name as `Content Autopilot`.
- Keep V1 intentionally narrow:
  - `Product`
  - `BrandProfile`
  - `ContentPlan`
  - `ContentPlanItem`
  - dashboard
  - manual generation flow
- Explicitly do **not** drag parser / viral monitoring / Instagram ingestion into V1.


## Backend changes made

### 1. Bootstrap flow

Added an idempotent bootstrap endpoint:

- `POST /api/setup/bootstrap-first-workspace`

It creates or reuses:

- first product `Health Concilium`
- global `BrandProfile`
- starter `ContentPlan` for the current month

Related files:

- `apps/api/app/api/routes/setup.py`
- `apps/api/app/services/bootstrap.py`
- `apps/api/app/schemas/bootstrap.py`


### 2. Job and generation contour

Added manual generation flow:

- `GET /api/job-runs`
- `POST /api/job-runs/content-plans/{plan_id}/items/{item_id}/start-generation`

Generation now:

- builds a prompt from `Product + BrandProfile + ContentPlanItem`
- routes through provider-based LLM client
- falls back safely if no provider is available
- stores generated payload in `research_data`
- stores review metadata in `article_review`
- creates `JobRun`

Related files:

- `apps/api/app/api/routes/job_runs.py`
- `apps/api/app/services/generation.py`
- `apps/api/app/services/generation_prompt.py`
- `apps/api/app/services/llm_client.py`
- `apps/api/app/schemas/job_run.py`


### 3. Provider-based LLM layer

LLM provider is no longer tied to one channel.

Supported values:

- `fallback`
- `openrouter`
- `openai`
- `gemini`

Important envs:

- `LLM_PROVIDER`
- `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`
- `OPENAI_API_KEY`, `OPENAI_MODEL`
- `GEMINI_API_KEY`, `GEMINI_MODEL`

`fallback` must continue to work for local workflow development without credentials.


### 4. Content item lifecycle

Added:

- `GET /api/content-plans/{plan_id}/items/{item_id}`
- `POST /api/content-plans/{plan_id}/items/{item_id}/status`

Current lifecycle:

- `planned -> draft`
- `draft -> review-ready`
- `review-ready -> draft | published | failed`
- `failed -> planned | draft`


## Frontend changes made

### 1. Dashboard

The web app no longer acts only as a landing page.

Dashboard now shows:

- summary metrics
- products
- brand profile
- content plans
- job runs

File:

- `apps/web/src/app/page.tsx`


### 2. Content plan page

Added intermediate operator page:

- `apps/web/src/app/content-plans/[planId]/page.tsx`

This page exists to bridge dashboard and item detail.

It shows:

- all items in the plan
- quick actions
- transition buttons
- links into item detail


### 3. Content item page

Added detail operator page:

- `apps/web/src/app/content-plans/[planId]/items/[itemId]/page.tsx`

It shows:

- generated draft
- hook / CTA
- review notes
- structured payload
- lifecycle actions
- generation action


## Important caveats

- In this environment the web build was not fully verified because `apps/web` dependencies are not installed locally.
- Python files were syntax-checked successfully via `py_compile`.
- There was a temporary encoding issue in one web page; it was corrected by rewriting the page as clean UTF-8.


## Best next step after resume

The next correct step is not new architecture. It is validation and operator UX polish:

1. run bootstrap on a live API
2. run manual generation on real data
3. check content plan page and content item page against live responses
4. improve display of last job, errors, and result summary
5. only after that move into deeper review/editor workflow
