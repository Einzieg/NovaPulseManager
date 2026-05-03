import { get } from './client';

export interface AppItem {
  id: string;
  name: string;
  version: string;
  package_name?: string | null;
}

export function listApps(): Promise<{ apps: AppItem[] }> {
  return get('/api/v1/apps');
}
