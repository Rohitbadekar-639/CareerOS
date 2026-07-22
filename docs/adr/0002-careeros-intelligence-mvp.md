# ADR-0002: CareerOS Intelligence MVP (Profile, Job Hunter, Notifications)

- **Status:** Accepted
- **Date:** 2026-07-22
- **Deciders:** Founding architecture/engineering
- **Related:** ADR-0001, `docs/domain-model.md`, `docs/ai-architecture.md`, `docs/vision.md`

## Context

Auth, Opportunity, Matching, and the seeker workflow (save/apply/tracker/copilot) exist.
The product must become an **AI job-search assistant**: ingest candidate evidence,
unify a profile, improve ranking explanations, and run a Job Hunter loop that discovers,
reranks, notifies, and prepares drafts — without redesigning the modular monolith.

## Decision

1. **Add `contexts/profile` and `contexts/notifications`.** Profile becomes the
   structured candidate source of truth; Matching `SeekerCriteria` is updated via an
   ACL/application sync (ADR-0001 follow-up). No cross-context table reads.

2. **Documents stay lightweight inside Profile for MVP:** resume text + parse results,
   LinkedIn paste/export text, GitHub username, portfolio URL — not a full object-storage
   Document BC yet. Ports (`ResumeParser`, `GitHubAnalyzer`, `PortfolioFetcher`) keep
   adapters swappable.

3. **LinkedIn:** user-provided paste or export text only (Vision: no scraping).
   **GitHub:** public REST API behind a port. **Portfolio:** fetch public HTML/text summary.

4. **Extraction + ranking:** deterministic skill/experience extractors on the sync path;
   Job Hunter / rematch runs in the **worker**. `MatchScorer` remains a port —
   heuristic default; optional LLM adapter later (never on HTTP request path).

5. **Job Hunter Agent** is a **worker orchestration loop** (not a new service):
   ingest opportunities → rematch from Profile-synced criteria → queue strong-match
   notifications → attach resume tips + cover-letter drafts (grounded Copilot) for
   surfaced matches. Daily digest composes in-app notifications.

6. **Notifications:** in-app Notification aggregate (queued→sent/read). Email channel
   is a port stub for MVP.

## Alternatives Considered

| Option | Why not |
|--------|---------|
| Full Documents BC + object storage now | Slows deployable MVP |
| Scrape LinkedIn | Violates Vision / legal source rules |
| LLM on `/v1/recommendations` | Violates Constitution |
| Separate Job Hunter microservice | Violates modular monolith |

## Consequences

- **Positive:** real assistant loop on existing foundation; Profile replaces ad-hoc criteria.
- **Tradeoffs:** parsers are heuristic; email digests stubbed; LLM rerank optional later.
- **Follow-ups:** full Documents BC, LangGraph specialist subgraphs, email provider adapter.

## Compliance

- [x] Locked architecture (ports, contexts, async AI, permitted sources)
- [x] Constitution (no LLM on request path; grounding; no auto-submit)
- [x] DPDP: profile/notification RLS by user; LinkedIn is user-provided only
