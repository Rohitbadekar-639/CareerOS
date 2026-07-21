"""Identity schema: users, consents, and Row-Level Security (M1 Batch 3).

Revision ID: 20260721_0002
Revises: 20260721_0001
Create Date: 2026-07-21
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260721_0002"
down_revision: str | None = "20260721_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS identity")

    op.execute(
        """
        CREATE TABLE identity.users (
            id UUID PRIMARY KEY,
            email TEXT NOT NULL,
            auth_ref TEXT NOT NULL,
            status TEXT NOT NULL,
            role TEXT NOT NULL,
            email_verified BOOLEAN NOT NULL DEFAULT FALSE,
            legal_hold BOOLEAN NOT NULL DEFAULT FALSE,
            tenant_id TEXT NULL,
            registered_at TIMESTAMPTZ NOT NULL,
            CONSTRAINT users_auth_ref_unique UNIQUE (auth_ref),
            CONSTRAINT users_email_unique UNIQUE (email)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX users_tenant_id_idx
            ON identity.users (tenant_id)
            WHERE tenant_id IS NOT NULL
        """
    )

    op.execute(
        """
        CREATE TABLE identity.consents (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL
                REFERENCES identity.users (id)
                ON DELETE CASCADE,
            purpose TEXT NOT NULL,
            granted_at TIMESTAMPTZ NOT NULL,
            withdrawn_at TIMESTAMPTZ NULL,
            CONSTRAINT consents_withdrawn_after_granted
                CHECK (withdrawn_at IS NULL OR withdrawn_at >= granted_at)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX consents_user_id_idx
            ON identity.consents (user_id)
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX consents_one_active_per_purpose
            ON identity.consents (user_id, purpose)
            WHERE withdrawn_at IS NULL
        """
    )

    # FORCE RLS so even the table owner is subject to policies (defense in depth).
    # Normal app access: set app.current_user_id (and optionally app.current_auth_ref).
    # Privileged/admin tooling: set app.rls_bypass = 'on' for the transaction.
    op.execute("ALTER TABLE identity.users ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE identity.users FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE identity.consents ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE identity.consents FORCE ROW LEVEL SECURITY")

    op.execute(
        """
        CREATE POLICY identity_users_isolation ON identity.users
            FOR ALL
            USING (
                current_setting('app.rls_bypass', true) = 'on'
                OR id::text = nullif(current_setting('app.current_user_id', true), '')
                OR auth_ref = nullif(current_setting('app.current_auth_ref', true), '')
            )
            WITH CHECK (
                current_setting('app.rls_bypass', true) = 'on'
                OR id::text = nullif(current_setting('app.current_user_id', true), '')
            )
        """
    )
    op.execute(
        """
        CREATE POLICY identity_consents_isolation ON identity.consents
            FOR ALL
            USING (
                current_setting('app.rls_bypass', true) = 'on'
                OR user_id::text = nullif(current_setting('app.current_user_id', true), '')
            )
            WITH CHECK (
                current_setting('app.rls_bypass', true) = 'on'
                OR user_id::text = nullif(current_setting('app.current_user_id', true), '')
            )
        """
    )

    # App role without BYPASSRLS / superuser — required for FORCE RLS to apply.
    # Local/CI: GRANT careeros_app TO the migration/login role, then SET ROLE.
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'careeros_app') THEN
                CREATE ROLE careeros_app NOSUPERUSER NOBYPASSRLS NOCREATEDB
                    NOCREATEROLE INHERIT NOLOGIN;
            END IF;
        END
        $$
        """
    )
    op.execute("GRANT USAGE ON SCHEMA identity TO careeros_app")
    op.execute(
        """
        GRANT SELECT, INSERT, UPDATE, DELETE ON
            identity.users, identity.consents TO careeros_app
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            EXECUTE format('GRANT careeros_app TO %I', current_user);
        END
        $$
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'careeros_app') THEN
                EXECUTE format('REVOKE careeros_app FROM %I', current_user);
            END IF;
        EXCEPTION
            WHEN undefined_object THEN NULL;
            WHEN invalid_grant_operation THEN NULL;
        END
        $$
        """
    )
    op.execute("DROP POLICY IF EXISTS identity_consents_isolation ON identity.consents")
    op.execute("DROP POLICY IF EXISTS identity_users_isolation ON identity.users")
    op.execute("DROP TABLE IF EXISTS identity.consents")
    op.execute("DROP TABLE IF EXISTS identity.users")
    op.execute("DROP SCHEMA IF EXISTS identity")
    op.execute("DROP ROLE IF EXISTS careeros_app")
