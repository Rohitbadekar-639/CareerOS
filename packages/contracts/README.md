# @career-os/contracts

OpenAPI-generated TypeScript types and Zod schemas. **Source of truth:** the
FastAPI app in `apps/api` (Technical Architecture §1 / §4).

## Commands

```bash
pnpm contracts:generate   # regenerate openapi.json + src/
pnpm contracts:check      # regenerate and fail if git diff is non-empty
pnpm --filter @career-os/contracts typecheck
```

## Pipeline

1. `scripts/export_openapi.py` dumps a deterministic OpenAPI document from
   `create_app` (no live server).
2. `openapi-typescript` → `src/types.ts`
3. `json-schema-to-zod` (driven by `scripts/generate.mjs`) → `src/schemas.ts`

CI runs `contracts:check` and blocks merges when the committed output is stale.
