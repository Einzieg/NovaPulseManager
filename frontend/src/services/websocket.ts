type AnyCallback = (data: any) => void;

class WebSocketService {
  private ws: WebSocket | null = null;

  private nodeStatusCallbacks: AnyCallback[] = [];

  private readonly apiBaseUrl: string;
  private readonly wsUrl: string;

  constructor() {
    const apiFromEnv = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_FASTAPI_URL;
    this.apiBaseUrl = (apiFromEnv || 'http://127.0.0.1:8765').replace(/\/+$/, '');

    const wsFromEnv = import.meta.env.VITE_WS_URL || import.meta.env.VITE_FASTAPI_WS_URL;
    this.wsUrl = (wsFromEnv || this.deriveWsUrl(this.apiBaseUrl)).replace(/\/+$/, '');
  }

  connect() {
    if (this.ws) {
      return;
    }

    const ws = new WebSocket(this.wsUrl);
    this.ws = ws;

    ws.addEventListener('open', () => {
      console.log('WebSocket connected');
    });

    ws.addEventListener('close', () => {
      if (this.ws === ws) {
        this.ws = null;
      }
    });

    ws.addEventListener('error', (error) => {
      console.error('WebSocket error:', error);
    });

    ws.addEventListener('message', (event) => {
      try {
        const msg = JSON.parse(event.data);
        this.handleWsMessage(msg);
      } catch (e) {
        console.error('WebSocket message parse error:', e);
      }
    });
  }

  disconnect() {
    this.ws?.close();
    this.ws = null;
    this.nodeStatusCallbacks = [];
  }

  async checkHealth(timeoutMs = 1500): Promise<boolean> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);

    try {
      await this.httpGet('/api/v1/health', { signal: controller.signal });
      return true;
    } catch {
      return false;
    } finally {
      clearTimeout(timeout);
    }
  }

  private deriveWsUrl(apiBaseUrl: string): string {
    try {
      const url = new URL(apiBaseUrl);
      url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
      url.pathname = '/ws';
      url.search = '';
      url.hash = '';
      return url.toString();
    } catch {
      return 'ws://127.0.0.1:8765/ws';
    }
  }

  private handleWsMessage(msg: any) {
    const event = msg?.event;
    const data = msg?.data;

    if (event === 'log') {
      window.dispatchEvent(new CustomEvent('task-log', { detail: data }));
      return;
    }

    if (event === 'module.status') {
      window.dispatchEvent(new CustomEvent('module-status', { detail: data }));
      return;
    }

    if (event === 'workflow.node_status') {
      for (const cb of this.nodeStatusCallbacks) {
        cb(data);
      }
      return;
    }

    if (event === 'response') {
      console.log('Response:', data);
      return;
    }

    if (event === 'error') {
      console.error('WebSocket error:', data);
    }
  }

  private async httpGet(path: string, init?: RequestInit): Promise<any> {
    const res = await fetch(`${this.apiBaseUrl}${path}`, init);
    const data = await this.parseJsonOrText(res);
    if (!res.ok) {
      throw new Error(typeof data === 'string' ? data : JSON.stringify(data));
    }
    return data;
  }

  private async httpPost(path: string, body: any): Promise<any> {
    const res = await fetch(`${this.apiBaseUrl}${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body ?? {}),
    });
    const data = await this.parseJsonOrText(res);
    if (!res.ok) {
      throw new Error(typeof data === 'string' ? data : JSON.stringify(data));
    }
    return data;
  }

  private async parseJsonOrText(res: Response): Promise<any> {
    const text = await res.text();
    if (!text) {
      return null;
    }

    try {
      return JSON.parse(text);
    } catch {
      return text;
    }
  }

  async startTask(moduleName: string, pluginId: string) {
    return this.httpPost('/api/v1/tasks/start', { module_name: moduleName, plugin_id: pluginId });
  }

  async stopTask(moduleName: string) {
    return this.httpPost('/api/v1/tasks/stop', { module_name: moduleName });
  }

  async getModuleList() {
    return this.httpGet('/api/v1/modules');
  }

  async getPluginList() {
    return this.httpGet('/api/v1/plugins');
  }

  async getDeviceList() {
    return this.httpGet('/api/v1/devices');
  }

  async createDevice(payload: { name: string; simulator_index: number; port: number }) {
    return this.httpPost('/api/v1/devices/create', payload);
  }

  async updateDevice(payload: { device_id: number; name: string; simulator_index: number; port: number }) {
    return this.httpPost('/api/v1/devices/update', payload);
  }

  async deleteDevice(payload: { device_id: number }) {
    return this.httpPost('/api/v1/devices/delete', payload);
  }

  async saveWorkflow(moduleName: string, workflowData: any) {
    return this.httpPost('/api/v1/workflows/save', { module_name: moduleName, workflow_data: workflowData });
  }

  async loadWorkflow(moduleName: string) {
    return this.httpGet(`/api/v1/workflows/load?module_name=${encodeURIComponent(moduleName)}`);
  }

  async listWorkflows(moduleName: string) {
    return this.httpGet(`/api/v1/workflows/list?module_name=${encodeURIComponent(moduleName)}`);
  }

  async getWorkflow(workflowId: string, moduleName?: string) {
    const qs = new URLSearchParams({ workflow_id: workflowId });
    if (moduleName) {
      qs.set('module_name', moduleName);
    }
    return this.httpGet(`/api/v1/workflows/get?${qs.toString()}`);
  }

  async deleteWorkflow(workflowId: string) {
    return this.httpPost('/api/v1/workflows/delete', { workflow_id: workflowId });
  }

  async setCurrentWorkflow(deviceId: number, workflowId: string | null) {
    return this.httpPost('/api/v1/workflows/set-current', {
      device_id: deviceId,
      workflow_id: workflowId,
    });
  }

  async startWorkflow(moduleName: string, workflowId: string) {
    return this.httpPost('/api/v1/workflows/start', { module_name: moduleName, workflow_id: workflowId });
  }

  async stopWorkflow(moduleName: string) {
    return this.httpPost('/api/v1/workflows/stop', { module_name: moduleName });
  }

  async getPluginConfig(deviceName: string, pluginId: string) {
    return this.httpGet(
      `/api/v1/plugins/config?device_name=${encodeURIComponent(deviceName)}&plugin_id=${encodeURIComponent(pluginId)}`
    );
  }

  async updatePluginConfig(deviceName: string, pluginId: string, config: Record<string, any>) {
    return this.httpPost('/api/v1/plugins/config/update', {
      device_name: deviceName,
      plugin_id: pluginId,
      config,
    });
  }

  async getConfig() {
    return this.httpGet('/api/v1/config');
  }

  async updateConfig(payload: Record<string, any>) {
    return this.httpPost('/api/v1/config/update', payload);
  }

  onNodeStatus(callback: AnyCallback) {
    this.nodeStatusCallbacks.push(callback);
  }
}

export default new WebSocketService();
