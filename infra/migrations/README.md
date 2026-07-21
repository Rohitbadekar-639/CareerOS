# CareerOS application migrations (Alembic)

> **Authority:** Engineering Constitution §18.9 — migrations live in
> `infra/migrations/`. Application schema is versioned here; Supabase CLI owns
> only Auth (see `supabase/`).

## Prerequisites

- `CAREEROS_DATABASE_URL` set (compose Postgres for local: see `.env.example`)
- Dev deps installed: `uv sync --all-packages` (includes Alembic + psycopg)

## Commands (repo root)

```bash
# Apply all revisions
uv run alembic -c infra/migrations/alembic.ini upgrade head

# Show current revision
uv run alembic -c infra/migrations/alembic.ini current

# Create a new empty revision (edit the file under versions/)
uv run alembic -c infra/migrations/alembic.ini revision -m "describe_change"
```

Or use the root scripts: `pnpm db:migrate` / `pnpm db:current`.

## Notes

- No ORM models are required; revisions may use raw SQL via Alembic ops.
- Do not point `CAREEROS_DATABASE_URL` at the Supabase local DB (port 54322).
- Domain tables (users, consents, …) land in later M1 batches — this Batch 1
  change only installs the migration runner.
