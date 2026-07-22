"""Postgres ProfileRepository with RLS by user_id."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from psycopg import Connection
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from careeros_profile.domain.profile import CandidateProfile, Experience, ExternalLinks

_SET_USER = "SELECT set_config('app.current_user_id', %s, true)"
_SET_BYPASS = "SELECT set_config('app.rls_bypass', %s, true)"


class PostgresProfileRepository:
    def __init__(self, connection: Connection[Any]) -> None:
        self._conn = connection
        self._conn.row_factory = dict_row

    def get(self, user_id: UUID) -> CandidateProfile | None:
        with self._conn.transaction():
            self._scope(user_id)
            row = self._conn.execute(
                "SELECT * FROM profile.candidate_profiles WHERE user_id = %s",
                (user_id,),
            ).fetchone()
            return self._from_row(row) if row else None

    def save(self, profile: CandidateProfile) -> None:
        with self._conn.transaction():
            self._scope(profile.user_id)
            self._conn.execute(
                """
                INSERT INTO profile.candidate_profiles (
                    id, user_id, version, headline, summary, resume_text, linkedin_text,
                    skills, experiences, years_experience, preferred_locations,
                    salary_expectation_min, salary_currency, remote_preference,
                    github_username, linkedin_url, portfolio_url,
                    github_summary, portfolio_summary, updated_at
                ) VALUES (
                    %(id)s, %(user_id)s, %(version)s, %(headline)s, %(summary)s,
                    %(resume_text)s, %(linkedin_text)s, %(skills)s, %(experiences)s,
                    %(years_experience)s, %(preferred_locations)s,
                    %(salary_expectation_min)s, %(salary_currency)s, %(remote_preference)s,
                    %(github_username)s, %(linkedin_url)s, %(portfolio_url)s,
                    %(github_summary)s, %(portfolio_summary)s, %(updated_at)s
                )
                ON CONFLICT (user_id) DO UPDATE SET
                    version = EXCLUDED.version,
                    headline = EXCLUDED.headline,
                    summary = EXCLUDED.summary,
                    resume_text = EXCLUDED.resume_text,
                    linkedin_text = EXCLUDED.linkedin_text,
                    skills = EXCLUDED.skills,
                    experiences = EXCLUDED.experiences,
                    years_experience = EXCLUDED.years_experience,
                    preferred_locations = EXCLUDED.preferred_locations,
                    salary_expectation_min = EXCLUDED.salary_expectation_min,
                    salary_currency = EXCLUDED.salary_currency,
                    remote_preference = EXCLUDED.remote_preference,
                    github_username = EXCLUDED.github_username,
                    linkedin_url = EXCLUDED.linkedin_url,
                    portfolio_url = EXCLUDED.portfolio_url,
                    github_summary = EXCLUDED.github_summary,
                    portfolio_summary = EXCLUDED.portfolio_summary,
                    updated_at = EXCLUDED.updated_at
                """,
                {
                    "id": profile.id,
                    "user_id": profile.user_id,
                    "version": profile.version,
                    "headline": profile.headline,
                    "summary": profile.summary,
                    "resume_text": profile.resume_text,
                    "linkedin_text": profile.linkedin_text,
                    "skills": list(profile.skills),
                    "experiences": Jsonb(
                        [
                            {
                                "title": e.title,
                                "company": e.company,
                                "start_year": e.start_year,
                                "end_year": e.end_year,
                                "summary": e.summary,
                            }
                            for e in profile.experiences
                        ]
                    ),
                    "years_experience": profile.years_experience,
                    "preferred_locations": list(profile.preferred_locations),
                    "salary_expectation_min": profile.salary_expectation_min,
                    "salary_currency": profile.salary_currency,
                    "remote_preference": profile.remote_preference,
                    "github_username": profile.links.github_username,
                    "linkedin_url": profile.links.linkedin_url,
                    "portfolio_url": profile.links.portfolio_url,
                    "github_summary": profile.github_summary,
                    "portfolio_summary": profile.portfolio_summary,
                    "updated_at": profile.updated_at,
                },
            )

    def list_user_ids(self) -> list[UUID]:
        with self._conn.transaction():
            self._conn.execute("SET LOCAL ROLE careeros_app")
            self._conn.execute(_SET_BYPASS, ("on",))
            rows = self._conn.execute("SELECT user_id FROM profile.candidate_profiles").fetchall()
            return [row["user_id"] for row in rows]

    def _scope(self, user_id: UUID) -> None:
        self._conn.execute("SET LOCAL ROLE careeros_app")
        self._conn.execute(_SET_BYPASS, ("off",))
        self._conn.execute(_SET_USER, (str(user_id),))

    def _from_row(self, row: dict[str, Any]) -> CandidateProfile:
        raw_exps = row.get("experiences") or []
        if isinstance(raw_exps, str):
            raw_exps = json.loads(raw_exps)
        experiences = tuple(
            Experience(
                title=str(item.get("title") or ""),
                company=str(item.get("company") or ""),
                start_year=item.get("start_year"),
                end_year=item.get("end_year"),
                summary=str(item.get("summary") or ""),
            )
            for item in raw_exps
            if isinstance(item, dict) and item.get("title") and item.get("company")
        )
        return CandidateProfile(
            id=row["id"],
            user_id=row["user_id"],
            version=int(row["version"]),
            headline=row.get("headline") or "",
            summary=row.get("summary") or "",
            resume_text=row.get("resume_text") or "",
            linkedin_text=row.get("linkedin_text") or "",
            skills=tuple(row.get("skills") or ()),
            experiences=experiences,
            years_experience=row.get("years_experience"),
            preferred_locations=tuple(row.get("preferred_locations") or ()),
            salary_expectation_min=row.get("salary_expectation_min"),
            salary_currency=row.get("salary_currency"),
            remote_preference=row.get("remote_preference") or "any",
            links=ExternalLinks(
                github_username=row.get("github_username"),
                linkedin_url=row.get("linkedin_url"),
                portfolio_url=row.get("portfolio_url"),
            ),
            github_summary=row.get("github_summary") or "",
            portfolio_summary=row.get("portfolio_summary") or "",
            updated_at=row["updated_at"],
        )
