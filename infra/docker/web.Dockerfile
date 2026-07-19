# syntax=docker/dockerfile:1.7
# CareerOS web image (M0-T13).
# Multi-stage pnpm build producing a Next.js standalone bundle, served from a
# slim Node base as a non-root user. Production web runs on Vercel; this image
# powers the local docker compose environment (T14).
# Build context is the repo root.

# ---- builder ----
FROM node:24-slim AS builder

ENV CI=1 \
    NEXT_TELEMETRY_DISABLED=1
RUN corepack enable

WORKDIR /app

# Manifests first for cacheable installs. Only apps/web and packages/config are
# JS workspace members (the Python apps have no package.json).
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml .npmrc .nvmrc turbo.json ./
COPY packages/config/package.json ./packages/config/package.json
COPY apps/web/package.json ./apps/web/package.json
RUN pnpm install --frozen-lockfile

COPY packages/config ./packages/config
COPY apps/web ./apps/web
RUN pnpm --filter @career-os/web build

# ---- runtime ----
FROM node:24-slim AS runtime

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home appuser

WORKDIR /app

# Standalone output already contains the minimal server + node_modules; static
# assets are copied alongside as Next expects.
COPY --from=builder --chown=appuser:app /app/apps/web/.next/standalone ./
COPY --from=builder --chown=appuser:app /app/apps/web/.next/static ./apps/web/.next/static

USER appuser

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
    CMD ["node", "-e", "require('http').get('http://127.0.0.1:3000/healthz',r=>process.exit(r.statusCode===200?0:1)).on('error',()=>process.exit(1))"]

CMD ["node", "apps/web/server.js"]
