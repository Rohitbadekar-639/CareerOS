"""Application tracking schema for save/apply/tracker MVP.

Revision ID: 20260722_0004
Revises: 20260722_0003
Create Date: 2026-07-22
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "20260722_0004"
down_revision: str | None = "20260722_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS application_tracking")
    op.execute(
        """
        CREATE TABLE application_tracking.applications (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL
                REFERENCES identity.users (id)
                ON DELETE CASCADE,
            opportunity_id UUID NOT NULL
                REFERENCES opportunity.opportunities (id)
                ON DELETE CASCADE,
            status TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            cover_letter_draft TEXT NULL,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX applications_one_active_per_user_opp
            ON application_tracking.applications (user_id, opportunity_id)
            WHERE status NOT IN ('closed', 'rejected', 'withdrawn')
        """
    )
    op.execute(
        """
        CREATE INDEX applications_user_updated_idx
            ON application_tracking.applications (user_id, updated_at DESC)
        """
    )
    op.execute("ALTER TABLE application_tracking.applications ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE application_tracking.applications FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY applications_own_rows ON application_tracking.applications
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
    op.execute("GRANT USAGE ON SCHEMA application_tracking TO careeros_app")
    op.execute(
        """
        GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA application_tracking
            TO careeros_app
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS application_tracking.applications")
    op.execute("DROP SCHEMA IF EXISTS application_tracking")
