# Identity & Access (`contexts/identity`)

Owns **User** and **Consent** (Domain Model). Generic subdomain — auth/privacy
evolve independently of Career Profile.

## Layers

| Layer | Status (M1 Batch 2) |
|---|---|
| `domain/` | Implemented — pure, no I/O |
| `application/` | Scaffold only |
| `ports/` | Scaffold only (no repository ports yet) |
| `infrastructure/` | Scaffold only |
| `api/` | Scaffold only |

Cross-context reactions (e.g. Candidate shell) consume IAM domain events in a
later batch — not via imports of this context's internals.
