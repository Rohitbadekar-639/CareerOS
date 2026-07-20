# Contributing to CareerOS

Thank you for contributing. CareerOS is an AI Career Operating System — **not** a job board,
resume builder, or auto-applier. Read this before opening a PR.

## Mandatory reading

1. [`AGENTS.md`](AGENTS.md) — orientation and golden rules
2. [`docs/engineering-constitution.md`](docs/engineering-constitution.md) — **highest priority**
3. Locked architecture docs (listed in `AGENTS.md`)
4. Current milestone roadmap: [`docs/roadmap/M0-foundations.md`](docs/roadmap/M0-foundations.md)

Local setup: [`docs/development.md`](docs/development.md).
Configuration & secrets: [`docs/environments.md`](docs/environments.md).

## Developer workflow

1. **Confirm fit.** The change must conform to the locked docs and Constitution. If it
   deviates, open an [ADR](#architecture-decision-records-adrs) and merge it **before**
   the code.
2. **Branch from the default trunk** (`master` today; Constitution §15 says `main` —
   use whichever is the primary integration branch on the remote). Short-lived
   branches only (Constitution §15).
3. **Implement one logical change.** Prefer small, reviewable PRs (< ~400 lines of
   meaningful diff).
4. **Meet Definition of Done** (Constitution §25) before requesting review.
5. **Keep CI green:** contracts, lint, typecheck, build, tests, eval-gate, security scan
   (see `.github/workflows/ci.yml`).
6. **Self-review** the diff, then request review. Author merges after approval.

### Branch naming

```text
type/short-description
```

Examples: `feat/match-explanations`, `fix/resume-parse-dates`, `docs/m0-t16-environments`,
`chore/ci-cache`.

Types align with Conventional Commits below.

## Conventional Commits

Commits use [Conventional Commits](https://www.conventionalcommits.org/) in the
**imperative mood** (Constitution §15):

| Type | Use for |
|---|---|
| `feat:` | A new capability visible to users or other packages |
| `fix:` | A bug fix |
| `chore:` | Tooling, scaffolding, dependency churn with no behaviour change |
| `refactor:` | Internal restructuring with no behaviour change |
| `docs:` | Documentation only |
| `test:` | Tests only |
| `perf:` | Performance improvement |
| `sec:` | Security fix or hardening |

Examples:

```text
docs: document CAREEROS_* settings and local setup
chore: add pre-commit hooks for lint and typecheck
fix: map unhandled errors to problem-details
```

Rules:

- One logical change per commit when practical; each commit should leave the tree working.
- Reference an issue or ADR when applicable (`Fixes #123`, `ADR-0000`).
- No secrets, generated junk, or large binaries — respect `.gitignore`.
- Do not use `--no-verify` to bypass hooks unless explicitly justified.

## Architecture Decision Records (ADRs)

Any deviation from a locked document or the Constitution **requires an ADR** merged
before the code (Constitution amendment rule; ADR-0000).

1. Copy [`docs/adr/template.md`](docs/adr/template.md) to `docs/adr/NNNN-short-title.md`.
2. Fill Context, Decision, Alternatives, Consequences, Compliance.
3. Name the exact rule/section overridden and justify it.
4. Open a PR for the ADR alone (or ahead of the implementing PR).
5. Only then land the code that depends on it.

## Pull requests

See Constitution §16 and the PR template (`.github/pull_request_template.md`).

- Describe **what** and **why**; link issues/ADRs; note tradeoffs.
- All CI gates green.
- At least one approval (two for safety-kernel, auth, security, or migration changes).
- No new lint/type suppressions without inline justification.
- Update docs/contracts in the same PR when the change invalidates them.

## Code review checklist

Reviewers verify Constitution **§24**. The PR template embeds the same checklist.
Authors should self-check before requesting review:

- [ ] Constitution & locked docs respected; deviations have an ADR
- [ ] Correct layer/context; dependency direction intact; no framework leakage into domain
- [ ] No business logic in UI, routers, or controllers
- [ ] No direct SQL, LLM calls, or vendor SDKs outside infrastructure/adapters
- [ ] No hardcoded prompts, model names, secrets, or magic values
- [ ] Aggregate/transaction boundaries respected; cross-context via events only
- [ ] Inputs validated; typed errors; safe error responses
- [ ] AuthZ enforced; RLS/user scoping intact; PII handled per policy
- [ ] Structured I/O, grounding, and HITL honored for AI changes; eval gate passed
- [ ] Tests present and meaningful; regression test for bug fixes
- [ ] Observability: logging/tracing/metrics adequate; no PII in logs
- [ ] Performance: no N+1, bounded queries, async for slow work, context size sane
- [ ] Naming from Ubiquitous Language; no god classes; no circular deps
- [ ] Docs/ADRs updated; PR explains WHAT and WHY
- [ ] Nothing from Constitution §26 present

## Definition of Done

A change is **Done** only when all of Constitution **§25** are true, including:

1. Meets the requirement; conforms to locked docs + Constitution
2. Correct context/layer; ports respected
3. Typed end-to-end; validation at boundaries
4. Tests written and passing; AI eval gate passed (when applicable)
5. Security reviewed (authz, PII, secrets, injection, uploads)
6. Observability in place
7. Errors handled and mapped safely
8. Performance acceptable
9. Docs/ADRs/contracts updated in the same PR
10. CI fully green; PR reviewed and approved
11. Feature-flagged if risky; rollback path exists
12. No item from §26 introduced

## Issues

Use the GitHub issue templates under `.github/ISSUE_TEMPLATE/`:

- **Bug report** — unexpected behaviour with repro steps
- **Feature request** — product/engineering proposal (must still fit the roadmap)
- **Task / chore** — scaffolding, docs, tooling within the current milestone

Do not open issues that ask for product features ahead of the current milestone unless
they are intentional roadmap discussion. M0 is foundations only — no domain logic.

## Local quality gates

```bash
pnpm lint && pnpm lint:py
pnpm typecheck && pnpm typecheck:py
pnpm test && pnpm test:py
pnpm build
uv build --all-packages
pnpm contracts:check
pnpm eval:gate
uv run pip-audit
pnpm audit --audit-level=high
```

Install git hooks: `uv run pre-commit install` (see [`docs/development.md`](docs/development.md)).

## License

Proprietary — see [`LICENSE`](LICENSE). By contributing you agree that contributions are
owned under the same terms.
