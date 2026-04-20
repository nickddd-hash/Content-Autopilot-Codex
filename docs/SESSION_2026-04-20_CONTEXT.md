# Session Context 2026-04-20

## What Was Restored

- Local and server work continued from repo `nickddd-hash/Content-Autopilot-Codex`.
- Server deployment is live at `https://content.flowsmart.ru`.
- Reverse proxy and HTTPS were configured on the server.
- The server stack runs from `/opt/athena-content` with `postgres`, `redis`, `api`, and `web`.

## Product State Restored

- Product restored on server: `My PR`
- Brand profile restored on server: `AI без сложности`
- System settings restored on server, including provider keys
- A current content plan for `My PR` was restored on the server with generated items

## Key Code Changes Made

- `apps/api/app/services/plan_generation.py`
  - removed invalid `product_id` usage when creating `ContentPlanItem`
  - added fallback plan-item generation when external LLM generation fails
- `apps/api/app/services/llm_client.py`
  - added safer HTTP error handling for OpenRouter, OpenAI, Gemini, and KIE
  - increased model request timeout to `180s`
- `apps/web/src/app/page.tsx`
  - current dashboard UI version
- `apps/web/src/app/products/[id]/page.tsx`
  - current product page UI version
- `apps/web/src/app/products/[id]/ProductContextForm.tsx`
  - restored product context editing flow
- `apps/web/src/app/content-plans/[planId]/page.tsx`
  - current content plan page UI version

## Channel-Aware Content Logic

- Generation logic was further updated so the system no longer assumes one "primary" channel.
- Instead, the generator now treats the product's active channel set as one combined publishing surface:
  - one core content idea;
  - one master draft;
  - channel-specific adaptations for every active channel.
- Content-plan generation now also takes active channels into account:
  - if Telegram is present, it should still produce strong concise post ideas;
  - if Instagram is present, it can propose carousel / reel / visual-first formats;
  - if YouTube is present, it can propose video-oriented angles;
  - if Blog is present, it can include longer article-worthy angles.
- The logic should not rotate channels mechanically item-by-item.
- Instead, it should choose themes that fit the whole channel set and then adapt one idea across all relevant outputs.
- `channel_targets` and `asset_brief` are now stored in item `research_data`.
- `channel_adaptations` are now returned in generation payloads and displayed in the item detail UI.

## Deployment Notes

- Initial server deploy showed an outdated landing page because deployed `main` did not include the current local working tree changes.
- Server `web` source structure was re-synced from the local working tree.
- `tsconfig.json` had to be updated on the server so the `@/*` alias resolved correctly.
- After redeploy, the dashboard UI renders correctly on `content.flowsmart.ru`.

## LLM / Generation Notes

- A fallback draft stub existed in production because model calls were timing out.
- OpenAI was connected through `OPENAI_API_KEY` and `LLM_PROVIDER=openai`.
- Direct OpenAI generation inside the API container works.
- After increasing backend timeout handling, manual generation succeeded for at least one item with `generation_mode = llm_generated`.

## Product / UX Findings

- Current generated draft shape is too article-like for Telegram posts.
- This needs a product-level change: generation should support a concise Telegram-first post format by default.
- Current operator UX is functional but not friendly enough.
- Content plan discovery after navigation is not obvious enough and should be improved.

## Next Product Priorities

1. Refine the generated output shape so the master draft and per-channel adaptations feel production-ready.
2. Improve content plan and generated draft UX in the operator interface.
3. Add real media-generation flows from `asset_brief` for channels that need visuals or video.
4. Keep hardening production generation so it does not fall back silently under load.
5. Continue work from this repository and from the deployed server state rather than rebuilding from scratch.
