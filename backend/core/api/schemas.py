from __future__ import annotations

from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, ConfigDict, Field


class StartTaskRequest(BaseModel):
    module_name: str = Field(..., min_length=1)
    plugin_id: str = Field(..., min_length=1)


class StopTaskRequest(BaseModel):
    module_name: str = Field(..., min_length=1)


class WorkflowPosition(BaseModel):
    x: float
    y: float


class WorkflowNode(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    plugin_id: str
    position: WorkflowPosition
    config: Dict[str, Any] = Field(default_factory=dict)


class WorkflowEdge(BaseModel):
    id: str
    source: str
    target: str


class WorkflowData(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    name: str = "Untitled"
    module_name: Optional[str] = None
    description: Optional[str] = None
    nodes: List[WorkflowNode] = Field(default_factory=list)
    edges: List[WorkflowEdge] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SaveWorkflowRequest(BaseModel):
    module_name: str = Field(..., min_length=1)
    workflow_data: WorkflowData


class StartWorkflowRequest(BaseModel):
    module_name: str = Field(..., min_length=1)
    workflow_id: str = Field(..., min_length=1)


class ModuleItem(BaseModel):
    """设备（历史命名：Module）在前端展示所需字段"""

    id: int
    name: str
    simulator_index: int
    port: int
    is_running: bool
    execution_mode: Literal["plugin", "workflow"] = "plugin"
    current_plugin: Optional[str] = None
    running_workflow_id: Optional[str] = None
    current_workflow_id: Optional[str] = None
    workflow_enabled: bool = False


class ModuleListResponse(BaseModel):
    modules: List[ModuleItem]


class DeviceListResponse(BaseModel):
    devices: List[ModuleItem]


class PluginItem(BaseModel):
    id: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    author: str = "Unknown"


class PluginListResponse(BaseModel):
    plugins: List[PluginItem]


class DeviceCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    simulator_index: int
    port: int


class DeviceUpdateRequest(BaseModel):
    device_id: int = Field(..., ge=1)
    name: str = Field(..., min_length=1)
    simulator_index: int
    port: int


class DeviceDeleteRequest(BaseModel):
    device_id: int = Field(..., ge=1)


class WorkflowSummary(BaseModel):
    workflow_id: str
    name: str
    description: Optional[str] = None
    module_name: str
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class WorkflowListResponse(BaseModel):
    workflows: List[WorkflowSummary]


class DeleteWorkflowRequest(BaseModel):
    workflow_id: str = Field(..., min_length=1)


class SetCurrentWorkflowRequest(BaseModel):
    device_id: int = Field(..., ge=1)
    workflow_id: Optional[str] = None


class StopWorkflowRequest(BaseModel):
    module_name: str = Field(..., min_length=1)


WorkflowStatus = Literal["running", "completed", "failed"]


class NodeStatusUpdate(BaseModel):
    module_name: str
    workflow_id: str
    node_id: str
    status: WorkflowStatus
    error: Optional[str] = None


class PluginConfigGetRequest(BaseModel):
    device_name: str = Field(..., min_length=1)
    plugin_id: str = Field(..., min_length=1)


class PluginConfigUpdateRequest(BaseModel):
    device_name: str = Field(..., min_length=1)
    plugin_id: str = Field(..., min_length=1)
    config: Dict[str, Any]


class LogEntry(BaseModel):
    module: str
    level: str
    message: str
    timestamp: float


class ConfigResponse(BaseModel):
    dark_mode: bool = True
    cap_tool: str = "MuMu"
    touch_tool: str = "MaaTouch"
    email: Optional[str] = None
    password: Optional[str] = None
    receiver: Optional[str] = None


class ConfigUpdateRequest(BaseModel):
    dark_mode: Optional[bool] = None
    cap_tool: Optional[str] = None
    touch_tool: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    receiver: Optional[str] = None
