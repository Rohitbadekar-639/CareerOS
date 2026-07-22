"""Parse configured ATS boards from settings."""

from __future__ import annotations

from careeros_opportunity.domain.value_objects import SourceKind
from careeros_opportunity.ports.opportunity_source import SourceBoard
from careeros_shared_kernel import ValidationError


def parse_opportunity_boards(raw: str) -> list[SourceBoard]:
    boards: list[SourceBoard] = []
    for part in raw.split(","):
        item = part.strip()
        if not item:
            continue
        if ":" not in item:
            raise ValidationError(f"Invalid opportunity board config: {item!r}")
        kind_raw, token = item.split(":", 1)
        kind_raw = kind_raw.strip().lower()
        token = token.strip()
        if not token:
            raise ValidationError(f"Empty board token in {item!r}")
        try:
            kind = SourceKind(kind_raw)
        except ValueError as exc:
            raise ValidationError(f"Unknown source kind: {kind_raw}") from exc
        boards.append(SourceBoard(kind=kind, board_token=token))
    return boards
