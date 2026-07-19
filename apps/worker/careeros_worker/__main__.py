import asyncio
import signal

from careeros_platform.settings import get_settings
from careeros_platform.task_queue import InMemoryTaskQueue
from careeros_worker.worker import run


async def _run_until_signalled() -> None:
    settings = get_settings()
    queue = InMemoryTaskQueue()
    stop_event = asyncio.Event()

    def request_stop(*_: object) -> None:
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            # Some platforms (e.g. Windows event loops) lack signal handlers.
            signal.signal(sig, request_stop)

    await run(queue, settings, stop_event)


def main() -> None:
    asyncio.run(_run_until_signalled())


if __name__ == "__main__":
    main()
