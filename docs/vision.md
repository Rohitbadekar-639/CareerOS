# CareerOS — Vision & Product Definition

> **Status:** LOCKED (see `docs/adr/0000-lock-architecture-documents.md`). Source of truth. Changes require an ADR.
> **Scope of this document:** product vision, scope, non-goals, functional & non-functional requirements, and the product roadmap. System/AI/technical design live in their dedicated locked documents.

## Critical framing (non-negotiable)

Three constraints frame everything CareerOS builds:

1. **Automated submission and automated communication on third-party platforms (LinkedIn, Naukri, Instahyre, company ATSs) is a legal and ToS minefield.** CareerOS forces human-in-the-loop before any external submission or communication. We build an *assistant and cockpit*, not an *auto-applier bot*.
2. **DPDP Act 2023 (India) applies from day one.** We process sensitive personal data (resumes = PII, salary, location, employment history) of Indian data principals. This is not a "later" problem.
3. **Multi-tenancy is treated as per-user isolation for the B2C MVP.** True B2B tenancy is reserved (schema-forward-compatible) but not built until a B2B deal justifies it.

## 1. Vision Statement

**CareerOS is the AI career operating system that runs quietly in the background of a job seeker's life — continuously understanding who they are, watching the market for genuinely relevant opportunities, and preparing them to win — while always keeping the human in the driver's seat for anything that leaves the platform.**

The unit of value is not "a resume" or "a job listing." It is **compounding career context**: a durable, structured, ever-improving model of the user that makes every subsequent action (tailoring, matching, prep, negotiation) cheaper and better over time. That accumulated context is the moat.

**Why this framing:** If the vision is "auto-apply to 500 jobs," we build a spam engine that platforms ban and users distrust. If the vision is "an AI that makes me a stronger, better-targeted candidate and removes the grunt work," we build a durable, defensible, monetizable product. This distinction determines the entire architecture — especially the human-in-the-loop boundary.

## 2. Product Scope

### In scope for MVP (Phase 1 — Software/IT roles, India)
- **Identity & Profile:** Auth, professional profile, structured career preferences (roles, salary, locations, work mode, notice period, tech stack, exclusions, target companies).
- **Document ingestion:** Resume, cover letter, certifications, portfolio links, GitHub, LinkedIn (via user-provided data / OAuth-permitted APIs / manual upload — NOT scraping).
- **Profile intelligence:** Parse and normalize uploaded documents into a canonical structured Candidate Profile; extract a skills graph.
- **Opportunity discovery:** Ingest opportunities from *legally permissible sources* (official/partner APIs, aggregator APIs with terms, public/official career feeds, or user-forwarded listings). Rank and prioritize by fit.
- **Fit & gap analysis:** Explainable match scoring between profile and opportunity; skill-gap identification.
- **AI-assisted tailoring:** Generate tailored resume/cover-letter *drafts* per opportunity. Draft only — nothing is sent.
- **Human review cockpit:** Every AI output that would leave the platform passes an explicit human approval gate.
- **Application tracking:** A personal tracker of opportunities and their status.
- **Observability & evaluation:** Full tracing of agent runs, cost tracking, and an offline eval harness.

### Explicitly deferred (Phase 2+)
- Auto-submission of any kind (revisit only with legal sign-off and official partner integrations).
- Interview simulation / mock interviews, negotiation coaching.
- Recruiter-side / B2B marketplace.
- Non-IT verticals and non-India geographies.
- Mobile apps (architecture must *support* them; we don't *build* them in MVP).

**Why scope it tightly:** the MVP must prove one loop — *"CareerOS understood me, surfaced something relevant I'd have missed, and made me materially better prepared for it"* — with real users, cheaply, without legal exposure.

## 3. Non-Goals

- **Not a job board.** We are an intelligence layer, not the canonical listings inventory.
- **Not a scraper of protected platforms.** No LinkedIn/Naukri scraping or automation in the core product.
- **Not an auto-applier / auto-messenger** in MVP. No unattended external communication.
- **Not a guaranteed-outcome service.** We never promise jobs; we improve odds and reduce effort.
- **Not a general-purpose chatbot.** Agents are scoped to career tasks with typed I/O.
- **Not multi-cloud / Kubernetes / microservice-swarm from day one.**
- **Not building our own foundation models.** We orchestrate commodity LLMs.

## 4. Functional Requirements

`[MVP]` = Phase 1, `[P2]` = later.

**FR-1 Accounts & Auth**
- FR-1.1 Email/OAuth sign-up & login (Supabase Auth). `[MVP]`
- FR-1.2 Session management, password reset, email verification. `[MVP]`
- FR-1.3 Account deletion + full data export (DPDP erasure & portability). `[MVP — legally required]`

**FR-2 Profile & Preferences**
- FR-2.1 Create/edit structured profile. `[MVP]`
- FR-2.2 Configure preferences: roles, seniority, salary range (with "confidential" option), locations (incl. Remote), work mode, notice period, tech inclusions/exclusions, target & excluded companies. `[MVP]`
- FR-2.3 Multiple named "search profiles". `[P2 — design schema now]`

**FR-3 Document & Link Ingestion**
- FR-3.1 Upload resume/cover letter/certs (PDF, DOCX). `[MVP]`
- FR-3.2 Add GitHub, portfolio, LinkedIn URLs. `[MVP]`
- FR-3.3 GitHub enrichment via official API. `[MVP]`
- FR-3.4 LinkedIn: import via user-initiated official export or OAuth-permitted fields only. `[MVP — constrained]`
- FR-3.5 Virus/malware scan + file-type/size validation on all uploads. `[MVP — security]`

**FR-4 Profile Intelligence**
- FR-4.1 Parse documents → canonical structured Candidate Profile. `[MVP]`
- FR-4.2 Extract skills, seniority, domains; build embeddings. `[MVP]`
- FR-4.3 Detect inconsistencies/gaps. `[P2]`

**FR-5 Opportunity Discovery & Ranking**
- FR-5.1 Ingest opportunities from permitted sources into a normalized model. `[MVP]`
- FR-5.2 Deduplicate opportunities across sources. `[MVP]`
- FR-5.3 Rank by explainable fit score. `[MVP]`
- FR-5.4 Apply hard filters (exclusions, location, work mode). `[MVP]`
- FR-5.5 Continuous background refresh + change detection. `[MVP]`

**FR-6 Fit, Gap & Preparation**
- FR-6.1 Per-opportunity match report with reasons for/against. `[MVP]`
- FR-6.2 Skill-gap list + suggested prep. `[MVP]`
- FR-6.3 Tailored resume/cover-letter draft generation. `[MVP]`

**FR-7 Human Review & Actioning**
- FR-7.1 Approval queue: every externally-bound artifact requires explicit approval/edit. `[MVP]`
- FR-7.2 Inline edit of AI drafts before approving. `[MVP]`
- FR-7.3 On approval: download / copy / guided "apply on source" hand-off. No unattended submission. `[MVP]`

**FR-8 Tracking & Notifications**
- FR-8.1 Opportunity pipeline tracker with statuses. `[MVP]`
- FR-8.2 Digest notifications (email) of new high-fit opportunities. `[MVP]`
- FR-8.3 In-app notification center. `[MVP]`

**FR-9 AI Ops (internal)**
- FR-9.1 Full run tracing (LangSmith), per-user cost accounting, rate limiting. `[MVP]`
- FR-9.2 Offline eval harness on a golden dataset. `[MVP]`
- FR-9.3 Feedback capture (thumbs/edits) feeding evaluation. `[MVP]`

## 5. Non-Functional Requirements

| # | Category | Requirement | Why |
|---|---|---|---|
| NFR-1 | Privacy/Legal | DPDP-compliant: consent, purpose limitation, erasure, export, India data-residency preference. | Sensitive PII. |
| NFR-2 | Security | Encryption in transit & at rest; RLS/row-scoping; least-privilege creds; secrets in a vault. | Handling resumes/PII. |
| NFR-3 | AI Safety | No irreversible external action without human approval; all agent actions logged/reversible. | Product promise + liability. |
| NFR-4 | Cost | Per-user LLM cost tracked and capped; cheap models by default. | Free-tier constraint; unit economics. |
| NFR-5 | Performance | Interactive actions p95 < 500ms server time. AI generations async with progress. | LLM latency is unavoidable. |
| NFR-6 | Availability | 99% MVP target (single-region). | Right-sized for stage. |
| NFR-7 | Observability | Structured logs, tracing, LLM tracing, error alerting from day one. | Can't operate unseen agents. |
| NFR-8 | Agent reliability | Retries w/ backoff, timeouts, graceful degradation, checkpointed resumable workflows. | LLM/tool calls fail routinely. |
| NFR-9 | Maintainability | Clean Architecture + DDD + Ports/Adapters. | Independently replaceable modules. |
| NFR-10 | Portability | No hard lock-in to one LLM vendor. | Model market moves fast. |
| NFR-11 | Scalability path | Stateless API, externalized state, queue-based async. | Scale later without rewrite. |
| NFR-12 | Accessibility/i18n | WCAG-conscious UI; i18n-ready. | India multilingual future. |

## 6. Future Expansion Roadmap (product)

- **Phase 0 — Foundations (pre-launch):** repo scaffolding, auth, profile+preferences, document upload+parse, security/DPDP baseline, observability + eval harness.
- **Phase 1 — Core loop MVP (IT/India):** opportunity ingestion (1–2 permitted sources), explainable matching, gap analysis, AI tailoring drafts, human-review cockpit, tracker, email digests.
- **Phase 2 — Depth & retention:** interview simulation, negotiation coach, multi search-profiles, richer personalization, more sources, in-app coaching.
- **Phase 3 — Reach:** mobile app (React Native, reusing shared UI + contracts), more IT sub-domains, broader Indian geos, richer integrations.
- **Phase 4 — Platform & B2B:** true multi-tenancy for institutions (colleges, bootcamps, staffing), analytics dashboards, cohort features.
- **Phase 5 — Global & all-careers:** non-IT verticals, additional geographies (each with legal review), localization.

**Guiding principle:** each phase unlocks only after the prior phase's retention/economics thesis is validated.

## Assumptions
1. Next.js "16" = latest stable at implementation time; verify features rather than assume.
2. Opportunity data comes only from legally permissible sources — not scraping protected platforms.
3. CareerOS is B2C at MVP; B2B/institutional is later.
4. Human-in-the-loop is mandatory before any external submission/communication.
5. Object storage and a task queue are required (even though unstated in the original brief).
6. pgvector for MVP, Qdrant later (behind a Port).
7. Redis optional for MVP.
8. India data-residency preference; DPDP applicability assumed.
9. Small founding team → operational simplicity weighted heavily.

## Open Questions
1. Which opportunity-data sources, and have any been legally cleared?
2. Do we have counsel for DPDP + third-party ToS review before launch?
3. Business model (free/freemium/subscription)?
4. Is "assistant + human hand-off, no auto-submit" permanent or a temporary MVP constraint? (Recommendation: permanent for protected platforms.)
5. LinkedIn: user-export/manual import only, or expected API access?
6. Data residency: hard requirement or preference?
7. LLM data terms: acceptable to send minimized PII; which providers meet no-training requirements?
8. Team size and target MVP date?
9. Single MVP success metric (e.g., % surfaced opportunities acted on, or prep-artifact approval rate)?
10. Any near-term B2B intent that would justify real multi-tenancy sooner?
