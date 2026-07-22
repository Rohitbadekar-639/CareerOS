"""Profile + Notifications schemas for CareerOS Intelligence (ADR-0002).

Revision ID: 20260722_0005
Revises: 20260722_0004
Create Date: 2026-07-22
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "20260722_0005"
down_revision: str | None = "20260722_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS profile")
    op.execute("CREATE SCHEMA IF NOT EXISTS notifications")

    op.execute(
        """
        CREATE TABLE profile.candidate_profiles (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL UNIQUE
                REFERENCES identity.users (id)
                ON DELETE CASCADE,
            version INT NOT NULL,
            headline TEXT NOT NULL DEFAULT '',
            summary TEXT NOT NULL DEFAULT '',
            resume_text TEXT NOT NULL DEFAULT '',
            linkedin_text TEXT NOT NULL DEFAULT '',
            skills TEXT[] NOT NULL DEFAULT '{}',
            experiences JSONB NOT NULL DEFAULT '[]',
            years_experience INT NULL,
            preferred_locations TEXT[] NOT NULL DEFAULT '{}',
            salary_expectation_min INT NULL,
            salary_currency TEXT NULL,
            remote_preference TEXT NOT NULL DEFAULT 'any',
            github_username TEXT NULL,
            linkedin_url TEXT NULL,
            portfolio_url TEXT NULL,
            github_summary TEXT NOT NULL DEFAULT '',
            portfolio_summary TEXT NOT NULL DEFAULT '',
            updated_at TIMESTAMPTZ NOT NULL
        )
        """
    )

    op.execute(
        """
        CREATE TABLE notifications.notifications (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL
                REFERENCES identity.users (id)
                ON DELETE CASCADE,
            kind TEXT NOT NULL,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            payload JSONB NOT NULL DEFAULT '{}',
            status TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL,
            read_at TIMESTAMPTZ NULL
        )
        """
    )
    op.execute(
        """
        CREATE INDEX notifications_user_created_idx
            ON notifications.notifications (user_id, created_at DESC)
        """
    )

    for table in ("profile.candidate_profiles", "notifications.notifications"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")

    op.execute(
        """
        CREATE POLICY profile_own_rows ON profile.candidate_profiles
            FOR ALL
            USING (
                current_setting('app.rls_bypass', true) = 'on'
                OR user_id::text = current_setting('app.current_user_id', true)
            )
            WITH CHECK (
                current_setting('app.rls_bypass', true) = 'on'
                OR user_id::text = current_setting('app.current_user_id', true)
            )
        """
    )
    op.execute(
        """
        CREATE POLICY notifications_own_rows ON notifications.notifications
            FOR ALL
            USING (
                current_setting('app.rls_bypass', true) = 'on'
                OR user_id::text = current_setting('app.current_user_id', true)
            )
            WITH CHECK (
                current_setting('app.rls_bypass', true) = 'on'
                OR user_id::text = current_setting('app.current_user_id', true)
            )
        """
    )

    op.execute("GRANT USAGE ON SCHEMA profile TO careeros_app")
    op.execute("GRANT USAGE ON SCHEMA notifications TO careeros_app")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA profile TO careeros_app"
    )
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA notifications TO careeros_app"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS notifications.notifications")
    op.execute("DROP TABLE IF EXISTS profile.candidate_profiles")
    op.execute("DROP SCHEMA IF EXISTS notifications")
    op.execute("DROP SCHEMA IF EXISTS profile")
