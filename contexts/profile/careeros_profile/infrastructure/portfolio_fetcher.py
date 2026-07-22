"""Public portfolio page fetcher (best-effort text summary)."""

from __future__ import annotations

import re

import httpx

from careeros_profile.domain.extraction import extract_from_text
from careeros_profile.ports.profile_ports import PortfolioSnapshot
from careeros_shared_kernel import ValidationError

_TAG = re.compile(r"<[^>]+>")


class HttpPortfolioFetcher:
    def __init__(self, *, client: httpx.Client | None = None, timeout: float = 20.0) -> None:
        self._client = client
        self._timeout = timeout

    def fetch(self, url: str) -> PortfolioSnapshot:
        if not url.startswith(("http://", "https://")):
            raise ValidationError("Portfolio URL must be http(s)")
        html = self._get_text(url)
        text = _TAG.sub(" ", html)
        text = re.sub(r"\s+", " ", text).strip()
        extraction = extract_from_text(text[:8000])
        return PortfolioSnapshot(
            url=url,
            summary=extraction.summary or text[:400],
            keywords=extraction.skills[:16],
        )

    def _get_text(self, url: str) -> str:
        headers = {"User-Agent": "CareerOS-MVP"}
        if self._client is not None:
            response = self._client.get(
                url, headers=headers, timeout=self._timeout, follow_redirects=True
            )
            response.raise_for_status()
            return response.text
        with httpx.Client(timeout=self._timeout, headers=headers, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.text
