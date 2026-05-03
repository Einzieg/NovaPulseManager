import { get, post, patch, del } from './client';

export function listDevices() {
  return get('/api/v1/devices');
}

export function createDevice(payload: { name: string; simulator_index: number; port: number }) {
  return post('/api/v1/devices', payload);
}

export function updateDevice(payload: { device_id: number; name: string; simulator_index: number; port: number }) {
  return patch(`/api/v1/devices/${payload.device_id}`, payload);
}

export function deleteDevice(payload: { device_id: number }) {
  return del(`/api/v1/devices/${payload.device_id}`);
}
