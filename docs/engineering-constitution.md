# CareerOS — Engineering Constitution

> **Status:** Highest-priority document in the repository.
> **Authority:** Supersedes personal preference and habit. It does **not** supersede the five locked architecture documents (Vision, System Architecture, Domain Model, AI Architecture, Technical Architecture) — it operationalizes them.
> **Amendment rule:** Any deviation from this constitution or the locked documents **requires an Architecture Decision Record (ADR)** in `docs/adr/`, reviewed and merged before the deviating code. No ADR, no deviation.
> **Audience:** Every human and AI contributor. If you are an AI coding agent, you must read and obey this document before writing code in this repository.

---

## How to read this document

- **MUST / MUST NOT** = hard rule. Violation blocks merge.
- **SHOULD / SHOULD NOT** = strong default. Deviation requires justification in the PR description.
- **MAY** = permitted option.
- When this document and reality conflict, **stop and raise an ADR** — do not silently drift.

---

## 1. Engineering Principles

1. **Production-first, not demo-first.** Every change is written as if it ships to real users handling real PII. No throwaway shortcuts in `main`.
2. **Correctness > cleverness.** Boring, obvious, testable code beats clever code. Optimize for the next reader.
3. **Small, reversible steps.** Prefer incremental, independently shippable changes over big-bang rewrites.
4. **Own the outcome, not just the code.** "It compiles" is not done. See Definition of Done (§25).
5. **Cost is a feature.** LLM spend, DB load, and infra cost are first-class design concerns, not afterthoughts.
6. **Security and privacy are existential.** We handle sensitive personal data of Indian data principals under DPDP. Treat every decision through that lens.
7. **Decisions are written down.** Significant "why" lives in ADRs, not in someone's head or a Slack thread.
8. **The human stays in control.** Nothing that represents a user or leaves the platform happens without explicit human approval.
9. **Measure before optimizing.** No performance work without evidence from observability.
10. **Leave it better.** Boy-scout rule, scoped: improve what you touch without unrelated churn.

---

## 2. Architecture Principles

1. **Modular monolith by default.** We do not introduce new deployable services without an ADR proving the need. The async worker tier is the one pre-approved split.
2. **Bounded contexts are the unit of modularity.** Code is organized by domain context, not by technical layer at the top level.
3. **Dependencies point inward.** `domain` depends on nothing; `application` depends on `domain`; `infrastructure` implements `ports`. Framework/vendor code lives only in `infrastructure`/adapters.
4. **Everything external is behind a Port.** LLMs, vector store, auth, storage, queue, event bus, opportunity sources, and all repositories are interfaces with swappable adapters.
5. **Cross-context communication is via domain events or published contracts only.** No context reads another context's tables or internal models.
6. **State lives outside compute.** API and worker processes are stateless; all state is in Postgres, object storage, vector store, or the queue.
7. **Deterministic-first AI.** Autonomy is used only where the task genuinely requires open-ended reasoning. Prefer deterministic graphs with LLM steps over autonomous agents.
8. **Design for scale, build for now.** Keep the scaling path open (ports, stateless compute, events) but do not build distributed-systems complexity the MVP does not need.
9. **Every module independently replaceable.** If swapping an adapter or context requires touching unrelated code, the boundary is wrong.
10. **The Human-Review context and the "no external-write tools" rule are the safety kernel.** They are protected; changes to them require heightened review.

---

## 3. Coding Principles

1. **SOLID applies everywhere**, especially SRP (one reason to change) and DIP (depend on abstractions).
2. **Pure domain.** Domain code MUST be free of framework, I/O, network, and vendor SDK imports.
3. **Explicit over implicit.** No hidden globals, no magic. Dependencies are injected, not reached for.
4. **Immutability by default.** Value Objects are immutable. Prefer immutable data; mutate only where ownership is clear.
5. **Fail fast, fail loud.** Validate at boundaries; raise typed errors; never swallow exceptions silently.
6. **No premature abstraction.** Abstract on the second real use case, not the first imagined one — except for the mandated Ports.
7. **Functions do one thing.** If you cannot name it without "and", split it.
8. **No dead code, no commented-out code** in `main`. Delete it; git remembers.
9. **Comments explain WHY, never WHAT.** No narration comments. If code needs a "what" comment, rename/refactor instead.
10. **Typed everything.** Full type coverage on both sides (Python type hints + TypeScript strict). No `any`, no untyped dicts crossing boundaries.

---

## 4. DDD Rules

1. **Ubiquitous Language is law.** Use the exact terms from the Domain Model (Candidate, Opportunity, Match, Recommendation, PreparationArtifact, ReviewTask, Application, AgentRun, etc.). Never reintroduce banned synonyms — e.g., "Job" for Opportunity, "Recommendation" for a raw Match.
2. **One aggregate = one transaction.** A single transaction MUST modify only one aggregate instance. Cross-aggregate consistency is eventual, via domain events.
3. **Aggregates stay small.** No god-aggregates. Reference other aggregates by ID, never by embedding.
4. **Repositories are per aggregate root**, and only persist/retrieve that aggregate. No cross-aggregate joins in repositories — use dedicated read models.
5. **Value Objects are immutable and identity-free.** If it has a lifecycle or identity, it is an Entity; otherwise it is a VO.
6. **Domain events are past-tense facts, versioned, and the only cross-context coupling.**
7. **No domain logic outside the domain.** Application services orchestrate; they do not contain business rules. UI and controllers contain none.
8. **Anti-Corruption Layer for all external data.** Parsed documents, external opportunities, and provider payloads are translated at the boundary; their shapes never leak inward.
9. **Skill Taxonomy is authoritative.** Skills are referenced by canonical ID, never free-text, across contexts.
10. **Invariants live in the aggregate.** Business rules are enforced inside the aggregate, not in services or the UI.

---

## 5. AI Agent Rules

1. **Classify before building.** Every new AI unit is explicitly a Deterministic Component, an LLM Step, or a true Agent. Default to the least autonomous option that works; justify any escalation.
2. **Structured I/O only.** Every agent/LLM step has a typed input and a schema-validated output. No free-text crossing a boundary that code must parse.
3. **Grounding is mandatory.** Generative outputs (tailoring, cover letters, matches) MUST be grounded in source data. Tailoring/prep MUST NOT assert skills or experience absent from the source Profile version. Zero fabrication is a hard gate.
4. **No external-write tools exist.** There is no tool to submit applications or message third parties. Email/calendar tools are user-facing only (digests/reminders) and are `external` class — gated by consent and, where representational, by human approval.
5. **Human-in-the-loop is structural.** Any externally-bound or user-representational artifact MUST pass through a `ReviewTask` and an `ArtifactApproved`/`EditedAndApproved` decision before it can leave the platform. Agents cannot route around this.
6. **The Supervisor holds no domain or external-write tools.** It orchestrates subgraphs only.
7. **Typed, namespaced, reference-based state.** Pass IDs and summaries, not payloads. Never dump full documents, transcripts, or embeddings into agent context.
8. **Bounded loops.** Self-critique iterations, plan depth, and retries are capped. No unbounded agent loops.
9. **Checkpoint and trace everything.** Every Agent Run is checkpointed, cost-tracked, and traced (LangSmith + `AgentRun` record) under one `traceId`.
10. **Ingested/untrusted text can never escalate tool permissions or write long-term memory.** This is the prompt-injection backstop.
11. **Every agent is independently evaluable** with defined metrics; changes are gated by the eval harness (§ Testing).
12. **Memory is consent-scoped and decaying.** Only consented data becomes long-term memory; contradictions are reconciled, not blindly appended.

---

## 6. Database Rules

1. **Postgres is the system of record.** pgvector for embeddings in MVP; Qdrant only when metrics justify, and always behind the `VectorStore` port.
2. **No raw SQL outside the infrastructure layer.** Queries live in repository/adapter implementations, never in controllers, services, or the domain.
3. **Row-Level Security is mandatory.** Every user-owned row is scoped by user (and tenant when activated) at the DB, independent of app-layer authz.
4. **Migrations are versioned, reviewed, and forward-compatible.** Use expand/contract; never a destructive migration without a documented, reversible plan.
5. **Files never live in the database.** Object storage holds files; the DB holds metadata and references.
6. **No cross-context foreign keys that couple contexts.** Reference other contexts by ID; enforce integrity at the domain/event level, not via cross-context FK webs.
7. **Immutable/append-only where the domain says so** (ResumeVersion, ReviewTask decisions, audit logs, AgentRun checkpoints).
8. **Indexes and access patterns are designed, not accidental.** New high-cardinality query paths require an index rationale in the PR.
9. **PII is classified.** Most sensitive fields (e.g., salary) use field-level encryption. Retention and erasure paths (DPDP) are implemented, not deferred.
10. **Read models are separate from aggregates.** Do not load aggregates to render lists.

---

## 7. API Design Standards

1. **Contract-first.** The API is the source of truth for types; `packages/contracts` is generated from it. No hand-maintained duplicate types.
2. **Consistent resource semantics.** Predictable, resource-oriented endpoints; correct HTTP status codes; no verbs-in-paths sprawl.
3. **Validated at the boundary.** Every request and response is schema-validated. Reject malformed input with structured problem-details errors.
4. **Versioned and backward-compatible.** Breaking changes require a new version and a migration note. Never break an existing contract silently.
5. **Stable, typed error format.** Errors use a consistent problem-details shape; never leak stack traces or internal identifiers.
6. **Idempotency for unsafe operations.** Mutations that may be retried use idempotency keys.
7. **Authorized on every request.** No endpoint trusts the client for identity or scope.
8. **Pagination, filtering, and limits by default** on collection endpoints. No unbounded result sets.
9. **No business logic in routers/controllers.** Routers translate HTTP ↔ application use cases only.
10. **Long-running work is async.** Endpoints enqueue and return a handle; they never block on AI/agent execution.

---

## 8. Frontend Standards

1. **Server Components by default; Client Components by exception** (only where interactivity requires it).
2. **Feature-based structure.** Code is organized under `features/` mirroring backend contexts, not by technical type at the top level.
3. **No business logic in the UI.** Components render and orchestrate calls; rules live in the backend.
4. **No LLM calls, secrets, or service tokens in the browser.** All privileged calls go through the BFF (server layer).
5. **Server state via TanStack Query; server mutations via Server Actions.** No global client store unless justified; URL holds filter/view state.
6. **Shared, validated schemas.** Forms use React Hook Form + Zod schemas sourced from `contracts`. No duplicated, drifting validation.
7. **Accessibility is required.** Semantic HTML, keyboard navigation, Radix a11y primitives, WCAG-conscious. i18n-ready structure.
8. **Presentational components come from `packages/ui`.** No one-off reimplementations of shared primitives.
9. **Explicit loading, empty, and error states** for every async surface — especially AI-latency surfaces (stream/progress).
10. **No direct fetch calls.** Use the typed `sdk`.

---

## 9. Backend Standards

1. **Five-layer context structure:** `api / application / domain / ports / infrastructure`. Respect the dependency direction (§2.3).
2. **Dependency Injection everywhere.** No module-level singletons reached for implicitly; wire dependencies at the edge.
3. **Application services orchestrate use cases** (load aggregate → invoke domain → persist → emit event) and contain no business rules.
4. **Ports for all external dependencies.** Vendor SDKs appear only in adapters.
5. **Typed configuration**, loaded per environment, fail-fast on missing values. No literals or magic numbers in code.
6. **Domain events are emitted for state changes** that other contexts may care about. Do not silently mutate and move on.
7. **Background/long-running work runs in the worker tier**, not in request handlers.
8. **Errors are typed and mapped** from domain → application → transport. No leaking internals.
9. **Idempotent, retry-safe workers** with dead-letter handling for poison messages.
10. **No cross-context imports of internal models.** Communicate via events or published contracts.

---

## 10. Testing Standards

1. **The testing pyramid holds.** Many fast unit tests (pure domain), fewer integration tests (adapters/repositories against real infra), few end-to-end tests for critical flows.
2. **Domain logic MUST be unit-tested** without any I/O, using fakes for ports.
3. **Every bug fix ships with a regression test.**
4. **AI outputs are evaluated, not asserted verbatim.** Use the eval harness (golden datasets + judges + heuristics) for agent/LLM quality. Prompt/agent/model changes MUST pass the eval gate in CI.
5. **Resume truthfulness / zero-fabrication is a hard eval gate.** No exceptions.
6. **Contract tests** guard the API ↔ frontend boundary and event schemas.
7. **Tests are deterministic and isolated.** No reliance on network, wall-clock, or ordering. LLM calls are mocked/recorded in unit/integration tests.
8. **Critical flows have E2E coverage:** signup → profile → match → prep → human approval.
9. **No merging with failing or skipped tests** (skips require an ADR or tracked issue).
10. **Coverage is a signal, not a target.** Meaningful assertions over coverage percentage — but critical paths MUST be covered.

---

## 11. Security Standards

1. **OWASP Top 10 is baseline.** Input validation, output encoding, authz on every request, secure headers/CSP, dependency scanning.
2. **Authorize on every request, at two layers** (application + RLS). Never trust the client.
3. **Secrets only in platform secret stores**, per environment, rotation-ready. Never in code, config files, logs, or the client bundle.
4. **All uploads are untrusted:** type/size validation, content sniffing, malware scanning, isolated parsing, quarantine on hit.
5. **Treat all ingested text as hostile** (prompt-injection defense). Whitelisted tools; ingested content cannot escalate permissions or write long-term memory.
6. **Encryption in transit (TLS) and at rest**; field-level encryption for the most sensitive PII.
7. **Rate limiting and cost caps** on auth and AI endpoints.
8. **Immutable audit logs** for approvals, auth events, admin actions, and tool invocations.
9. **PII minimization to LLMs**; prefer providers with no-training-on-data terms; redact PII in logs and traces.
10. **DPDP rights are implemented features:** consent capture, purpose limitation, export, and erasure (with anonymized audit retention).

---

## 12. Performance Standards

1. **Interactive endpoints target p95 < 500ms server time.** AI generation is async with progress feedback, never blocking.
2. **No N+1 queries.** Batch and paginate. Collection endpoints are always bounded.
3. **Cache deliberately:** exact + semantic caches for repetitive LLM tasks; Next.js/TanStack caching with explicit invalidation on mutation.
4. **Context size is monitored.** Reference-passing and top-K retrieval keep agent context bounded; context growth is an alertable metric.
5. **Parallelize independent work** (map-reduce fan-out) instead of serial loops.
6. **Right-size models** per task via the routing table; premium models only for the two core generative tasks unless justified.
7. **Measure before optimizing.** Use tracing/metrics evidence; no speculative optimization.
8. **Backpressure on ingestion.** The highest-volume pipeline must be incremental, idempotent, and rate-aware.
9. **Budgets enforced.** Per-run and per-candidate cost/usage caps abort runaway work.
10. **Load-relevant changes state their performance impact** in the PR.

---

## 13. Observability Standards

1. **One `traceId` end-to-end** across web → api → worker → agents, correlated to `AgentRun` and domain events.
2. **Structured JSON logs** with correlation id on every line; PII-redacted.
3. **Every Agent Run is traced** (LangSmith nested spans) and cost-tracked (per run, agent, candidate, model).
4. **RED metrics for HTTP; queue depth/lag for async; AI success/HITL/guardrail/eval-score metrics.**
5. **Health checks** (liveness/readiness + dependency checks) for api and worker.
6. **Alerting** on error rate, p99 latency, queue lag, cost anomalies, and eval-score regressions.
7. **Errors reported** to the error-tracking system with release + trace context.
8. **No silent failures.** A failure that is not logged, traced, and (if material) alerted does not exist — and that is the danger.
9. **Failed runs preserve state** for replay and debugging.
10. **Dashboards exist before scale**, not after the incident.

---

## 14. Documentation Standards

1. **ADRs for every significant or deviating decision.** `docs/adr/` uses a consistent template (context, decision, alternatives, consequences).
2. **The locked five documents are canonical.** Code must conform; conflicts are resolved by ADR, not by ad-hoc code.
3. **Public contracts are documented** (API, events, agent I/O schemas) and versioned.
4. **READMEs explain how to run and reason about a module**, not what each line does.
5. **Ubiquitous Language is documented and kept current** with the Domain Model.
6. **Runbooks** exist for on-call concerns (backups/restore, incident response, cost spikes).
7. **Docs live in the repo** and are updated in the same PR as the change they describe.
8. **No stale docs.** If a change invalidates a doc, updating it is part of Definition of Done.
9. **Diagrams use Mermaid** in-repo (versionable), not binary images where avoidable.
10. **Assumptions and open questions are recorded**, not left implicit.

---

## 15. Git Standards

1. **Trunk-based-ish with short-lived branches.** Branch from `main`, merge back fast.
2. **Branch naming:** `type/short-description` (e.g., `feat/match-explanations`, `fix/resume-parse-dates`).
3. **Conventional Commits** (`feat:`, `fix:`, `chore:`, `refactor:`, `docs:`, `test:`, `perf:`, `sec:`). Imperative mood.
4. **Small, atomic commits** that each leave the tree working.
5. **No secrets, generated artifacts, or large binaries** committed. Respect `.gitignore`.
6. **Rebase to keep history clean** before merge; no merge-commit noise from long divergence.
7. **`main` is always releasable.** Never push broken code to `main`.
8. **Signed/verified commits** where the platform supports it.
9. **One logical change per PR.** Do not bundle unrelated refactors with features.
10. **Reference the issue/ADR** in the commit/PR when applicable.

---

## 16. Pull Request Standards

1. **PRs are small and reviewable** (prefer < ~400 lines of meaningful diff). Large PRs require justification.
2. **Description explains WHAT and WHY**, links issues/ADRs, and notes tradeoffs.
3. **All CI gates green:** lint, typecheck, tests, eval gate, security scan.
4. **At least one reviewer approval** (two for safety-kernel, auth, security, or migration changes).
5. **Self-review first.** The author walks the diff before requesting review.
6. **Screenshots/notes for UI changes**; migration plan for DB changes.
7. **No new lint/type suppressions** without inline justification.
8. **Constitution compliance is a review criterion** (see §24).
9. **Draft PRs for early feedback** are encouraged; ready-for-review means DoD-met.
10. **The author merges after approval**, and is responsible for post-merge health.

---

## 17. Naming Conventions

1. **Names come from the Ubiquitous Language.** No inventing synonyms for domain concepts.
2. **Python:** `snake_case` for functions/variables/modules, `PascalCase` for classes, `UPPER_SNAKE` for constants.
3. **TypeScript:** `camelCase` for variables/functions, `PascalCase` for components/types, `UPPER_SNAKE` for constants.
4. **Files:** kebab-case for TS/React files; snake_case for Python files. Test files clearly suffixed.
5. **Booleans read as predicates** (`is_`, `has_`, `can_`).
6. **No abbreviations** except well-known ones (id, url, db). No single-letter names outside tiny local scopes.
7. **Ports are named by capability** (`LLMProvider`, `VectorStore`, `OpportunitySource`); adapters name the vendor (`GeminiLLMProvider`).
8. **Events are past-tense** (`ResumeParsed`, `ArtifactApproved`).
9. **Aggregates, entities, VOs, repositories, and services** are named exactly as in the Domain Model.
10. **No misleading names.** A name that lies is worse than no name.

---

## 18. Folder Structure Rules

1. **Top-level layout is fixed** by the Technical Architecture (`apps/`, `packages/`, `shared/`, `agents/`, `contexts/`, `evals/`, `infra/`, `docs/`). Adding a top-level directory requires an ADR.
2. **Each context follows the five-layer shape** (`domain/ application/ ports/ infrastructure/ api/`).
3. **Frontend follows feature-based structure** under `features/`.
4. **The AI engine lives in `agents/`**, wrapped by the `ai_orchestration` context — not scattered.
5. **Shared code lives in the designated shared packages**, not copy-pasted across apps.
6. **Tests live beside or in the mandated test locations**, never mixed into production modules ambiguously.
7. **No business logic in `apps/*/api` routers or Next.js route handlers.**
8. **Prompts live in the versioned prompt registry** (`agents/prompts/`), never inline.
9. **Migrations live in `infra/migrations/`.**
10. **If you cannot find where something belongs, it is a design smell — ask, do not dump it in a catch-all.**

---

## 19. Error Handling Standards

1. **Typed domain errors** originate in the domain; application maps to results/exceptions; transport maps to problem-details.
2. **Never swallow exceptions.** Catch only to add context or translate, then rethrow or handle deliberately.
3. **No leaking internals** (stack traces, SQL, provider messages, identifiers) to clients.
4. **Fail fast at boundaries;** validate inputs before doing work.
5. **Distinguish expected vs. unexpected failures.** Expected (validation, not-found) → clean responses; unexpected → logged, traced, alerted.
6. **External calls are wrapped** with timeouts, retries (where idempotent), and fallbacks.
7. **AI failures are classified** (transient/tool/model/validation/policy) and recovered per the AI Architecture, preserving run state.
8. **No catch-all `except`/`catch` that hides bugs.**
9. **Errors carry correlation/trace context.**
10. **User-facing error messages are safe, clear, and actionable** — never raw internals.

---

## 20. Logging Standards

1. **Structured JSON only.** No unstructured `print`/`console.log` in production paths.
2. **Correlation/trace id on every log line.**
3. **Never log secrets or PII.** Redact by default; sensitive fields are masked.
4. **Log at the right level:** `debug` (dev detail), `info` (state transitions/events), `warn` (recoverable anomalies), `error` (failures needing attention).
5. **Log decisions and state transitions**, not noise. Avoid log spam.
6. **No logging as flow control** and no logging instead of proper error handling.
7. **Agent tool invocations and approvals are logged** to the audit trail.
8. **Logs are centralized** and queryable.
9. **One event, one log** — avoid duplicate logging of the same failure at multiple layers.
10. **Do not use logs to communicate with users** — that is the UI's job.

---

## 21. Prompt Engineering Standards

1. **No hardcoded prompts in code.** All prompts live in the versioned prompt registry (`agents/prompts/`), referenced by id + version.
2. **Prompts are versioned;** changes go through the eval gate before shipping.
3. **Every prompt demands structured output** with an explicit schema.
4. **Grounding is instructed and enforced:** prompts require citing source evidence; downstream verification checks it. Generation cannot invent unevidenced facts.
5. **System, developer, and user content are clearly separated;** untrusted/ingested content is never placed where it can act as instructions.
6. **Prompts are minimal and reference-based** — pass IDs/summaries, not full payloads, to control tokens.
7. **Few-shot exemplars live in procedural memory / registry**, not inlined ad hoc.
8. **Prompts are model-agnostic where possible**, with provider-specific variants isolated behind the provider abstraction.
9. **Every prompt has associated eval cases** (golden examples + failure cases).
10. **No prompt ships without a defined failure mode and guardrail.**

---

## 22. LLM Usage Standards

1. **All LLM access is behind the `LLMProvider` port.** No direct vendor SDK calls outside adapters.
2. **No hardcoded model names.** Models are selected via the routing configuration (§23).
3. **Structured, validated outputs only.** Reject/repair invalid outputs; never trust raw text downstream.
4. **Bounded cost and loops.** Enforce per-run/per-candidate budgets and capped iterations.
5. **Cache aggressively** (exact + semantic + provider prompt caching) for repetitive tasks.
6. **Minimize PII sent to providers;** prefer no-training-data terms; redact traces.
7. **Every LLM call is traced and cost-tracked.**
8. **Retries with backoff + provider fallback** on transient/rate-limit/outage errors.
9. **No LLM call on the request path** for anything non-trivial — enqueue to the worker.
10. **No LLM calls inside React components or controllers.** Ever.

---

## 23. Model Routing Standards

1. **Routing is declarative config** (task → model tier), hot-swappable without code changes.
2. **Right-size by task value.** Cheap/fast models for extraction/normalization/routing; premium models only for the two core generative tasks (tailoring/cover letter) or hard judgments.
3. **Fallback chains are defined** per task (primary → secondary provider/model).
4. **Judges differ from generators.** Evaluation models are distinct from the models being evaluated.
5. **Routing changes are observable** — cost/quality impact is tracked after any change.
6. **Determinism first.** Routing should route ~most decisions to deterministic rules, escalating to LLMs only when needed.
7. **Model changes pass the eval gate** before rollout.
8. **Budgets are enforced at the routing layer** (abort/downgrade on threshold).
9. **No provider lock-in.** Adding/removing a provider is an adapter + config change.
10. **Document the routing table** and keep it current.

---

## 24. Code Review Checklist

Reviewers MUST verify:

- [ ] **Constitution & locked docs respected**; deviations have an ADR.
- [ ] **Correct layer/context;** dependency direction intact; no framework leakage into domain.
- [ ] **No business logic in UI, routers, or controllers.**
- [ ] **No direct SQL, LLM calls, or vendor SDKs outside infrastructure/adapters.**
- [ ] **No hardcoded prompts, model names, secrets, or magic values.**
- [ ] **Aggregate/transaction boundaries respected;** cross-context via events only.
- [ ] **Inputs validated;** typed errors; safe error responses.
- [ ] **AuthZ enforced;** RLS/user scoping intact; PII handled per policy.
- [ ] **Structured I/O, grounding, and HITL** honored for AI changes; eval gate passed.
- [ ] **Tests present and meaningful;** regression test for bug fixes.
- [ ] **Observability:** logging/tracing/metrics adequate; no PII in logs.
- [ ] **Performance:** no N+1, bounded queries, async for slow work, context size sane.
- [ ] **Naming from Ubiquitous Language;** no god classes; no circular deps.
- [ ] **Docs/ADRs updated;** PR explains WHAT and WHY.
- [ ] **Nothing from §26 present.**

---

## 25. Definition of Done

A change is **Done** only when ALL are true:

1. Meets the requirement and conforms to the locked docs + this constitution.
2. Correct context/layer; ports respected; no drift.
3. Typed end-to-end; validation at boundaries.
4. Tests written and passing (unit/integration/E2E as appropriate); AI eval gate passed.
5. Security reviewed: authz, PII, secrets, injection, uploads.
6. Observability in place: logs, traces, metrics, and cost tracking for AI.
7. Errors handled and mapped safely.
8. Performance acceptable; no obvious N+1 or unbounded work.
9. Docs/ADRs/contracts updated in the same PR.
10. CI fully green; PR reviewed and approved (two for safety-critical).
11. Feature-flagged if risky; rollback path exists.
12. No item from §26 introduced.

---

## 26. Things NEVER Allowed

These are hard stops. Introducing any of these blocks merge and, if merged, must be reverted.

1. **Business logic inside UI / components.**
2. **LLM calls inside React components or controllers.**
3. **Direct SQL inside controllers, services, or the domain.**
4. **Skipping input or domain validation.**
5. **Ignoring / not emitting domain events** for cross-context state changes.
6. **Framework or vendor-SDK leakage into the domain layer.**
7. **Circular dependencies** between modules/contexts.
8. **Hardcoded prompts.**
9. **Hardcoded model names.**
10. **Vendor lock-in** — bypassing a Port to call a vendor directly outside adapters.
11. **Secrets in code, config files, logs, or the client bundle.**
12. **Large "God" classes/functions/aggregates** with many responsibilities.
13. **A tool that submits applications or messages third parties**, or any external-write action, without an ADR *and* legal sign-off *and* mandatory HITL.
14. **Any externally-bound or user-representational AI artifact leaving the platform without human approval.**
15. **Fabricated resume/profile content** — asserting skills/experience not in the source Profile version.
16. **Ingested/untrusted text escalating tool permissions or writing long-term memory.**
17. **PII sent to logs, traces, or LLM providers beyond the minimum necessary.**
18. **Cross-context access to another context's tables or internal models.**
19. **Blocking the request path on LLM/agent execution.**
20. **Modifying the safety kernel (Human-Review, no-external-write) without heightened review and an ADR.**
21. **Unbounded loops, queries, result sets, or agent iterations.**
22. **Merging with failing/skipped tests or a failing eval gate.**
23. **Committing generated artifacts, large binaries, or dead/commented-out code to `main`.**
24. **Deviating from the locked architecture documents without an ADR.**

---

> **Final word:** This constitution exists to prevent architecture drift across many contributors and many AI coding sessions. When in doubt, choose the option that keeps the domain pure, the human in control, PII protected, cost bounded, and the decision written down. If none of the rules cover your case, **stop and open an ADR** — do not improvise your way into drift.
