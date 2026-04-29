/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_WS_URL?: string;
  readonly VITE_FASTAPI_URL?: string;
  readonly VITE_FASTAPI_WS_URL?: string;
}

interface Window {
  ipcRenderer: {
    send: (channel: string, data?: any) => void;
    on: (channel: string, func: (...args: any[]) => void) => void;
    minimize: () => void;
    maximize: () => void;
    close: () => void;
  }
}
