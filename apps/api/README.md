# careeros-api

FastAPI modular monolith (sync HTTP; enqueues async work) — M0-T6 skeleton.

Boots and wires to typed settings from `careeros-platform`. No domain logic yet;
the root router is an empty placeholder.

## Endpoints

- `GET /healthz` — liveness; returns `{"status":"ok"}`.
- `GET /readyz` — readiness with per-dependency checks (stubbed until adapters land).

## Cross-cutting behaviour

- **Request correlation (T11):** every request opens a span; its trace id is
  returned in the `x-trace-id` response header and stamped on every log line.
- **Problem-details (T12):** domain errors and unexpected exceptions are mapped to
  RFC 9457 `application/problem+json`. Stack traces and internal messages never
  leak to clients.

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
See [`docs/environments.md`](../../docs/environments.md) for the full configuration
surface and [`docs/development.md`](../../docs/development.md) for local setup.
