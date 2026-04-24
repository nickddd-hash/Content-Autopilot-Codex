# Session 2026-04-22 Context

## Main Product Changes

- Added background plan pipeline flow for content plan assembly.
- Added plan-level calendar inside the content plan page.
- Added archive screen and archive/restore flow for materials.
- Added manual Telegram publishing from the item page.
- Added readable publish error handling on the item page instead of crashing SSR.

## Telegram Publishing Rule

- A Telegram post with illustration must fit into one message caption.
- New plan-generated Telegram items are created with `include_illustration = true`.
- Generation prompt targets a shorter Telegram format.
- Backend now additionally shortens generated Telegram drafts to a caption-safe size when needed.

## Regeneration Behavior

- `Перегенерировать текст` on the item page now regenerates from the current draft.
- Regeneration preserves:
  - `content_direction`
  - `channel_targets`
  - `include_illustration`
- Title should regenerate together with the body.

## UI / UX Notes

- Dashboard remains product-only.
- Product page is compact and plan-first.
- Plan page now includes:
  - pipeline polling
  - plan mix
  - quick post modal
  - calendar by day
  - content queue
- Item page now focuses on:
  - editing
  - regeneration
  - illustration
  - publish now
  - archive

## Important Follow-Up

- Add manual date editing for scheduled posts.
- Improve the calendar from day drill-down into a fuller monthly planning tool.
- Keep pushing toward a simpler "generate -> schedule -> autopost" flow with less manual friction.
