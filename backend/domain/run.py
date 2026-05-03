from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


RunStatus = Literal["pending", "running", "cancelling", "succeeded", "failed", "cancelled"]
NodeRunStatus = Literal["pending", "running", "succeeded", "failed", "skipped"]


@dataclass
class WorkflowRun:
    run_id: str
    workflow_id: str
    module_name: str
    status: RunStatus = "pending"
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "workflow_id": self.workflow_id,
            "module_name": self.module_name,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "error": self.error,
        }


@dataclass
class WorkflowNodeRun:
    run_id: str
    node_id: str
    app_id: str
    module_id: str
    action_id: str
    action_ref: str
    device_id: int
    status: NodeRunStatus = "pending"
    error: str | None = None
