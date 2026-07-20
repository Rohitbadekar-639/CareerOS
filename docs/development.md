# Developer setup

> **M0-T16.** How to clone CareerOS and run the local stack. Configuration details live in
> [`environments.md`](environments.md). Contribution workflow lives in
> [`CONTRIBUTING.md`](../CONTRIBUTING.md).

## Prerequisites

| Tool | Pin / range | Notes |
|---|---|---|
| Node.js | `24.x` (see `.nvmrc`) | `engines.node` is `>=24 <25` |
| pnpm | `10.11.0` | Via `packageManager` in root `package.json` (Corepack) |
| Python | `3.14.x` (see `.python-version`) | `requires-python = ">=3.14,<3.15"` |
| uv | recent stable | Resolves the Python workspace + lockfile |
| Docker + Compose | Docker Engine with Compose v2 | Required for the one-command stack |

Optional but recommended: enable Corepack (`corepack enable`) so the pinned pnpm is used.

## One-command local stack

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
| Postgres | `localhost:${POSTGRES_PORT:-5432}` |

Stop with `Ctrl+C` or `docker compose down`. Data persists in the `postgres-data` volume.

## Host development (without full compose)

### 1. Install dependencies

```bash
pnpm install
uv sync --all-packages
```

### 2. Configure environment

```bash
cp .env.example .env
```

Ensure `CAREEROS_DATABASE_URL` points at a reachable Postgres (compose Postgres on
`localhost:5432` is the usual choice). See [`environments.md`](environments.md).

### 3. Run services

```bash
# Terminal A — Postgres (if not already up)
docker compose up postgres

# Terminal B — API
uv run python -m careeros_api

# Terminal C — Worker
uv run python -m careeros_worker

# Terminal D — Web
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
