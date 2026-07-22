# Opportunity Discovery (Job Intelligence MVP — ADR-0001)

Normalized **Opportunity** catalog from permitted public ATS feeds.

| Layer | Contents |
|-------|----------|
| `domain/` | Opportunity aggregate, DedupKey, SourceProvenance |
| `ports/` | `OpportunitySource`, `OpportunityRepository` |
| `application/` | ingest, search, board config parsing |
| `infrastructure/` | Greenhouse + Ashby adapters, Postgres repo |

UI may say “jobs”; domain language remains Opportunity.
