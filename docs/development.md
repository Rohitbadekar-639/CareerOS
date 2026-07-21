# Developer setup

> How to clone CareerOS and run the local stack. Configuration details live in
> [`environments.md`](environments.md). Contribution workflow lives in
> [`CONTRIBUTING.md`](../CONTRIBUTING.md).

## Prerequisites

| Tool | Pin / range | Notes |
|---|---|---|
| Node.js | `24.x` (see `.nvmrc`) | `engines.node` is `>=24 <25` |
| pnpm | `10.11.0` | Via `packageManager` in root `package.json` (Corepack) |
| Python | `3.14.x` (see `.python-version`) | `requires-python = ">=3.14,<3.15"` |
| uv | recent stable | Resolves the Python workspace + lockfile |
| Docker + Compose | Docker Engine with Compose v2 | Required for app Postgres + api/worker/web |
| Supabase CLI | recent stable | **Required for Auth** (M1). See [install docs](https://supabase.com/docs/guides/cli) |

Optional but recommended: enable Corepack (`corepack enable`) so the pinned pnpm is used.

## One-command app stack

From the repository root:

```bash
docker compose up --build
```

This starts Postgres (pgvector), api, worker, and web with local-dev defaults from
`docker-compose.yml` / `.env.example`. Compose does **not** require a `.env` file.

When healthy:

| Service | URL / check |
|---|---|
| api | http://127.0.0.1:8000/healthz |
| web | http://127.0.0.1:3000/healthz |
| worker | container `HEALTHCHECK` via `python -m careeros_worker.health` |
| Postgres (app) | `localhost:${POSTGRES_PORT:-5432}` |

Stop with `Ctrl+C` or `docker compose down`. Data persists in the `postgres-data` volume.

### Apply app migrations

After Postgres is up:

```bash
pnpm db:migrate
```

See [`infra/migrations/README.md`](../infra/migrations/README.md).

## Local Supabase Auth (CLI)

Auth is **not** a compose service. Use the Supabase CLI against `supabase/config.toml`.

```bash
# Once: install the CLI (see Supabase docs for your OS)
# Then from the repo root:
supabase start
supabase status -o env
```

Copy `API_URL`, `ANON_KEY`, and `JWT_SECRET` into `.env` as:

| `supabase status` | CareerOS env |
|---|---|
| `API_URL` | `CAREEROS_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_URL` |
| `ANON_KEY` | `CAREEROS_SUPABASE_ANON_KEY` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` |
| `JWT_SECRET` | `CAREEROS_SUPABASE_JWT_SECRET` (must match `supabase/config.toml`) |

Useful URLs after start (defaults from `supabase/config.toml`):

| Service | URL |
|---|---|
| Auth / API | http://127.0.0.1:54321 |
| Studio | http://127.0.0.1:54323 |
| Inbucket (local email) | http://127.0.0.1:54324 |
| Supabase DB (Auth internals only) | `localhost:54322` — **do not** use as `CAREEROS_DATABASE_URL` |

Stop Auth with `supabase stop`.

When api/worker run **inside compose**, they call Auth at
`http://host.docker.internal:54321` (compose default). When they run on the **host**,
use `http://127.0.0.1:54321` in `.env`.

OAuth providers (Google/GitHub) are disabled in `config.toml` until you set client
credentials via `env(...)` vars; email/password works locally without them.

## Host development (without full compose)

### 1. Install dependencies

```bash
pnpm install
uv sync --all-packages
```

### 2. Configure environment

```bash
cp .env.example .env
supabase start
# sync keys from `supabase status -o env` into `.env` if needed
```

Ensure `CAREEROS_DATABASE_URL` points at compose Postgres (`localhost:5432`), not
Supabase’s Auth DB. See [`environments.md`](environments.md).

### 3. Run services

```bash
# Terminal A — App Postgres
docker compose up postgres

# Terminal B — Migrations (once per schema change)
pnpm db:migrate

# Terminal C — Supabase Auth (if not already running)
supabase start

# Terminal D — API
uv run python -m careeros_api

# Terminal E — Worker
uv run python -m careeros_worker

# Terminal F — Web
pnpm --filter @career-os/web dev
```

App-specific notes: `apps/api/README.md`, `apps/worker/README.md`, `apps/web/README.md`.

## Common commands

Root scripts mirror CI (see `.github/workflows/ci.yml`):

```bash
pnpm lint && pnpm lint:py          # ESLint + ruff
pnpm typecheck && pnpm typecheck:py
pnpm test && pnpm test:py
pnpm build                         # Turbo JS/TS build
uv build --all-packages            # Python package builds
pnpm contracts:check               # OpenAPI → TS contracts drift check
pnpm contracts:generate            # Regenerate contracts
pnpm eval:gate                     # Eval gate placeholder
pnpm db:migrate                    # Alembic upgrade head
pnpm db:current                    # Alembic current revision
uv run pip-audit                   # Python dependency audit
pnpm audit --audit-level=high      # JS dependency audit
```

## Pre-commit hooks

Install once after `uv sync`:

```bash
uv run pre-commit install
```

Hooks run a fast subset (ruff format/lint, ESLint, JS/Python typecheck) matching CI.
Full tests, contracts check, and security scans stay in CI. Run everything locally with:

```bash
uv run pre-commit run --all-files
```

## Before you open a PR

Follow [`CONTRIBUTING.md`](../CONTRIBUTING.md): branch naming, Conventional Commits,
Constitution §24 / §25, and green CI gates. Read [`AGENTS.md`](../AGENTS.md) first.
