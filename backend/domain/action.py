from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ActionExecutionContext:
    run_id: str
    workflow_id: str | None
    node_id: str | None
    device_id: int
    device_name: str
    device: Any
    app_id: str
    module_id: str
    action_id: str
    action_ref: str
    app_config: dict[str, Any]
    module_config: dict[str, Any]
    action_config: dict[str, Any]
    node_config: dict[str, Any]
    effective_config: dict[str, Any]
    event_bus: Any
    logger: Any
    cancellation_token: Any


class ActionBase(ABC):
    action_ref: str

    def __init__(self, ctx):
        self.ctx = ctx

    async def prepare(self):
        pass

    @abstractmethod
    async def execute(self):
        raise NotImplementedError

    async def cleanup(self):
        pass
