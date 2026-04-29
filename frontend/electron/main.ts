import { app, BrowserWindow, shell, ipcMain } from 'electron'
import * as path from 'path'

// 屏蔽 Windows 7 的 GPU 加速以防黑屏（可选）
if (process.platform === 'win32') app.commandLine.appendSwitch('disable-color-correction')

let win: BrowserWindow | null = null

function createWindow() {
  win = new BrowserWindow({
    width: 1280,
    height: 860,
    minWidth: 1024,
    minHeight: 768,
    // 核心视觉配置 ------------------------
    frame: true,             // 恢复原生标题栏
    transparent: false,      // 恢复原生标题栏时通常需要关闭透明以保证标题栏渲染正常
    hasShadow: true,         // 开启窗口阴影 (MacOS)
    vibrancy: 'under-window',// MacOS 专用的高斯模糊特效
    visualEffectState: 'active', // 保持模糊即使窗口未激活 (MacOS)
    backgroundColor: '#00000000', // 确保背景完全透明
    // -----------------------------------
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false, // 开发阶段如有跨域需求可暂时关闭
    },
  })

  // 移除默认菜单栏 (File, Edit, View 等)
  win.setMenu(null)

  // 开发环境加载 localhost，生产环境加载打包后的 index.html
  if (process.env.VITE_DEV_SERVER_URL) {
    win.loadURL(process.env.VITE_DEV_SERVER_URL)
    win.webContents.openDevTools() // 开发时打开控制台
  } else {
    win.loadFile(path.join(__dirname, '../dist/index.html'))
  }

  // 修复窗口闪烁
  win.once('ready-to-show', () => {
    win?.show()
  })
  
  // 处理外部链接用浏览器打开
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('https:')) shell.openExternal(url)
    return { action: 'deny' }
  })
}

app.whenReady().then(createWindow)

app.on('window-all-closed', () => {
  win = null
  if (process.platform !== 'darwin') app.quit()
})

// IPC 通信示例：处理最小化/关闭按钮
ipcMain.on('window-min', () => win?.minimize())
ipcMain.on('window-close', () => win?.close())
ipcMain.on('window-max', () => {
  if (win?.isMaximized()) win.unmaximize()
  else win?.maximize()
})