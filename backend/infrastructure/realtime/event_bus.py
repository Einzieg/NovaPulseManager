from __future__ import annotations

import inspect
from collections import defaultdict
from typing import Any, Callable


class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[Callable[[dict[str, Any]], Any]]] = defaultdict(list)

    def subscribe(self, event: str, callback: Callable[[dict[str, Any]], Any]) -> None:
        self._subscribers[event].append(callback)

    async def publish(self, event: str, data: dict[str, Any]) -> None:
        for callback in list(self._subscribers.get(event, [])):
            result = callback(data)
            if inspect.isawaitable(result):
                await result
