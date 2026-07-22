# Environments & configuration

> Documents the configuration surface that exists in the repository today.
> Do not invent variables here — every application setting must exist on
> `careeros_platform.settings.Settings` (or in `docker-compose.yml` for compose-only knobs).
> Next.js `NEXT_PUBLIC_*` vars are documented here but are **not** Python Settings.

Locked references: Technical Architecture §5 (Auth), §8 (Configuration), §11 (Deployment);
Engineering Constitution §11 (Security — secrets).

## Environments

| Environment | Value of `CAREEROS_ENVIRONMENT` | How it runs today |
|---|---|---|
| Development | `development` (default) | Local `docker compose` + **Supabase CLI** for Auth; and/or host processes (`uv` / `pnpm`) |
| Staging | `staging` | Not provisioned yet; same typed settings + secret-store injection when deployed |
| Production | `production` | Not provisioned yet; same typed settings + secret-store injection when deployed |

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
| `CAREEROS_DATABASE_URL` | `database_url` | **yes** | — | App Postgres (compose). Never the Supabase CLI DB on `:54322` |
| `CAREEROS_SUPABASE_URL` | `supabase_url` | **yes** | — | Local: `http://127.0.0.1:54321` after `supabase start` |
| `CAREEROS_SUPABASE_ANON_KEY` | `supabase_anon_key` | **yes** | — | From `supabase status`; local-only demo key in `.env.example` |
| `CAREEROS_SUPABASE_JWT_SECRET` | `supabase_jwt_secret` | **yes** | — | Legacy HS256 verify; must match `supabase/config.toml` `[auth].jwt_secret` locally |
| `CAREEROS_SUPABASE_JWT_AUDIENCE` | `supabase_jwt_audience` | no | `authenticated` | Supabase JWT `aud` claim |
| `CAREEROS_SUPABASE_JWKS_URL` | `supabase_jwks_url` | no | `{supabase_url}/auth/v1/.well-known/jwks.json` | Override when JWKS host ≠ issuer (compose uses `host.docker.internal`) |
| _(computed)_ | `supabase_jwt_issuer` | — | `{supabase_url}/auth/v1` | Not an env var; derived for JWT verification |
| `CAREEROS_APP_NAME` | `app_name` | no | `career-os` | Service name in logs |
| `CAREEROS_ENVIRONMENT` | `environment` | no | `development` | One of `development`, `staging`, `production` |
| `CAREEROS_LOG_LEVEL` | `log_level` | no | `INFO` | Structured JSON logger level |
| `CAREEROS_API_HOST` | `api_host` | no | `127.0.0.1` | Compose overrides to `0.0.0.0` inside the api container |
| `CAREEROS_API_PORT` | `api_port` | no | `8000` | Published host port via compose as well |

There are no LLM, storage, queue, Redis, or feature-flag env vars yet — those arrive with
later milestones behind ports, and will be added to `.env.example` in the same PR that
introduces them. **Service-role keys are intentionally omitted** from Settings until a
server use case needs them; they must never appear in `NEXT_PUBLIC_*` or the client bundle.

## Web (Next.js) public env

Used by the BFF / browser Supabase client (later M1 batches). Not read by Python `Settings`.

| Env var | Required for auth UI | Notes |
|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | yes (when auth UI lands) | Same value as `CAREEROS_SUPABASE_URL` locally |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | yes (when auth UI lands) | Same value as `CAREEROS_SUPABASE_ANON_KEY` locally |

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

so containers talk to Postgres by service DNS (`postgres`), not `localhost`. Supabase Auth
runs on the **Docker host** via the CLI. Compose defaults `CAREEROS_SUPABASE_URL` to
`http://host.docker.internal:54321` so api/worker containers can reach it; host-run
processes should use `http://127.0.0.1:54321` (see `.env.example`).

The web image sets `NODE_ENV=production`, `PORT=3000`, and `HOSTNAME=0.0.0.0` in
`infra/docker/web.Dockerfile`; compose additionally sets `NODE_ENV` and `PORT` on the
web service.

## Migrations

Application schema: Alembic under `infra/migrations/` (see that README). Commands:

```bash
pnpm db:migrate    # upgrade head
pnpm db:current    # show revision
```

## Secrets

Rules (Constitution + Technical Architecture §8):

- **Never commit secrets.** `.env`, `.env.*` (except `.env.example`), keys, and `secrets/`
  directories are git-ignored.
- **Local development:** copy `.env.example` → `.env`, run `supabase start`, sync keys from
  `supabase status -o env` if they differ from the example.
- **Staging / production:** inject required values from the **platform secret store** as
  process environment variables. Do not bake secrets into images, compose files, or the
  client bundle.
- **Rotation:** treat secret-store values as rotatable; the app only reads env at
  process start (`get_settings()` is cached for the process lifetime).
- **No secrets in logs or the browser.** Structured logging redacts auth-related keys;
  privileged credentials never reach Next.js Client Components.

## Checklist: keep `.env.example` honest

When adding a field to `Settings` or a new compose variable:

1. Add it to `.env.example` with a safe local default or a commented placeholder.
2. Document it in the tables above in the same PR.
3. Never put a real credential in either file.
