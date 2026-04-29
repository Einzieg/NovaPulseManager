/**
 * 工作流系统TypeScript类型定义
 * 严格遵循docs/workflow-visualization-design.md规范
 */

export interface WorkflowNode {
  id: string;
  plugin_id: string;
  position: { x: number; y: number };
  config?: Record<string, any>;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
}

export interface WorkflowData {
  id: string;
  name: string;
  description?: string;
  module_name: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  created_at?: string;
  updated_at?: string;
}

export type WorkflowStatus = 'running' | 'completed' | 'failed';

export interface NodeStatusUpdate {
  module_name: string;
  workflow_id: string;
  node_id: string;
  status: WorkflowStatus;
  error?: string;
}