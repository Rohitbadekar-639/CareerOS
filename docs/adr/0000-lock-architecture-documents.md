# ADR-0000: Lock the foundational architecture documents

- **Status:** Accepted
- **Date:** 2026-07-17
- **Deciders:** Founding architecture/engineering
- **Related:** All documents in `docs/`

## Context

Before implementation begins, CareerOS completed a deliberate, phased planning effort:
Vision → System Architecture → Domain Model → AI Multi-Agent Architecture → Technical
Architecture → Engineering Constitution. Each was reviewed and approved in principle.

To prevent architecture drift across many contributors and many AI coding sessions, these
documents must be treated as the permanent source of truth, with a controlled process for
change. Without this, incremental decisions silently erode the intended design.

## Decision

The following documents are **LOCKED** and are the permanent source of truth for CareerOS:

1. `docs/vision.md` — Vision
2. `docs/system-architecture.md` — System Architecture
3. `docs/domain-model.md` — Domain Model
4. `docs/ai-architecture.md` — AI Multi-Agent Architecture
5. `docs/technical-architecture.md` — Technical Architecture
6. `docs/engineering-constitution.md` — Engineering Constitution (highest-priority operational doc)

**No implementation may violate these documents.** Any deviation — including changes to the
documents themselves — requires a new ADR that is reviewed and merged **before** the deviating
code. The ADR must name the specific rule/section it overrides and justify the change.

> Note: all six documents are committed under `docs/`. The System Architecture document is named
> `docs/system-architecture.md`; earlier drafts referred to it as `docs/architecture.md`, and all
> references (AGENTS.md, `.cursor/rules/`, this ADR) were updated to the canonical name.

## Alternatives Considered

| Option | Pros | Cons | Why not chosen |
|--------|------|------|----------------|
| No formal lock (docs as loose guidance) | Max flexibility | Guaranteed drift; decisions lost | Defeats the purpose of the planning phase |
| Lock docs, allow ad-hoc verbal exceptions | Fast | Untracked, unauditable drift | No paper trail; erodes trust |
| **Lock docs + mandatory ADR for any deviation** | Auditable, deliberate, reversible | Slight process overhead | Chosen — overhead is the point |

## Consequences

- **Positive:** stable foundation; every significant decision is written down; drift is prevented; AI agents have an authoritative context to obey.
- **Negative / tradeoffs:** deviations cost an ADR (intentional friction).
- **Follow-ups:** all six documents are committed to `docs/`; keep ADRs numbered sequentially from 0001.

## Compliance

- [x] Consistent with the locked architecture documents (this ADR establishes the lock).
- [x] Engineering Constitution reviewed (defines the amendment rule this ADR formalizes).
- [x] Security/DPDP implications considered (docs encode DPDP posture).
- [x] Cost/observability implications considered (docs encode cost + observability posture).
