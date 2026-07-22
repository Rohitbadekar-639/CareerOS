"""Greenhouse adapter maps public board JSON into RawOpportunityListing."""

from __future__ import annotations

import httpx

from careeros_opportunity.domain.value_objects import SourceKind
from careeros_opportunity.infrastructure.greenhouse_source import GreenhouseOpportunitySource
from careeros_opportunity.ports.opportunity_source import SourceBoard


def test_greenhouse_maps_jobs() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "boards/stripe/jobs" in str(request.url)
        return httpx.Response(
            200,
            json={
                "jobs": [
                    {
                        "id": 42,
                        "title": "Software Engineer",
                        "absolute_url": "https://boards.greenhouse.io/stripe/jobs/42",
                        "location": {"name": "Remote"},
                        "content": "<p>Python and FastAPI</p>",
                        "updated_at": "2026-07-01T00:00:00Z",
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    source = GreenhouseOpportunitySource(client=client)
    listings = source.fetch_listings(SourceBoard(kind=SourceKind.GREENHOUSE, board_token="stripe"))
    assert len(listings) == 1
    assert listings[0].title == "Software Engineer"
    assert listings[0].is_remote is True
    assert listings[0].external_id == "42"
