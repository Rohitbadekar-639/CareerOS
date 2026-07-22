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

# Manifests first for cacheable installs.
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml .npmrc .nvmrc turbo.json ./
COPY packages/config/package.json ./packages/config/package.json
COPY packages/sdk/package.json ./packages/sdk/package.json
COPY apps/web/package.json ./apps/web/package.json
RUN pnpm install --frozen-lockfile

COPY packages/config ./packages/config
COPY packages/sdk ./packages/sdk
COPY apps/web ./apps/web
# Bake public Supabase URL/key at build time for the browser bundle.
ARG NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0
ENV NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL \
    NEXT_PUBLIC_SUPABASE_ANON_KEY=$NEXT_PUBLIC_SUPABASE_ANON_KEY \
    CAREEROS_API_BASE_URL=http://api:8000
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
