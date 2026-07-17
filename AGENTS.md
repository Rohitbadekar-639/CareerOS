# AGENTS.md — CareerOS

> **Read this before writing any code.** This file orients every human and AI contributor. The binding rules live in the **Engineering Constitution** and the five locked architecture documents.

## What CareerOS is

An AI Career Operating System for India (MVP: software/IT roles). It is **not** a job board, **not** a resume builder, and **not** an auto-applier. It is an AI layer that understands a candidate, surfaces relevant opportunities, and prepares them to win — **with a human approving anything that leaves the platform**.

## Mandatory reading (source of truth, in order)

These are **LOCKED**. No code may violate them without an ADR (`docs/adr/`).

1. `docs/vision.md`
2. `docs/system-architecture.md` (System Architecture)
3. `docs/domain-model.md`
4. `docs/ai-architecture.md`
5. `docs/technical-architecture.md`
6. `docs/engineering-constitution.md` — **highest-priority document; obey it.**

> If any of these files are not yet present in the repo, treat the corresponding approved specification as authoritative and flag the missing file.

## Golden rules (the short list — full rules in the Constitution §26)

- **Never** put business logic in the UI, routers, or controllers.
- **Never** call an LLM inside a React component or on the request path — enqueue to the worker.
- **Never** call a DB, LLM, or vendor SDK outside the `infrastructure`/adapters layer (everything external is behind a Port).
- **Never** hardcode prompts, model names, or secrets.
- **Never** let an AI artifact that represents the user or leaves the platform bypass human approval.
- **Never** fabricate resume/profile content not present in the source Profile version.
- **Never** cross bounded contexts except via domain events or published contracts.
- **Deterministic-first AI**: prefer deterministic graphs with LLM steps over autonomous agents.

## Where things live (see Technical Architecture)

| Path | Purpose |
|------|---------|
| `apps/web` | Next.js 16 frontend (Server-Components-first) |
| `apps/api` | FastAPI modular monolith (sync HTTP; enqueues async work) |
| `apps/worker` | Async agent + background job runtime |
| `contexts/` | DDD bounded contexts (`domain/ application/ ports/ infrastructure/ api/`) |
| `agents/` | AI engine (orchestration, subgraphs, tools, memory, prompts, evals) |
| `packages/` | Shared TS (`contracts`, `sdk`, `ui`, `config`) |
| `shared/` | Shared Python (`shared_kernel`, `platform`, `event_contracts`) |
| `evals/` | Golden datasets + eval runners (CI quality gate) |
| `infra/` | Docker, deploy config, migrations |
| `docs/` | Locked specs + ADRs |

## Workflow

1. Confirm the change conforms to the locked docs + Constitution. If it deviates, **open an ADR first**.
2. Work in a short-lived branch; Conventional Commits; small atomic PRs.
3. Meet the **Definition of Done** (Constitution §25) and pass the **Code Review Checklist** (§24).
4. All CI gates green (lint, typecheck, tests, eval gate, security scan) before merge.

## Current phase

**Implementation is starting at Milestone M0 (Foundations).** See `docs/roadmap/M0-foundations.md`. Do not build product features ahead of the roadmap.
