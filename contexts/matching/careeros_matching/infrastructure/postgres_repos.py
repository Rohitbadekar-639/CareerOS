"""Postgres adapters for Matching (RLS by user_id)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from psycopg import Connection
from psycopg.rows import dict_row

from careeros_matching.domain.match import Match, MatchStatus
from careeros_matching.domain.seeker_criteria import RemotePreference, SeekerCriteria

_SET_USER = "SELECT set_config('app.current_user_id', %s, true)"
_SET_BYPASS = "SELECT set_config('app.rls_bypass', %s, true)"


class PostgresSeekerCriteriaRepository:
    def __init__(self, connection: Connection[Any]) -> None:
        self._conn = connection
        self._conn.row_factory = dict_row

    def list_user_ids(self) -> list[UUID]:
        with self._conn.transaction():
            self._assume_app_role()
            self._conn.execute(_SET_BYPASS, ("on",))
            rows = self._conn.execute("SELECT user_id FROM matching.seeker_criteria").fetchall()
            return [row["user_id"] for row in rows]

    def get(self, user_id: UUID) -> SeekerCriteria | None:
        with self._conn.transaction():
            self._assume_app_role()
            self._scope(user_id)
            row = self._conn.execute(
                "SELECT * FROM matching.seeker_criteria WHERE user_id = %s",
                (user_id,),
            ).fetchone()
            if row is None:
                return None
            return SeekerCriteria(
                user_id=row["user_id"],
                resume_text=row["resume_text"] or "",
                skills=tuple(row["skills"] or ()),
                years_experience=row.get("years_experience"),
                preferred_locations=tuple(row["preferred_locations"] or ()),
                salary_expectation_min=row.get("salary_expectation_min"),
                salary_currency=row.get("salary_currency"),
                remote_preference=RemotePreference(row["remote_preference"]),
                updated_at=row["updated_at"],
            )

    def save(self, criteria: SeekerCriteria) -> None:
        with self._conn.transaction():
            self._assume_app_role()
            self._scope(criteria.user_id)
            self._conn.execute(
                """
                INSERT INTO matching.seeker_criteria (
                    user_id, resume_text, skills, years_experience, preferred_locations,
                    salary_expectation_min, salary_currency, remote_preference, updated_at
                ) VALUES (
                    %(user_id)s, %(resume_text)s, %(skills)s, %(years_experience)s,
                    %(preferred_locations)s, %(salary_expectation_min)s, %(salary_currency)s,
                    %(remote_preference)s, %(updated_at)s
                )
                ON CONFLICT (user_id) DO UPDATE SET
                    resume_text = EXCLUDED.resume_text,
                    skills = EXCLUDED.skills,
                    years_experience = EXCLUDED.years_experience,
                    preferred_locations = EXCLUDED.preferred_locations,
                    salary_expectation_min = EXCLUDED.salary_expectation_min,
                    salary_currency = EXCLUDED.salary_currency,
                    remote_preference = EXCLUDED.remote_preference,
                    updated_at = EXCLUDED.updated_at
                """,
                {
                    "user_id": criteria.user_id,
                    "resume_text": criteria.resume_text,
                    "skills": list(criteria.skills),
                    "years_experience": criteria.years_experience,
                    "preferred_locations": list(criteria.preferred_locations),
                    "salary_expectation_min": criteria.salary_expectation_min,
                    "salary_currency": criteria.salary_currency,
                    "remote_preference": criteria.remote_preference.value,
                    "updated_at": criteria.updated_at,
                },
            )

    def _assume_app_role(self) -> None:
        self._conn.execute("SET LOCAL ROLE careeros_app")

    def _scope(self, user_id: UUID) -> None:
        self._conn.execute(_SET_BYPASS, ("off",))
        self._conn.execute(_SET_USER, (str(user_id),))


class PostgresMatchRepository:
    def __init__(self, connection: Connection[Any]) -> None:
        self._conn = connection
        self._conn.row_factory = dict_row

    def replace_for_user(self, user_id: UUID, matches: list[Match]) -> None:
        with self._conn.transaction():
            self._assume_app_role()
            self._scope(user_id)
            self._conn.execute(
                "DELETE FROM matching.matches WHERE user_id = %s",
                (user_id,),
            )
            for match in matches:
                self._conn.execute(
                    """
                    INSERT INTO matching.matches (
                        id, user_id, opportunity_id, score, hard_filter_passed,
                        reasons, gaps, model_version, status, computed_at
                    ) VALUES (
                        %(id)s, %(user_id)s, %(opportunity_id)s, %(score)s,
                        %(hard_filter_passed)s, %(reasons)s, %(gaps)s,
                        %(model_version)s, %(status)s, %(computed_at)s
                    )
                    """,
                    {
                        "id": match.id,
                        "user_id": match.user_id,
                        "opportunity_id": match.opportunity_id,
                        "score": match.score,
                        "hard_filter_passed": match.hard_filter_passed,
                        "reasons": list(match.reasons),
                        "gaps": list(match.gaps),
                        "model_version": match.model_version,
                        "status": match.status.value,
                        "computed_at": match.computed_at,
                    },
                )

    def get_for_opportunity(self, user_id: UUID, opportunity_id: UUID) -> Match | None:
        with self._conn.transaction():
            self._assume_app_role()
            self._scope(user_id)
            row = self._conn.execute(
                """
                SELECT * FROM matching.matches
                WHERE user_id = %s AND opportunity_id = %s
                ORDER BY computed_at DESC
                LIMIT 1
                """,
                (user_id, opportunity_id),
            ).fetchone()
            if row is None:
                return None
            return Match(
                id=row["id"],
                user_id=row["user_id"],
                opportunity_id=row["opportunity_id"],
                score=float(row["score"]),
                hard_filter_passed=bool(row["hard_filter_passed"]),
                reasons=tuple(row["reasons"] or ()),
                gaps=tuple(row["gaps"] or ()),
                model_version=row["model_version"],
                status=MatchStatus(row["status"]),
                computed_at=row["computed_at"],
            )

    def list_surfaced(
        self,
        user_id: UUID,
        *,
        min_score: float = 0.55,
        limit: int = 50,
    ) -> list[Match]:
        with self._conn.transaction():
            self._assume_app_role()
            self._scope(user_id)
            rows = self._conn.execute(
                """
                SELECT * FROM matching.matches
                WHERE user_id = %s
                  AND status = 'surfaced'
                  AND hard_filter_passed = TRUE
                  AND score >= %s
                ORDER BY score DESC
                LIMIT %s
                """,
                (user_id, min_score, limit),
            ).fetchall()
            return [
                Match(
                    id=row["id"],
                    user_id=row["user_id"],
                    opportunity_id=row["opportunity_id"],
                    score=float(row["score"]),
                    hard_filter_passed=bool(row["hard_filter_passed"]),
                    reasons=tuple(row["reasons"] or ()),
                    gaps=tuple(row["gaps"] or ()),
                    model_version=row["model_version"],
                    status=MatchStatus(row["status"]),
                    computed_at=row["computed_at"],
                )
                for row in rows
            ]

    def _assume_app_role(self) -> None:
        self._conn.execute("SET LOCAL ROLE careeros_app")

    def _scope(self, user_id: UUID) -> None:
        self._conn.execute(_SET_BYPASS, ("off",))
        self._conn.execute(_SET_USER, (str(user_id),))
