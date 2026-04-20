# Server Access And Secrets

Sensitive file. This document contains infrastructure access details, passwords, and API keys for the current server environment.

## Server

- Domain: `https://content.flowsmart.ru`
- Server IP: `82.21.72.233`
- OS: Ubuntu 22.04
- Project root on server: `/opt/athena-content`

## SSH Access

- User: `root`
- Private key path on the current Windows machine: `C:\Users\DIT\.ssh\athena_content_ed25519`
- Public key path on the current Windows machine: `C:\Users\DIT\.ssh\athena_content_ed25519.pub`

Example:

```powershell
ssh -i $HOME\.ssh\athena_content_ed25519 root@82.21.72.233
```

## Docker Stack

The stack is run from:

```text
/opt/athena-content
```

Main services:

- `postgres`
- `redis`
- `api`
- `web`

Useful commands:

```bash
cd /opt/athena-content
docker compose ps
docker compose logs --tail=200 api
docker compose logs --tail=200 web
docker compose up -d --build
```

## Reverse Proxy / Public Access

- Public web entry: `https://content.flowsmart.ru`
- `nginx` is installed on the server
- HTTPS certificate was issued with Let's Encrypt

Current proxy shape:

- `/` -> `127.0.0.1:3000`
- `/api/` -> `127.0.0.1:8000`

## Server .env

Current `/opt/athena-content/.env` values:

```env
POSTGRES_DB=athena_content
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/athena_content
REDIS_URL=redis://redis:6379/0
ENVIRONMENT=development
AUTO_CREATE_TABLES=true

OPENROUTER_API_KEY=
VK_CLIENT_ID=
VK_CLIENT_SECRET=
OAUTH_REDIRECT_BASE=https://content.flowsmart.ru

BRAND_MASCOT_URL=
BRAND_LOGO_URL=
APP_BASE_URL=https://content.flowsmart.ru
NEXT_PUBLIC_API_BASE_URL=https://content.flowsmart.ru/api
```

## Database

- Database name: `athena_content`
- Postgres user: `postgres`
- Postgres password: `postgres`
- Internal docker host: `postgres`
- Internal Postgres port: `5432`
- Host-exposed Postgres port: `5433`

Examples:

```bash
docker exec -it athena-content-postgres-1 psql -U postgres -d athena_content
```

```text
postgresql+asyncpg://postgres:postgres@postgres:5432/athena_content
```

## Runtime Provider Settings In App DB

These are stored in the server app settings table and are part of the active runtime configuration:

- `LLM_PROVIDER=openai`
- `OPENAI_MODEL=gpt-5.4`
- `KIE_MODEL=gpt-5-4`
- `KIE_BASE_URL=https://api.kie.ai/codex/v1`

Live API keys are intentionally not stored in plaintext in this git-tracked document because GitHub push protection blocks repository pushes that contain active secrets.

To retrieve the current runtime settings, including keys, run:

```powershell
ssh -i $HOME\.ssh\athena_content_ed25519 root@82.21.72.233 "docker exec -i athena-content-postgres-1 psql -U postgres -d athena_content -c \"select key, value from system_settings order by key;\""
```

That command will show the live values for:

- `OPENAI_API_KEY`
- `KIE_AI_API_KEY`
- `OPENROUTER_API_KEY`
- any future provider keys stored in `system_settings`

## Current Product State On Server

Restored and working:

- Product: `My PR`
- Brand profile: `AI без сложности`
- Current plan month: `2026-04`
- Active content plan contains generated items and draft generation is wired to OpenAI

## Important Notes

- This repository now contains sensitive infrastructure data because the user explicitly requested it.
- API keys are retrievable from the server with the command above, but are not stored in plaintext in git because GitHub blocks pushes that contain active secrets.
- If this repository will ever become public or shared more broadly, rotate every secret in this environment immediately.
- The application code is in git, but the live database contents still remain server-side state.
