"""Greenhouse public Boards API adapter."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

import httpx

from careeros_opportunity.domain.value_objects import SourceKind
from careeros_opportunity.infrastructure.text_skills import extract_skillish_tokens
from careeros_opportunity.ports.opportunity_source import (
    OpportunitySource,
    RawOpportunityListing,
    SourceBoard,
)

_REMOTE = re.compile(r"\bremote\b", re.IGNORECASE)
_TAG = re.compile(r"<[^>]+>")


class GreenhouseOpportunitySource:
    kind = SourceKind.GREENHOUSE

    def __init__(self, *, client: httpx.Client | None = None, timeout: float = 30.0) -> None:
        self._client = client
        self._timeout = timeout

    def fetch_listings(self, board: SourceBoard) -> list[RawOpportunityListing]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{board.board_token}/jobs"
        payload = self._get_json(url, params={"content": "true"})
        jobs = payload.get("jobs") if isinstance(payload, dict) else None
        if not isinstance(jobs, list):
            return []
        company = board.board_token.replace("-", " ").title()
        out: list[RawOpportunityListing] = []
        for job in jobs:
            if not isinstance(job, dict):
                continue
            listing = self._map_job(job, board=board, company=company)
            if listing is not None:
                out.append(listing)
        return out

    def _get_json(self, url: str, *, params: dict[str, str]) -> Any:
        if self._client is not None:
            response = self._client.get(url, params=params, timeout=self._timeout)
            response.raise_for_status()
            return response.json()
        with httpx.Client(timeout=self._timeout) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    def _map_job(
        self,
        job: dict[str, Any],
        *,
        board: SourceBoard,
        company: str,
    ) -> RawOpportunityListing | None:
        title = str(job.get("title") or "").strip()
        job_id = job.get("id")
        absolute_url = str(job.get("absolute_url") or "").strip()
        if not title or job_id is None or not absolute_url:
            return None
        location_name = None
        location = job.get("location")
        if isinstance(location, dict):
            raw_loc = location.get("name")
            if isinstance(raw_loc, str) and raw_loc.strip():
                location_name = raw_loc.strip()
        content = job.get("content")
        description = _TAG.sub(" ", str(content or ""))
        description = re.sub(r"\s+", " ", description).strip()
        posted_at = _parse_iso(job.get("updated_at") or job.get("first_published"))
        is_remote = bool(location_name and _REMOTE.search(location_name))
        return RawOpportunityListing(
            title=title,
            company=company,
            location=location_name,
            is_remote=is_remote,
            description_text=description,
            apply_url=absolute_url,
            external_id=str(job_id),
            source_url=absolute_url,
            posted_at=posted_at,
            skills=extract_skillish_tokens(f"{title} {description}"),
        )


def _parse_iso(raw: object) -> datetime | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _as_source(source: GreenhouseOpportunitySource) -> OpportunitySource:
    return source
