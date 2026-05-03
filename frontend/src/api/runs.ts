import { get, post } from './client';

export function startRun(workflowId: string) {
  return post(`/api/v1/workflows/${encodeURIComponent(workflowId)}/runs`);
}

export function getRun(runId: string) {
  return get(`/api/v1/runs/${encodeURIComponent(runId)}`);
}

export function cancelRun(runId: string) {
  return post(`/api/v1/runs/${encodeURIComponent(runId)}/cancel`);
}

export function listRuns() {
  return get('/api/v1/runs');
}
