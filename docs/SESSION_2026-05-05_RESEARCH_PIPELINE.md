# Session 2026-05-05 Research Pipeline

## Main Decision

The content factory should move from a prompt-first architecture to a real research-first architecture.

Prompt rules alone are not enough because:

- the model will loop over the same familiar pains
- freshness will be partly fake
- new solutions and practical signals will enter the plan randomly instead of systematically
- diversity will depend too much on wording instead of real editorial structure

## Architecture Shift

Previous conceptual flow:

1. product context
2. prompt
3. generated topics

New conceptual flow:

1. collect external signals
2. normalize them into research candidates
3. compare them against topic memory
4. apply diversity logic
5. pass cleaned candidate pool into plan generation
6. generate plan topics

## New Models

Added:

- `ResearchSource`
- `ResearchCandidate`
- `TopicMemory`
- `PlanResearchLink`

## New Service

Added:

- `app/services/research_pipeline.py`

Responsibilities:

- fetch research signals
- normalize them into:
  - pain cluster
  - audience segment
  - business process
  - solution type
  - implementation model
  - angle
  - freshness reason
- keep duplicate-group logic
- filter through topic memory
- limit over-concentration of one pain cluster
- attach research to generated plan items
- write/update topic memory

## Integration Points

`plan_generation.py` now:

- collects research candidates before topic generation
- includes research candidate pool in the prompt
- accepts `research_candidate_ids` in LLM output
- stores research metadata in item `research_data`
- writes `PlanResearchLink`
- writes `TopicMemory`

`content_plans.py` and `plan_execution.py` now also keep topic memory updated in:

- manual item creation
- quick post creation
- item updates
- status transitions
- publish-now / autopost

## Verification

Completed:

- backend compile check
- module import check
- Alembic migration through SSH-tunneled DB access
- DB write check for:
  - research sources
  - research candidates
- end-to-end smoke test with:
  - mocked external fetch
  - mocked LLM topic output
- smoke test confirmed:
  - plan items created
  - `TopicMemory` entries created
  - `PlanResearchLink` entries created

## Environment Notes

- local Docker unavailable in current shell
- server Postgres intentionally not public after hardening
- DB access restored through SSH tunnel:
  - local `127.0.0.1:5433`
  - remote Docker container `172.18.0.2:5432`

Current server-backed credentials confirmed from `/opt/athena-content/.env`:

- `POSTGRES_USER=postgres`
- `POSTGRES_PASSWORD=wJlqjYypes6DGFf4xKdZ5aRoTNvB`
- app user inside Docker network:
  - `athena_app`
  - password present in server `.env`

## Bugs Found

Two async SQLAlchemy issues caused `MissingGreenlet`:

- checking `source.candidates`
- checking `existing.candidates`

Fix:

- replace lazy relationship access with explicit SQL existence queries

Production deploy smoke-testing then found two more real issues:

- `StringDataRightTruncationError` because LLM-normalized label fields could exceed `varchar(100)`
- `AttributeError` in `_candidate_memory_key` because topic-memory DB rows are `TopicMemory`, not dicts

Fix:

- clamp label-like fields with `_fit_label(...)` before insert
- support `TopicMemory` directly in `_candidate_memory_key`

## Remaining Real-World Gap

The local shell still cannot perform live outbound `httpx` fetches, so true external-fetch behavior was not verified here directly.

That should be verified after deploy in the real server environment.

## Next Step

1. Re-deploy the latest production fixes
2. Re-run live research-first smoke test in the API container
3. Run one real plan-generation path in deployed code
4. Inspect:
   - research candidate quality
   - memory quality
   - pain diversity
   - topic freshness
