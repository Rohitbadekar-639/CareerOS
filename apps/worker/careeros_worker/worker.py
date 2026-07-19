import asyncio

from careeros_platform.settings import Settings
from careeros_platform.task_queue import TaskQueue


async def run(
    queue: TaskQueue,
    settings: Settings,
    stop_event: asyncio.Event,
    poll_timeout: float = 1.0,
) -> None:
    """Run the worker's idle consumer loop until signalled to stop.

    The M0 skeleton registers no job handlers (LangGraph dispatch arrives in
    M3) and has no producers, so the loop polls the ``TaskQueue`` port, idles on
    empty results, and exits promptly once ``stop_event`` is set.
    """
    while not stop_event.is_set():
        payload = await queue.dequeue(poll_timeout)
        if payload is None:
            continue
        # No handlers in the M0 skeleton; job dispatch is added in M3.
