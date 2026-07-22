# ADR-0001: Job Intelligence MVP slice (Opportunity + Matching)

- **Status:** Accepted
- **Date:** 2026-07-22
- **Deciders:** Founding architecture/engineering
- **Related:** `docs/domain-model.md`, `docs/technical-architecture.md` §13, `docs/ai-architecture.md`, `docs/vision.md`

## Context

CareerOS is pivoting product emphasis toward an **AI Job Search Operating System**.
M1 authentication is in place. Locked milestones sequence Opportunity Ingestion (M4)
after Profile (M2) and Matching (M5) after both. Waiting for a full Profile context
would delay a working job-discovery MVP for real seekers.

Public ATS board feeds (Greenhouse Boards API, Ashby Job Board API) are **official
public JSON feeds** published by employers — treated as permitted sources with
recorded provenance (Vision FR-5 / Opportunity Source rules).

## Decision

1. **Ship a Job Intelligence MVP** that implements Opportunity Discovery + Normalization
   (deterministic) and Matching/Ranking **ahead of** full Career Profile / Documents,
   without redesigning the modular monolith, auth, ports, or worker split.

2. **Domain language remains `Opportunity` / `Match` / `Recommendation`.** Product UI
   may say “jobs”; persistence and APIs use Opportunity terminology where practical.

3. **New packages:** `contexts/opportunity` and `contexts/matching`, five-layer each.
   Cross-context access only via application orchestration in API/worker (DTOs), never
   shared tables or domain imports across contexts.

4. **Initial `OpportunitySource` adapters:** Greenhouse and Ashby public board feeds,
   registered behind a port; additional boards/sources are config + adapter additions.

5. **Minimal `SeekerCriteria`** lives in Matching until Career Profile lands: resume
   text, skills, years experience, preferred locations, salary expectations, remote
   preference — enough to rank. Profile will later become the source of truth via ACL.

6. **Ranking is deterministic-first** (`HeuristicMatchScorer` behind a `MatchScorer`
   port). No LLM on the HTTP request path. A future LLM adapter may run only in the
   worker. Dashboard shows **precomputed** recommendations above a relevance threshold.

7. **Scheduler** runs in the existing worker tier (periodic ingest + rematch enqueue),
   not a new deployable.

## Alternatives Considered

| Option | Why not |
|--------|---------|
| Wait for full M2 Profile before any jobs | Blocks seeker value too long |
| Rename Opportunity → Job in domain | Violates locked Ubiquitous Language |
| Scrape LinkedIn/Naukri | Violates Vision / legal source rules |
| LLM scoring on `/v1/recommendations` | Violates Constitution (no LLM on request path) |
| New microservice for ingestion | Violates modular-monolith decision |

## Consequences

- **Positive:** working discovery loop on auth foundation; pluggable sources; path open to Profile ACL and LLM Match Intelligence.
- **Tradeoffs:** SeekerCriteria is temporary; rematch strategy is simple (full rescore of active opportunities); board tokens are config-managed.
- **Follow-ups:** Profile ACL replaces SeekerCriteria; LLM MatchScorer adapter; more sources; freshness/stale sweeps; legal register per source.

## Compliance

- [x] Consistent with locked architecture (ports, contexts, async AI, permitted sources)
- [x] Engineering Constitution reviewed (no LLM on request path; no cross-context table access)
- [x] Security/DPDP: seeker criteria RLS by user; provenance required on opportunities
- [x] Cost/observability: deterministic scoring default; ingest behind scheduler/worker
