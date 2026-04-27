# Session 2026-04-27 Context

## Main Changes

- Dzen added as a second real project channel.
- Dzen channel now has generation mode:
  - `auto`
  - `post`
  - `article`
- Existing plans can now be extended for selected channels only.
- Scheduling changed to parallel groups by channel signature, so Telegram and Dzen materials can share the same publication dates.
- The noisy `Адаптации по каналам` block is hidden from the main item page UI.
- User-facing generated text is cleaned from obvious markdown noise:
  - `#`
  - `**`
  - bullet asterisks

## Important Editorial Decision

- Automation and bot topics must not drift into:
  - constructors
  - no-code DIY
  - fake first-person founder stories
  - self-assembly tutorials
- Default framing must lead toward the author as implementer:
  - bot production
  - implementation under the client's process
  - done-for-you automation help

## Important Caution

- If an item already contains bad semantic anchors in:
  - title
  - angle
  - keywords
  - manual brief
  then model regeneration can keep pulling the text back into the wrong positioning.
- In that case:
  1. clean the item inputs
  2. regenerate the item
  3. verify the new draft before publication

## Current Problematic Example

- One Dzen item drifted into:
  - `my experience`
  - `constructors`
  - `without code`
  - DIY framing
- Prompt was hardened globally against this drift.
- Existing Dzen materials were regenerated after the change.

## Next Continuation Point

- Review regenerated Dzen materials in UI.
- Tighten CTA wording so Dzen posts/articles more clearly lead to:
  - audit / discovery call
  - bot production
  - implementation under the client's workflow
- Then continue with broader multi-channel planning UX.
