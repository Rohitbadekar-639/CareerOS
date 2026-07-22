"""Postgres adapter for OpportunityRepository (shared catalog — no per-user RLS)."""

from __future__ import annotations

import json
from typing import Any

from psycopg import Connection
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from careeros_opportunity.domain.lifecycle import OpportunityStatus
from careeros_opportunity.domain.opportunity import CompensationHint, Opportunity
from careeros_opportunity.domain.value_objects import (
    CompanyName,
    DedupKey,
    OpportunityId,
    SourceKind,
    SourceProvenance,
)
from careeros_opportunity.ports.opportunity_source import OpportunitySearchFilter


class PostgresOpportunityRepository:
    def __init__(self, connection: Connection[Any]) -> None:
        self._conn = connection
        self._conn.row_factory = dict_row

    def get(self, opportunity_id: OpportunityId) -> Opportunity | None:
        row = self._conn.execute(
            "SELECT * FROM opportunity.opportunities WHERE id = %s",
            (opportunity_id.value,),
        ).fetchone()
        return self._from_row(row) if row else None

    def find_by_dedup_key(self, dedup_key: DedupKey) -> Opportunity | None:
        row = self._conn.execute(
            "SELECT * FROM opportunity.opportunities WHERE dedup_key = %s",
            (str(dedup_key),),
        ).fetchone()
        return self._from_row(row) if row else None

    def upsert(self, opportunity: Opportunity) -> Opportunity:
        comp = opportunity.compensation
        self._conn.execute(
            """
            INSERT INTO opportunity.opportunities (
                id, title, company, location, is_remote, description_text, apply_url,
                dedup_key, status, source_kind, board_token, external_id, source_url,
                legal_basis, compensation, skills, posted_at, ingested_at, updated_at
            ) VALUES (
                %(id)s, %(title)s, %(company)s, %(location)s, %(is_remote)s,
                %(description_text)s, %(apply_url)s, %(dedup_key)s, %(status)s,
                %(source_kind)s, %(board_token)s, %(external_id)s, %(source_url)s,
                %(legal_basis)s, %(compensation)s, %(skills)s, %(posted_at)s,
                %(ingested_at)s, %(updated_at)s
            )
            ON CONFLICT (dedup_key) DO UPDATE SET
                title = EXCLUDED.title,
                company = EXCLUDED.company,
                location = EXCLUDED.location,
                is_remote = EXCLUDED.is_remote,
                description_text = EXCLUDED.description_text,
                apply_url = EXCLUDED.apply_url,
                status = EXCLUDED.status,
                source_kind = EXCLUDED.source_kind,
                board_token = EXCLUDED.board_token,
                external_id = EXCLUDED.external_id,
                source_url = EXCLUDED.source_url,
                legal_basis = EXCLUDED.legal_basis,
                compensation = EXCLUDED.compensation,
                skills = EXCLUDED.skills,
                posted_at = EXCLUDED.posted_at,
                updated_at = EXCLUDED.updated_at
            """,
            {
                "id": opportunity.id.value,
                "title": opportunity.title,
                "company": str(opportunity.company),
                "location": opportunity.location,
                "is_remote": opportunity.is_remote,
                "description_text": opportunity.description_text,
                "apply_url": opportunity.apply_url,
                "dedup_key": str(opportunity.dedup_key),
                "status": opportunity.status.value,
                "source_kind": opportunity.provenance.kind.value,
                "board_token": opportunity.provenance.board_token,
                "external_id": opportunity.provenance.external_id,
                "source_url": opportunity.provenance.source_url,
                "legal_basis": opportunity.provenance.legal_basis,
                "compensation": Jsonb(
                    {
                        "currency": comp.currency if comp else None,
                        "min_amount": comp.min_amount if comp else None,
                        "max_amount": comp.max_amount if comp else None,
                        "period": comp.period if comp else None,
                    }
                    if comp
                    else None
                ),
                "skills": list(opportunity.skills),
                "posted_at": opportunity.posted_at,
                "ingested_at": opportunity.ingested_at,
                "updated_at": opportunity.updated_at,
            },
        )
        # Reload by dedup to return canonical row id after conflict update.
        loaded = self.find_by_dedup_key(opportunity.dedup_key)
        assert loaded is not None
        return loaded

    def search(self, filters: OpportunitySearchFilter) -> list[Opportunity]:
        clauses = ["status = 'active'"]
        params: list[Any] = []
        if filters.query:
            clauses.append("(title ILIKE %s OR company ILIKE %s OR description_text ILIKE %s)")
            q = f"%{filters.query.strip()}%"
            params.extend([q, q, q])
        if filters.location:
            clauses.append("location ILIKE %s")
            params.append(f"%{filters.location.strip()}%")
        if filters.remote_only is True:
            clauses.append("is_remote = TRUE")
        if filters.company:
            clauses.append("company ILIKE %s")
            params.append(f"%{filters.company.strip()}%")
        if filters.source_kind is not None:
            clauses.append("source_kind = %s")
            params.append(filters.source_kind.value)
        params.extend([filters.limit, filters.offset])
        sql = f"""
            SELECT * FROM opportunity.opportunities
            WHERE {" AND ".join(clauses)}
            ORDER BY updated_at DESC
            LIMIT %s OFFSET %s
        """
        rows = self._conn.execute(sql, params).fetchall()
        return [self._from_row(row) for row in rows]

    def list_active(self, *, limit: int = 500) -> list[Opportunity]:
        rows = self._conn.execute(
            """
            SELECT * FROM opportunity.opportunities
            WHERE status = 'active'
            ORDER BY updated_at DESC
            LIMIT %s
            """,
            (limit,),
        ).fetchall()
        return [self._from_row(row) for row in rows]

    def _from_row(self, row: dict[str, Any]) -> Opportunity:
        comp_raw = row.get("compensation")
        compensation = None
        if isinstance(comp_raw, dict):
            compensation = CompensationHint(
                currency=comp_raw.get("currency"),
                min_amount=comp_raw.get("min_amount"),
                max_amount=comp_raw.get("max_amount"),
                period=comp_raw.get("period"),
            )
        elif isinstance(comp_raw, str) and comp_raw:
            parsed = json.loads(comp_raw)
            if isinstance(parsed, dict):
                compensation = CompensationHint(
                    currency=parsed.get("currency"),
                    min_amount=parsed.get("min_amount"),
                    max_amount=parsed.get("max_amount"),
                    period=parsed.get("period"),
                )
        skills = row.get("skills") or []
        if not isinstance(skills, list):
            skills = []
        return Opportunity(
            OpportunityId(row["id"]),
            title=row["title"],
            company=CompanyName(row["company"]),
            location=row.get("location"),
            is_remote=bool(row["is_remote"]),
            description_text=row["description_text"] or "",
            apply_url=row["apply_url"],
            provenance=SourceProvenance(
                kind=SourceKind(row["source_kind"]),
                board_token=row["board_token"],
                external_id=row["external_id"],
                source_url=row["source_url"],
                legal_basis=row.get("legal_basis") or "public_ats_board_feed",
            ),
            dedup_key=DedupKey(row["dedup_key"]),
            status=OpportunityStatus(row["status"]),
            compensation=compensation,
            posted_at=row.get("posted_at"),
            ingested_at=row["ingested_at"],
            updated_at=row["updated_at"],
            skills=[str(s) for s in skills],
        )
