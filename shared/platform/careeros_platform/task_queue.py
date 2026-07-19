"""The ``TaskQueue`` port and an in-memory adapter.

The API enqueues background work and the worker consumes it; both depend on this
port, never on a concrete broker. The MVP transport is a Postgres-backed queue
(added later, behind this same port). ``InMemoryTaskQueue`` is a dependency-free
default used for local runs and tests.
"""

import asyncio
from collections.abc import Mapping
from typing import Protocol, runtime_checkable

TaskPayload = Mapping[str, object]


@runtime_checkable
class TaskQueue(Protocol):
    async def enqueue(self, payload: TaskPayload) -> None: ...

    async def dequeue(self, timeout: float) -> TaskPayload | None:
        """Return the next payload, or ``None`` if none arrives within ``timeout``."""
        ...


class InMemoryTaskQueue:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[TaskPayload] = asyncio.Queue()

    async def enqueue(self, payload: TaskPayload) -> None:
        await self._queue.put(payload)

    async def dequeue(self, timeout: float) -> TaskPayload | None:
        try:
            return await asyncio.wait_for(self._queue.get(), timeout)
        except TimeoutError:
            return None
