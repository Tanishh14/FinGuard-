"""Real-time stream endpoint (SSE) for live transactions and alerts."""
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio

from app.services.broadcaster import subscribe

router = APIRouter()


async def event_generator(request: Request):
    # stream "data: <json>\n\n" per Server-Sent Events spec
    agen = subscribe()
    async for msg in agen:
        # If client disconnected, stop
        if await request.is_disconnected():
            break
        yield f"data: {msg}\n\n"


@router.get("/stream")
async def stream(request: Request):
    return StreamingResponse(event_generator(request), media_type="text/event-stream")
