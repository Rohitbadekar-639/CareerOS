"""Job Hunter Agent — worker orchestration (ADR-0002)."""

from __future__ import annotations

import logging
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from careeros_application_tracking.application import AttachCoverLetterDraft
from careeros_application_tracking.infrastructure import PostgresApplicationRepository
from careeros_matching.application import CareerCopilot, RecomputeMatches, sync_snapshot_to_matching
from careeros_matching.application.copilot import OpportunityBrief
from careeros_matching.domain.ranking import OpportunitySnapshot
from careeros_matching.infrastructure import (
    PostgresMatchRepository,
    PostgresSeekerCriteriaRepository,
)
from careeros_notifications.application import PublishNotification
from careeros_notifications.domain.notification import NotificationKind
from careeros_notifications.infrastructure import PostgresNotificationRepository
from careeros_opportunity.application import RefreshConfiguredSources, parse_opportunity_boards
from careeros_opportunity.domain.value_objects import OpportunityId
from careeros_opportunity.infrastructure import (
    AshbyOpportunitySource,
    GreenhouseOpportunitySource,
    PostgresOpportunityRepository,
)
from careeros_platform.db import open_connection
from careeros_platform.settings import Settings
from careeros_profile.infrastructure import PostgresProfileRepository
from careeros_worker.profile_bridge import profile_to_snapshot

logger = logging.getLogger(__name__)


def _snapshots(opps: list[Any]) -> list[OpportunitySnapshot]:
    out: list[OpportunitySnapshot] = []
    for opp in opps:
        salary_min = None
        salary_currency = None
        if opp.compensation is not None:
            salary_min = opp.compensation.min_amount
            salary_currency = opp.compensation.currency
        out.append(
            OpportunitySnapshot(
                opportunity_id=opp.id.value,
                title=opp.title,
                company=str(opp.company),
                location=opp.location,
                is_remote=opp.is_remote,
                description_text=opp.description_text,
                skills=opp.skills,
                salary_min=salary_min,
                salary_currency=salary_currency,
            )
        )
    return out


def run_job_hunter_cycle(settings: Settings) -> dict[str, object]:
    """Discover → sync profiles → rerank → notify → prepare drafts."""
    boards = parse_opportunity_boards(settings.opportunity_boards)
    strong_threshold = float(settings.match_min_score)
    conn = open_connection(settings.database_url)
    try:
        opp_repo = PostgresOpportunityRepository(conn)
        ingest = RefreshConfiguredSources(
            repository=opp_repo,
            sources={
                "greenhouse": GreenhouseOpportunitySource(),
                "ashby": AshbyOpportunitySource(),
            },
            boards=boards,
        ).execute()

        opportunities = _snapshots(opp_repo.list_active(limit=settings.opportunity_active_limit))
        profile_repo = PostgresProfileRepository(conn)
        criteria_repo = PostgresSeekerCriteriaRepository(conn)
        match_repo = PostgresMatchRepository(conn)
        notify = PublishNotification(repository=PostgresNotificationRepository(conn))
        apps = PostgresApplicationRepository(conn)
        rematcher = RecomputeMatches(criteria_repo=criteria_repo, match_repo=match_repo)
        copilot = CareerCopilot()

        notified = 0
        drafts = 0
        user_ids = list({*profile_repo.list_user_ids(), *criteria_repo.list_user_ids()})
        for user_id in user_ids:
            profile = profile_repo.get(user_id)
            if profile is not None:
                sync_snapshot_to_matching(
                    profile_to_snapshot(profile),
                    criteria_repo=criteria_repo,
                )
            matches = rematcher.execute(user_id, opportunities)
            strong = [
                m
                for m in matches
                if m.hard_filter_passed
                and m.score >= strong_threshold
                and m.status.value == "surfaced"
            ][:5]
            if not strong:
                continue
            lines: list[str] = []
            prep_lines: list[str] = []
            for match in strong:
                opp = opp_repo.get(OpportunityId(match.opportunity_id))
                if opp is None:
                    continue
                reason = match.reasons[0] if match.reasons else "Strong skill fit"
                lines.append(f"- {opp.title} at {opp.company} ({match.score:.0%}): {reason}")
                brief = OpportunityBrief(
                    title=opp.title,
                    company=str(opp.company),
                    location=opp.location,
                    is_remote=opp.is_remote,
                    description_text=opp.description_text,
                    skills=opp.skills,
                )
                criteria = criteria_repo.get(user_id)
                advice = copilot.advise(criteria=criteria, match=match, opportunity=brief)
                if advice.resume_suggestions:
                    tip = advice.resume_suggestions[0]
                    prep_lines.append(f"- {opp.title} @ {opp.company}: {tip}")
                if criteria is not None:
                    draft = copilot.draft_cover_letter(
                        criteria=criteria,
                        opportunity=brief,
                        match=match,
                    )
                    AttachCoverLetterDraft(repository=apps).execute(
                        user_id=user_id,
                        opportunity_id=match.opportunity_id,
                        draft=draft.body,
                    )
                    drafts += 1
            if lines:
                notify.execute(
                    user_id=user_id,
                    kind=NotificationKind.STRONG_MATCH,
                    title=f"{len(lines)} strong matches found",
                    body="Job Hunter found new highly relevant openings:\n" + "\n".join(lines),
                    payload={"count": len(lines), "at": datetime.now(UTC).isoformat()},
                )
                notified += 1
            if prep_lines:
                notify.execute(
                    user_id=user_id,
                    kind=NotificationKind.HUNTER_PREP,
                    title="Resume tips for strong matches",
                    body=(
                        "Grounded suggestions (only claim what is already in your profile):\n"
                        + "\n".join(prep_lines)
                    ),
                    payload={"count": len(prep_lines)},
                )

        for user_id in user_ids:
            surfaced = match_repo.list_surfaced(
                user_id,
                min_score=strong_threshold,
                limit=10,
            )
            if not surfaced:
                continue
            digest_lines: list[str] = []
            for match in surfaced[:5]:
                opp = opp_repo.get(OpportunityId(match.opportunity_id))
                if opp is None:
                    continue
                why = "; ".join(match.reasons[:2]) if match.reasons else "Fit score above threshold"
                digest_lines.append(f"{opp.title} @ {opp.company} — {match.score:.0%} — {why}")
            notify.execute(
                user_id=user_id,
                kind=NotificationKind.DAILY_DIGEST,
                title="Daily recommendation digest",
                body="Top opportunities for you today:\n- " + "\n- ".join(digest_lines),
                payload={"items": len(digest_lines)},
            )

        conn.commit()
        return {
            "boards": {k: asdict(v) for k, v in ingest.items()},
            "users": len(user_ids),
            "notified_users": notified,
            "cover_letter_drafts": drafts,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
