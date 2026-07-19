# careeros-worker

Async background-job runtime — M0-T7 skeleton.

Starts, reads typed settings, and idles against the `TaskQueue` port
(`careeros_platform.task_queue`) until signalled to stop. No job handlers and no
LangGraph yet — dispatch arrives in M3.

## Run locally

```bash
uv run python -m careeros_worker    # starts and idles; Ctrl+C to stop cleanly
```

## Health check (T12)

The worker is not an HTTP service, so its liveness/readiness surface is a CLI
suitable for a container `HEALTHCHECK` — exit `0` when ready, non-zero otherwise:

```bash
uv run python -m careeros_worker.health
```

## Test

```bash
uv run pytest apps/worker
```
