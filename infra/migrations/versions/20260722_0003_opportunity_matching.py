"""Opportunity + Matching schemas for Job Intelligence MVP (ADR-0001).

Revision ID: 20260722_0003
Revises: 20260721_0002
Create Date: 2026-07-22
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "20260722_0003"
down_revision: str | None = "20260721_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS opportunity")
    op.execute("CREATE SCHEMA IF NOT EXISTS matching")

    op.execute(
        """
        CREATE TABLE opportunity.opportunities (
            id UUID PRIMARY KEY,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT NULL,
            is_remote BOOLEAN NOT NULL DEFAULT FALSE,
            description_text TEXT NOT NULL DEFAULT '',
            apply_url TEXT NOT NULL,
            dedup_key TEXT NOT NULL,
            status TEXT NOT NULL,
            source_kind TEXT NOT NULL,
            board_token TEXT NOT NULL,
            external_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            legal_basis TEXT NOT NULL DEFAULT 'public_ats_board_feed',
            compensation JSONB NULL,
            skills TEXT[] NOT NULL DEFAULT '{}',
            posted_at TIMESTAMPTZ NULL,
            ingested_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL,
            CONSTRAINT opportunities_dedup_key_unique UNIQUE (dedup_key)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX opportunities_status_updated_idx
            ON opportunity.opportunities (status, updated_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX opportunities_source_idx
            ON opportunity.opportunities (source_kind, board_token)
        """
    )
    op.execute(
        """
        CREATE INDEX opportunities_title_trgm_support_idx
            ON opportunity.opportunities (lower(title))
        """
    )

    op.execute(
        """
        CREATE TABLE matching.seeker_criteria (
            user_id UUID PRIMARY KEY
                REFERENCES identity.users (id)
                ON DELETE CASCADE,
            resume_text TEXT NOT NULL DEFAULT '',
            skills TEXT[] NOT NULL DEFAULT '{}',
            years_experience INT NULL,
            preferred_locations TEXT[] NOT NULL DEFAULT '{}',
            salary_expectation_min INT NULL,
            salary_currency TEXT NULL,
            remote_preference TEXT NOT NULL DEFAULT 'any',
            updated_at TIMESTAMPTZ NOT NULL
        )
        """
    )

    op.execute(
        """
        CREATE TABLE matching.matches (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL
                REFERENCES identity.users (id)
                ON DELETE CASCADE,
            opportunity_id UUID NOT NULL
                REFERENCES opportunity.opportunities (id)
                ON DELETE CASCADE,
            score DOUBLE PRECISION NOT NULL,
            hard_filter_passed BOOLEAN NOT NULL,
            reasons TEXT[] NOT NULL DEFAULT '{}',
            gaps TEXT[] NOT NULL DEFAULT '{}',
            model_version TEXT NOT NULL,
            status TEXT NOT NULL,
            computed_at TIMESTAMPTZ NOT NULL,
            CONSTRAINT matches_user_opportunity_unique UNIQUE (user_id, opportunity_id)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX matches_user_score_idx
            ON matching.matches (user_id, score DESC)
        """
    )

    # Matching is user-scoped; opportunity catalog is shared (SELECT/write for app role).
    op.execute("ALTER TABLE matching.seeker_criteria ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE matching.seeker_criteria FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE matching.matches ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE matching.matches FORCE ROW LEVEL SECURITY")

    op.execute(
        """
        CREATE POLICY seeker_criteria_own_rows ON matching.seeker_criteria
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
        CREATE POLICY matches_own_rows ON matching.matches
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

    op.execute("GRANT USAGE ON SCHEMA opportunity TO careeros_app")
    op.execute("GRANT USAGE ON SCHEMA matching TO careeros_app")
    op.execute(
        """
        GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA opportunity
            TO careeros_app
        """
    )
    op.execute(
        """
        GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA matching
            TO careeros_app
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS matching.matches")
    op.execute("DROP TABLE IF EXISTS matching.seeker_criteria")
    op.execute("DROP TABLE IF EXISTS opportunity.opportunities")
    op.execute("DROP SCHEMA IF EXISTS matching")
    op.execute("DROP SCHEMA IF EXISTS opportunity")
