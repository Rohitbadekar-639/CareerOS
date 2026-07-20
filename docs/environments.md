# Environments & configuration

> **M0-T16.** Documents the configuration surface that exists in the repository today.
> Do not invent variables here — every application setting must exist on
> `careeros_platform.settings.Settings` (or in `docker-compose.yml` for compose-only knobs).

Locked references: Technical Architecture §8 (Configuration), §11 (Deployment);
Engineering Constitution §11 (Security — secrets).

## Environments

| Environment | Value of `CAREEROS_ENVIRONMENT` | How it runs today |
|---|---|---|
| Development | `development` (default) | Local `docker compose` and/or host processes (`uv` / `pnpm`) |
| Staging | `staging` | Not provisioned in M0; same typed settings + secret-store injection when deployed |
| Production | `production` | Not provisioned in M0; same typed settings + secret-store injection when deployed |

Staging and production are named by the typed `Environment` enum so fail-fast config works
the same way in every tier. Deploy targets land in later milestones; until then, treat
`staging` / `production` as reserved values for process env / secret stores only.

## Loading order (application settings)

Implemented in `shared/platform/careeros_platform/settings.py` via `load_settings()`:

1. **Explicit constructor kwargs** (highest; used in tests)
2. **Process environment variables** with prefix `CAREEROS_`
3. **Environment-specific dotenv** — `.env.<environment>` (e.g. `.env.staging`)
4. **Base dotenv** — `.env`

Missing required values raise a pydantic `ValidationError` at construction (fail-fast).
Dotenv files are git-ignored (see `.gitignore`). Only `.env.example` is tracked.

## Application settings (`CAREEROS_*`)

| Env var | Settings field | Required | Default | Notes |
|---|---|---|---|---|
| `CAREEROS_DATABASE_URL` | `database_url` | **yes** | — | Credentials live here; never commit real values |
| `CAREEROS_APP_NAME` | `app_name` | no | `career-os` | Service name in logs |
| `CAREEROS_ENVIRONMENT` | `environment` | no | `development` | One of `development`, `staging`, `production` |
| `CAREEROS_LOG_LEVEL` | `log_level` | no | `INFO` | Structured JSON logger level |
| `CAREEROS_API_HOST` | `api_host` | no | `127.0.0.1` | Compose overrides to `0.0.0.0` inside the api container |
| `CAREEROS_API_PORT` | `api_port` | no | `8000` | Published host port via compose as well |

These are the **only** application settings that exist in M0. There are no LLM, auth,
storage, queue, Redis, or feature-flag env vars yet — those arrive with later milestones
behind ports, and will be added to `.env.example` in the same PR that introduces them.

## Compose-only variables

Used by `docker-compose.yml` for the local stack. Not read by `Settings`.

| Env var | Default | Purpose |
|---|---|---|
| `POSTGRES_USER` | `careeros` | Postgres role |
| `POSTGRES_PASSWORD` | `careeros` | Postgres password (local-dev only) |
| `POSTGRES_DB` | `careeros` | Database name |
| `POSTGRES_PORT` | `5432` | Host port published for Postgres |
| `WEB_PORT` | `3000` | Host port published for the web container |

Inside compose, api/worker receive:

```text
CAREEROS_DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
```

so containers talk to Postgres by service DNS (`postgres`), not `localhost`.

The web image sets `NODE_ENV=production`, `PORT=3000`, and `HOSTNAME=0.0.0.0` in
`infra/docker/web.Dockerfile`; compose additionally sets `NODE_ENV` and `PORT` on the
web service. These are not `CAREEROS_*` settings. The web app has no app-level env
vars in M0.

## Secrets

Rules (Constitution + Technical Architecture §8):

- **Never commit secrets.** `.env`, `.env.*` (except `.env.example`), keys, and `secrets/`
  directories are git-ignored.
- **Local development:** copy `.env.example` → `.env` and use the local-dev defaults.
  Those defaults (`careeros` / `careeros`) are for the disposable compose Postgres only.
- **Staging / production:** inject required values (especially `CAREEROS_DATABASE_URL`)
  from the **platform secret store** as process environment variables. Do not bake
  secrets into images, compose files, or the client bundle.
- **Rotation:** treat secret-store values as rotatable; the app only reads env at
  process start (`get_settings()` is cached for the process lifetime).
- **No secrets in logs or the browser.** Structured logging redacts PII; privileged
  credentials never reach Next.js Client Components.

M0 does not yet wire a cloud secret manager. When staging/prod deploys land, secrets
remain env-injected — only the source (secret store vs local `.env`) changes.

## Checklist: keep `.env.example` honest

When adding a field to `Settings` or a new compose variable:

1. Add it to `.env.example` with a safe local default or a commented placeholder.
2. Document it in the tables above in the same PR.
3. Never put a real credential in either file.
