# Session 2026-04-24 Context

## Main Changes

- API settings now autosave.
- OpenRouter-based image regeneration was verified in production after saving provider/model settings.
- Generated images now use a new media URL/version on regeneration, so the browser does not keep showing the old cached file.
- Item page now supports uploading a user image to replace the generated illustration.
- Telegram publishing now sends titles in bold.
- One scheduled Telegram post was manually shortened and then published successfully after hitting the image-caption length limit.

## UI Direction Confirmed

- Reduce visual noise.
- Replace long helper text with compact UI and only minimal tooltip-style hints.
- Keep action rows small and focused.
- Avoid broad rewrites of the plan page and item page because encoding regressions can appear easily.

## Content Plan Page Direction

- Calendar should be compact and placed on the left.
- Show current month from the current date, plus next month.
- Show posts for the selected day on the right.
- In the selected-day list show:
  - scheduled publication date/time
  - topic/title
- Date editing should stay inside the post page, not on the plan page.

## Important Operational Note

- After UI edits on UTF-8-heavy routes, verify:
  - diff size
  - live deployed route
  - rendered Russian text

## Session End State

- Work stopped while reshaping the plan page into a compact two-column calendar layout.
- This should be the next continuation point.
