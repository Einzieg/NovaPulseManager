from __future__ import annotations

from typing import Awaitable, TypeVar

from fastapi import HTTPException

from backend.application.errors import DeviceAlreadyRunning

T = TypeVar("T")


async def call_handler(awaitable: Awaitable[T]) -> T:
    try:
        return await awaitable
    except DeviceAlreadyRunning as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
