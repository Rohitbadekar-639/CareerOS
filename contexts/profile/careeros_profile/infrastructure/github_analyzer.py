"""GitHub public profile/repo analyzer."""

from __future__ import annotations

from typing import Any

import httpx

from careeros_profile.ports.profile_ports import GitHubAnalysis
from careeros_shared_kernel import ValidationError


class HttpGitHubAnalyzer:
    def __init__(self, *, client: httpx.Client | None = None, timeout: float = 20.0) -> None:
        self._client = client
        self._timeout = timeout

    def analyze(self, username: str) -> GitHubAnalysis:
        user = self._get_json(f"https://api.github.com/users/{username}")
        repos = self._get_json(
            f"https://api.github.com/users/{username}/repos?sort=updated&per_page=10"
        )
        if not isinstance(user, dict):
            raise ValidationError("GitHub user lookup failed")
        login = str(user.get("login") or username)
        bio = str(user.get("bio") or "").strip()
        languages: list[str] = []
        top_repos: list[str] = []
        if isinstance(repos, list):
            for repo in repos:
                if not isinstance(repo, dict):
                    continue
                name = str(repo.get("name") or "").strip()
                lang = str(repo.get("language") or "").strip()
                if name:
                    top_repos.append(name)
                if lang and lang.lower() not in {x.lower() for x in languages}:
                    languages.append(lang)
        summary_parts = [
            f"GitHub @{login}",
            bio,
            f"Public repos: {user.get('public_repos', 0)}",
            ("Top repos: " + ", ".join(top_repos[:5])) if top_repos else "",
            ("Languages: " + ", ".join(languages[:8])) if languages else "",
        ]
        return GitHubAnalysis(
            username=login,
            summary=" | ".join(p for p in summary_parts if p),
            languages=tuple(languages[:12]),
            top_repos=tuple(top_repos[:8]),
        )

    def _get_json(self, url: str) -> Any:
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "CareerOS-MVP"}
        if self._client is not None:
            response = self._client.get(url, headers=headers, timeout=self._timeout)
            if response.status_code == 404:
                raise ValidationError(f"GitHub user not found: {url}")
            response.raise_for_status()
            return response.json()
        with httpx.Client(timeout=self._timeout, headers=headers) as client:
            response = client.get(url)
            if response.status_code == 404:
                raise ValidationError("GitHub user not found")
            response.raise_for_status()
            return response.json()
