# syntax=docker/dockerfile:1.7
# CareerOS api image (M0-T13).
# Multi-stage: uv builds a locked, dev-free virtualenv; the runtime image ships
# only that venv on a slim Python base and runs as a non-root user.
# Build context is the repo root (uv workspace resolution needs the members).

# ---- builder ----
# Pinned to the exact patch in .python-version so uv finds the interpreter
# without needing a managed download.
FROM python:3.14.5-slim AS builder

# Pinned uv (Constitution: pin versions).
COPY --from=ghcr.io/astral-sh/uv:0.11.29 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app
COPY . .

# Resolve exactly the api package + its workspace deps, no dev group, and install
# non-editable so the runtime image needs no source tree — just the venv.
RUN uv sync --frozen --no-dev --no-editable --package careeros-api

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

EXPOSE 8000

# Liveness via the app's own /healthz (no curl in the slim image).
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2).status == 200 else 1)"]

CMD ["python", "-m", "careeros_api"]
