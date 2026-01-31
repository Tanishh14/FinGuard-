"""Simple in-process broadcaster for Server-Sent Events (SSE).

This is an in-memory, single-process publisher used for development/testing.
In production use a proper pub/sub (Redis, NATS) for multi-instance scaling.
"""
import asyncio
import json
from typing import Dict, Any, AsyncGenerator, List

_subscribers: List[asyncio.Queue] = []


def publish(event: Dict[str, Any]):
    """Publish an event to all subscribers (non-blocking)."""
    data = json.dumps(event, default=str)
    for q in list(_subscribers):
        try:
            q.put_nowait(data)
        except asyncio.QueueFull:
            # Drop event if subscriber is slow
            continue


async def subscribe() -> AsyncGenerator[str, None]:
    """Async generator that yields events as they arrive."""
    q: asyncio.Queue = asyncio.Queue(maxsize=100)
    _subscribers.append(q)
    try:
        while True:
            data = await q.get()
            yield data
    finally:
        try:
            _subscribers.remove(q)
        except ValueError:
            pass
