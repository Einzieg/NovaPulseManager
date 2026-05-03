import { get } from './client';

export interface ActionItem {
  app_id: string;
  module_id: string;
  action_id: string;
  action_ref: string;
  name: string;
  description: string;
}

export function listActions(params?: { app_id?: string; module_id?: string }): Promise<{ actions: ActionItem[] }> {
  const qs = new URLSearchParams();
  if (params?.app_id) qs.set('app_id', params.app_id);
  if (params?.module_id) qs.set('module_id', params.module_id);
  const suffix = qs.toString() ? `?${qs.toString()}` : '';
  return get(`/api/v1/actions${suffix}`);
}
