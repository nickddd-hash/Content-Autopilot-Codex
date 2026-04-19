# Session Context 2026-04-19

## What Changed In Product

- Reviewed and stabilized the current `Content-Autopilot-Codex` workspace after large Antigravity edits.
- Fixed product-page save flow for context fields and added visible save feedback.
- Fixed frontend route mismatch for monitoring source creation.
- Cleaned a portion of mojibake / broken UI text on key screens.
- Added a `Create content plan` flow from the product page.
- Added plan-page controls so the operator can:
  - generate themes without a fixed plan theme;
  - generate a special batch of posts for a one-off urgent topic;
  - specify desired post count for that special batch.
- Updated runtime LLM resolution so text generation can read API keys from `system_settings` instead of only `.env`.
- Added KIE-aware runtime LLM support for text generation requests.

## Current Local Runtime Notes

- Local frontend is expected at `http://127.0.0.1:3000`.
- Local backend is expected at `http://127.0.0.1:8000`.
- The app has been flaky in `next dev`; the more stable local mode was `next build` + `next start`.
- `KIE_AI_API_KEY` is saved in `system_settings` and a direct live request to the official KIE endpoint succeeded.
- Content-plan creation without a theme now works.
- Theme generation flow no longer fails at the provider-auth layer, but still needs one more debugging pass to confirm items are persisted reliably after LLM output is returned.

## User Brand / Blog Conclusions

- The user is **not** positioning as a generic programmer, prompt engineer, or AI influencer.
- The strongest positioning is:
  - builder of applied AI and automation systems;
  - product engineer who turns messy real-world processes into working operational flows;
  - someone who connects AI, interfaces, backend, data, automation, and deployment into one usable contour.
- Public framing should avoid hype, guru language, or "visionary AI" tone.
- The natural voice is calm, practical, system-minded, and human.

## Blog Strategy Conclusions

- The recommended Telegram channel model is:
  - a broad, approachable channel;
  - with a clear human owner behind it;
  - so the channel grows reach while also building trust in the user personally.
- The chosen channel name is:
  - `AI без сложности`
- The audience is **not primarily technical**.
- The main audience includes:
  - small business owners;
  - private practitioners;
  - experts and consultants;
  - operators and specialists;
  - people who have heard about AI and automation, but do not proactively research solutions.
- This audience often:
  - delays action;
  - does not want technical detail;
  - responds to concrete examples, practical simplification, and "you can just ask me" trust signals.
- Content should therefore optimize for:
  - simple explanations;
  - practical use cases;
  - useful AI/news filtering without hype;
  - examples of what can be simplified in normal work and life;
  - occasional strong SaaS / tooling explanations, but still in plain language.
- Content should **not** optimize for:
  - developers;
  - AI insiders;
  - abstract trend commentary;
  - motivational fluff;
  - generic "thought leadership".

## Product Context Saved For "My PR"

For the product focused on the user's own PR/blogs, the context that was agreed conceptually is:

- This is a personal-brand / blog product built around the user's real expertise.
- The system should represent the user as a practical builder of applied AI and automation systems.
- Tone should be clear, calm, useful, and non-hyped.
- Target audience should be broad non-technical practitioners who want results without deep tooling research.
- The content factory should be able to generate topics from product context alone, without requiring the operator to always predefine a plan theme.
- The content factory should also support one-off topic injection for urgent or timely themes outside the standing plan.

## Recommended Next Step On Another Machine

1. Pull latest `main`.
2. Open the `My PR` product.
3. Recheck the product context fields.
4. Create a fresh content plan with an empty plan theme.
5. Retest `Generate themes` with:
   - empty special theme;
   - explicit special theme;
   - small count like `2`.
6. If plan items still come back empty, inspect the live backend response from `POST /api/content-plans/{id}/generate-items` and log the raw parsed KIE payload.
