# @career-os/web

Next.js 16 (App Router) frontend skeleton — M0-T5. Server-Components-first;
no features, no data fetching yet (feature slices arrive from M1 under `features/`,
mirroring backend contexts — see Technical Architecture §3).

All tooling comes from `@career-os/config` (tsconfig base, ESLint flat config,
Prettier, Tailwind v4 theme).

## Routes

- `/` — static landing page.
- `/healthz` — static health JSON (`{"status":"ok"}`), used by smoke tests and
  later by compose/deploy health checks (T14).

## Commands

```bash
pnpm dev        # local dev server
pnpm build      # production build
pnpm start      # serve the production build
pnpm lint       # eslint (shared preset)
pnpm typecheck  # tsc --noEmit
pnpm test       # vitest smoke tests
```
