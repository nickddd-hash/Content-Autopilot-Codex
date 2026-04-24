# Session 2026-04-23 Context

## Main Changes

- Added a real API settings screen at `/settings`.
- Added `/api/settings/system` to read and save runtime settings.
- Fixed the API crash after upload support by adding `python-multipart`.
- Fixed upload body size issues by raising Next server action body limit to `20mb`.
- Reworked settings UI into a compact layout:
  - provider
  - keys
  - text / image / video selectors

## Provider Routing

- Text generation now follows:
  - `LLM_PROVIDER`
  - `TEXT_MODEL`
- Image generation now follows:
  - `LLM_PROVIDER`
  - `IMAGE_MODEL`
- OpenRouter text support was added in `apps/api/app/services/llm_client.py`.
- OpenRouter image generation path was added in `apps/api/app/services/media_generator.py`.

## Models Added To UI

- `google/gemini-2.5-flash-image`
- `google/gemini-3.1-flash-image-preview`

## Important Current Note

- The code path is wired, but a real production end-to-end test is still needed:
  - save OpenRouter settings in UI
  - run one text generation
  - run one image regeneration

## Session End State

- Server is up.
- Settings screen works.
- Health check is green.
- Work stopped right after wiring provider-based text/image selection and before final OpenRouter live validation.
