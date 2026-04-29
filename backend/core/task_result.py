from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class TaskStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class TaskResult:
    status: TaskStatus
    message: str = ""
    data: Optional[dict[str, Any]] = None
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.status == TaskStatus.SUCCESS

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "success": self.success,
            "status": self.status.value,
            "message": self.message,
        }
        if self.data is not None:
            payload["data"] = self.data
        if self.error is not None:
            payload["error"] = self.error
        return payload

    @classmethod
    def ok(cls, message: str = "", *, data: Optional[dict[str, Any]] = None) -> "TaskResult":
        return cls(status=TaskStatus.SUCCESS, message=message, data=data)

    @classmethod
    def fail(
        cls,
        message: str = "",
        *,
        error: Optional[str] = None,
        data: Optional[dict[str, Any]] = None,
    ) -> "TaskResult":
        return cls(status=TaskStatus.FAILED, message=message, data=data, error=error)

    @classmethod
    def cancelled(cls, message: str = "cancelled") -> "TaskResult":
        return cls(status=TaskStatus.CANCELLED, message=message)
