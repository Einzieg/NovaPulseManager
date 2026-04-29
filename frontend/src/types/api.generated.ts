/* eslint-disable */
// This file is generated from backend/core/api/schemas.py
// Run: python scripts/generate_frontend_types.py

export type WorkflowStatus = 'running' | 'completed' | 'failed';

export interface DeleteWorkflowRequest {
  workflow_id: string;
}

export interface DeviceCreateRequest {
  name: string;
  simulator_index: number;
  port: number;
}

export interface DeviceDeleteRequest {
  device_id: number;
}

export interface DeviceListResponse {
  devices: ModuleItem[];
}

export interface DeviceUpdateRequest {
  device_id: number;
  name: string;
  simulator_index: number;
  port: number;
}

export interface LogEntry {
  module: string;
  level: string;
  message: string;
  timestamp: number;
}

export interface ModuleItem {
  id: number;
  name: string;
  simulator_index: number;
  port: number;
  is_running: boolean;
  execution_mode?: 'plugin' | 'workflow';
  current_plugin?: string | null;
  running_workflow_id?: string | null;
  current_workflow_id?: string | null;
  workflow_enabled?: boolean;
}

export interface ModuleListResponse {
  modules: ModuleItem[];
}

export interface NodeStatusUpdate {
  module_name: string;
  workflow_id: string;
  node_id: string;
  status: 'running' | 'completed' | 'failed';
  error?: string | null;
}

export interface PluginItem {
  id: string;
  name: string;
  description?: string;
  version?: string;
  author?: string;
}

export interface PluginListResponse {
  plugins: PluginItem[];
}

export interface SaveWorkflowRequest {
  module_name: string;
  workflow_data: WorkflowData;
}

export interface SetCurrentWorkflowRequest {
  device_id: number;
  workflow_id?: string | null;
}

export interface StartTaskRequest {
  module_name: string;
  plugin_id: string;
}

export interface StartWorkflowRequest {
  module_name: string;
  workflow_id: string;
}

export interface StopTaskRequest {
  module_name: string;
}

export interface StopWorkflowRequest {
  module_name: string;
}

export interface WorkflowData {
  id: string;
  name?: string;
  module_name?: string | null;
  description?: string | null;
  nodes?: WorkflowNode[];
  edges?: WorkflowEdge[];
  created_at?: string | null;
  updated_at?: string | null;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
}

export interface WorkflowListResponse {
  workflows: WorkflowSummary[];
}

export interface WorkflowNode {
  id: string;
  plugin_id: string;
  position: WorkflowPosition;
  config?: Record<string, any>;
}

export interface WorkflowPosition {
  x: number;
  y: number;
}

export interface WorkflowSummary {
  workflow_id: string;
  name: string;
  description?: string | null;
  module_name: string;
  is_active?: boolean;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ConfigData {
  dark_mode: boolean;
  cap_tool: string;
  touch_tool: string;
  email: string | null;
  password: string | null;
  receiver: string | null;
}

export interface ConfigUpdateRequest {
  dark_mode?: boolean;
  cap_tool?: string;
  touch_tool?: string;
  email?: string | null;
  password?: string | null;
  receiver?: string | null;
}
