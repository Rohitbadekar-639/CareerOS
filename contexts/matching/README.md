# Matching & Fit (Job Intelligence MVP — ADR-0001)

Explainable ranking of Opportunities for a seeker.

| Layer | Contents |
|-------|----------|
| `domain/` | SeekerCriteria (temporary until Profile), Match, HeuristicMatchScorer |
| `ports/` | criteria/match repositories, MatchScorer |
| `application/` | upsert criteria, recompute, list recommendations |
| `infrastructure/` | Postgres + RLS |

No LLM on the request path. Dashboard reads precomputed surfaced matches.
