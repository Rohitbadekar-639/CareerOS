# careeros-api

FastAPI modular monolith (sync HTTP; enqueues async work) — M0-T6 skeleton.

Boots and wires to typed settings from `careeros-platform`. No domain logic and
no endpoints yet: the root router is an empty placeholder, and health/readiness
endpoints arrive in T12.

## Run locally

```bash
uv run python -m careeros_api      # starts uvicorn on CAREEROS_API_HOST:CAREEROS_API_PORT
```

## Test

```bash
uv run pytest apps/api
```

## Configuration

Settings come from `careeros_platform.settings.Settings` (env prefix `CAREEROS_`).
The full configuration surface (per-environment loading, required-var fail-fast)
is owned by T9; this skeleton uses only the minimal typed settings it needs.
