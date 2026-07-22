"""Shared lightweight skill token harvest for ATS adapters."""

from __future__ import annotations

import re

_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9+.#]{1,24}")
_STOP = frozenset(
    {
        "with",
        "and",
        "the",
        "for",
        "you",
        "our",
        "will",
        "this",
        "that",
        "from",
        "have",
        "your",
        "are",
        "job",
        "role",
        "team",
        "work",
        "about",
        "experience",
        "years",
    }
)


def extract_skillish_tokens(text: str, *, limit: int = 40) -> tuple[str, ...]:
    tokens = _TOKEN.findall(text.lower())
    seen: list[str] = []
    for tok in tokens:
        if tok in _STOP or len(tok) < 3:
            continue
        if tok not in seen:
            seen.append(tok)
        if len(seen) >= limit:
            break
    return tuple(seen)
