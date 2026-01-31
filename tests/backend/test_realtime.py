import asyncio
from app.services.broadcaster import subscribe, publish


async def _consume_one():
    agen = subscribe()
    async for msg in agen:
        return msg


def test_publish_and_subscribe(event_loop):
    # Publish an event and ensure subscriber receives it
    loop = asyncio.get_event_loop()
    task = loop.create_task(_consume_one())
    publish({"type": "test", "value": 1})
    res = loop.run_until_complete(task)
    assert '"type": "test"' in res
