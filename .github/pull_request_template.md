## Summary

<!-- What changed and why. Link issues / ADRs. Note tradeoffs. -->

-

## Milestone / scope

- [ ] Fits the current milestone roadmap (see `docs/roadmap/`)
- [ ] No product/domain logic ahead of the roadmap
- [ ] Deviations from locked docs have a merged ADR

## Test plan

<!-- How a reviewer can verify. Check all that apply. -->

- [ ] `pnpm lint && pnpm lint:py`
- [ ] `pnpm typecheck && pnpm typecheck:py`
- [ ] `pnpm test && pnpm test:py`
- [ ] `pnpm build`
- [ ] `pnpm contracts:check` (if OpenAPI / contracts touched)
- [ ] `docker compose up --build` healthy (if Docker / compose / Dockerfiles touched)
- [ ] Other: <!-- describe -->

## Code review checklist (Constitution §24)

Reviewers MUST verify:

- [ ] **Constitution & locked docs respected**; deviations have an ADR
- [ ] **Correct layer/context;** dependency direction intact; no framework leakage into domain
- [ ] **No business logic in UI, routers, or controllers**
- [ ] **No direct SQL, LLM calls, or vendor SDKs outside infrastructure/adapters**
- [ ] **No hardcoded prompts, model names, secrets, or magic values**
- [ ] **Aggregate/transaction boundaries respected;** cross-context via events only
- [ ] **Inputs validated;** typed errors; safe error responses
- [ ] **AuthZ enforced;** RLS/user scoping intact; PII handled per policy
- [ ] **Structured I/O, grounding, and HITL** honored for AI changes; eval gate passed
- [ ] **Tests present and meaningful;** regression test for bug fixes
- [ ] **Observability:** logging/tracing/metrics adequate; no PII in logs
- [ ] **Performance:** no N+1, bounded queries, async for slow work, context size sane
- [ ] **Naming from Ubiquitous Language;** no god classes; no circular deps
- [ ] **Docs/ADRs updated;** PR explains WHAT and WHY
- [ ] **Nothing from §26 present**

## Definition of Done (Constitution §25)

- [ ] Author confirms all §25 items are met (see `CONTRIBUTING.md`)
- [ ] CI fully green (contracts, lint, typecheck, build, tests, eval-gate, security scan)
- [ ] Self-reviewed before requesting review
