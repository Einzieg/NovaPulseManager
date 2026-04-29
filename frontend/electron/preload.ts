import { contextBridge, ipcRenderer } from 'electron'

// 暴露给前端 window 对象的 API
contextBridge.exposeInMainWorld('ipcRenderer', {
  send: (channel: string, data: any) => ipcRenderer.send(channel, data),
  on: (channel: string, func: any) => 
    ipcRenderer.on(channel, (event, ...args) => func(...args)),
  // 专门用于窗口控制
  minimize: () => ipcRenderer.send('window-min'),
  maximize: () => ipcRenderer.send('window-max'),
  close: () => ipcRenderer.send('window-close'),
})