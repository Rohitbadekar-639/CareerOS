# Identity & Access (`contexts/identity`)

Owns **User** and **Consent** (Domain Model). Generic subdomain — auth/privacy
evolve independently of Career Profile.

## Layers

| Layer | Status (M1) |
|---|---|
| `domain/` | Implemented — pure, no I/O |
| `application/` | Scaffold only |
| `ports/` | `UserRepository`, `AuthProvider` |
| `infrastructure/` | `PostgresUserRepository`, `SupabaseAuthProvider` (HS256 + JWKS/ES256) |
| `api/` | Scaffold only |

## Persistence & RLS

- Schema: `identity.users`, `identity.consents` (Alembic `20260721_0002`)
- RLS is **FORCE**d. Session GUCs:
  - `app.current_user_id` — own-row read/write
  - `app.current_auth_ref` — lookup by Supabase subject
  - `app.rls_bypass=on` — admin/migrations/tests only
- Runtime role: `PostgresUserRepository` uses `SET LOCAL ROLE careeros_app`
  (non-superuser, no `BYPASSRLS`) so policies apply even when the login role is
  a Docker superuser.

## Integration tests

```bash
docker compose up -d postgres
pnpm db:migrate
# if host :5432 is taken, use POSTGRES_PORT=5433 and matching DATABASE_URL
uv run pytest contexts/identity -m integration
```
