const apiFromEnv = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_FASTAPI_URL;
export const API_BASE_URL = (apiFromEnv || 'http://127.0.0.1:8765').replace(/\/+$/, '');

async function parseJsonOrText(res: Response): Promise<any> {
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

async function request(path: string, init?: RequestInit): Promise<any> {
  const res = await fetch(`${API_BASE_URL}${path}`, init);
  const data = await parseJsonOrText(res);
  if (!res.ok) {
    throw new Error(typeof data === 'string' ? data : JSON.stringify(data));
  }
  return data;
}

export function get(path: string, init?: RequestInit): Promise<any> {
  return request(path, init);
}

export function post(path: string, body?: any): Promise<any> {
  return request(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body ?? {}),
  });
}

export function patch(path: string, body?: any): Promise<any> {
  return request(path, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body ?? {}),
  });
}

export function del(path: string): Promise<any> {
  return request(path, { method: 'DELETE' });
}
