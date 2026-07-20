# syntax=docker/dockerfile:1.7
# CareerOS worker image (M0-T13).
# Same multi-stage uv pattern as the api. The worker is not an HTTP service, so
# its healthcheck is the health CLI (exit 0 when ready).
# Build context is the repo root.

# ---- builder ----
# Pinned to the exact patch in .python-version so uv finds the interpreter
# without needing a managed download.
FROM python:3.14.5-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.11.29 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app
COPY . .

RUN uv sync --frozen --no-dev --no-editable --package careeros-worker

# ---- runtime ----
FROM python:3.14.5-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home appuser

WORKDIR /app
COPY --from=builder --chown=appuser:app /app/.venv /app/.venv

USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-m", "careeros_worker.health"]

CMD ["python", "-m", "careeros_worker"]
