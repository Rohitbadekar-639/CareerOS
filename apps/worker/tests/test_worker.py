import asyncio

from careeros_platform.settings import Environment, Settings
from careeros_platform.task_queue import InMemoryTaskQueue
from careeros_worker.worker import run


def _test_settings() -> Settings:
    return Settings(
        database_url="postgresql://localhost:5432/careeros_test",
        supabase_url="http://127.0.0.1:54321",
        supabase_anon_key="test-anon-key",
        supabase_jwt_secret="test-jwt-secret-at-least-32-characters-long",
        environment=Environment.DEVELOPMENT,
    )


def test_worker_starts_idles_and_stops_cleanly() -> None:
    async def scenario() -> None:
        queue = InMemoryTaskQueue()
        stop_event = asyncio.Event()
        task = asyncio.create_task(run(queue, _test_settings(), stop_event, poll_timeout=0.01))

        await asyncio.sleep(0.05)
        assert not task.done()

        stop_event.set()
        await asyncio.wait_for(task, timeout=1.0)
        assert task.done()
        assert task.exception() is None

    asyncio.run(scenario())
