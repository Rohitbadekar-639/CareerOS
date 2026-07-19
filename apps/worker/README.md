# careeros-worker

Async background-job runtime — M0-T7 skeleton.

Starts, reads typed settings, and idles against the `TaskQueue` port
(`careeros_platform.task_queue`) until signalled to stop. No job handlers and no
LangGraph yet — dispatch arrives in M3.

## Run locally

```bash
uv run python -m careeros_worker    # starts and idles; Ctrl+C to stop cleanly
```

## Test

```bash
uv run pytest apps/worker
```
