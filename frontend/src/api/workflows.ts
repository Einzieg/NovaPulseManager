import { get, post, del } from './client';

export function saveWorkflow(moduleName: string, workflowData: any) {
  return post('/api/v1/workflows', { module_name: moduleName, workflow_data: workflowData });
}

export function loadWorkflow(moduleName: string) {
  return get(`/api/v1/workflows/load?module_name=${encodeURIComponent(moduleName)}`);
}

export function listWorkflows(moduleName: string) {
  return get(`/api/v1/workflows?module_name=${encodeURIComponent(moduleName)}`);
}

export function getWorkflow(workflowId: string) {
  return get(`/api/v1/workflows/${encodeURIComponent(workflowId)}`);
}

export function deleteWorkflow(workflowId: string) {
  return del(`/api/v1/workflows/${encodeURIComponent(workflowId)}`);
}

export function setCurrentWorkflow(deviceId: number, workflowId: string | null) {
  return post('/api/v1/workflows/set-current', {
    device_id: deviceId,
    workflow_id: workflowId,
  });
}

export function startWorkflow(moduleName: string, workflowId: string) {
  return post('/api/v1/workflows/start', { module_name: moduleName, workflow_id: workflowId });
}

export function stopWorkflow(moduleName: string) {
  return post('/api/v1/workflows/stop', { module_name: moduleName });
}
