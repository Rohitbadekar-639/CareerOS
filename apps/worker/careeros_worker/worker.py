"""Worker runtime: queue consumer + Job Hunter / ingest cycles."""

from __future__ import annotations

import asyncio
import logging

from careeros_platform.settings import Settings
from careeros_platform.task_queue import TaskQueue
from careeros_worker.job_hunter import run_job_hunter_cycle

logger = logging.getLogger(__name__)


async def run(
    queue: TaskQueue,
    settings: Settings,
    stop_event: asyncio.Event,
    poll_timeout: float = 1.0,
) -> None:
    """Consume queue tasks and periodically run the Job Hunter agent."""
    interval = max(60, int(settings.ingestion_interval_seconds))
    # First periodic hunt after `interval`; queue jobs trigger immediately.
    next_hunt = asyncio.get_running_loop().time() + interval

    while not stop_event.is_set():
        now = asyncio.get_running_loop().time()
        if now >= next_hunt:
            try:
                summary = await asyncio.to_thread(run_job_hunter_cycle, settings)
                logger.info("job_hunter_complete", extra={"summary": summary})
            except Exception:
                logger.exception("job_hunter_failed")
            next_hunt = now + interval

        payload = await queue.dequeue(poll_timeout)
        if payload is None:
            continue
        job = str(payload.get("job") or "")
        if job in {"opportunity.ingest", "job_hunter.run"}:
            try:
                summary = await asyncio.to_thread(run_job_hunter_cycle, settings)
                logger.info("job_hunter_task_complete", extra={"summary": summary})
            except Exception:
                logger.exception("job_hunter_task_failed")
            next_hunt = asyncio.get_running_loop().time() + interval
