import React, { useState, useEffect } from 'react';
import Sidebar from './components/layout/Sidebar';
import DevicesPage from './pages/DevicesPage';
import WorkflowEditor from './components/workflow/WorkflowEditor';
import { Settings, Terminal } from 'lucide-react';
import { Toaster } from 'sonner';
import websocketService from './services/websocket';
import SettingsPanel from './components/settings/SettingsPanel';

function App() {
  const [activeTab, setActiveTab] = useState('devices');
  const [backendStatus, setBackendStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');
  const [settingsOpen, setSettingsOpen] = useState(false);

  useEffect(() => {
    // Sync theme from localStorage first (prevents FOUC), then reconcile with backend
    const cached = localStorage.getItem('dark_mode');
    if (cached === 'true') document.documentElement.classList.add('dark');

    websocketService.connect();
    websocketService.getConfig().then((cfg) => {
      const dark = !!cfg?.dark_mode;
      document.documentElement.classList.toggle('dark', dark);
      localStorage.setItem('dark_mode', String(dark));
    }).catch(() => {});
    return () => websocketService.disconnect();
  }, []);

  useEffect(() => {
    let cancelled = false;
    let inFlight = false;

    const check = async () => {
      if (inFlight) {
        return;
      }
      inFlight = true;
      try {
        const ok = await websocketService.checkHealth();
        if (cancelled) {
          return;
        }
        setBackendStatus(ok ? 'connected' : 'disconnected');
        if (ok) {
          websocketService.connect();
        }
      } finally {
        inFlight = false;
      }
    };

    check();
    const interval = window.setInterval(check, 2000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, []);

  return (
    <div className="flex h-screen w-full overflow-hidden bg-ios-bg p-6 font-sans text-ios-black selection:bg-ios-accent selection:text-ios-on-accent">
      <Toaster
        position="top-center"
        toastOptions={{
          className: 'rounded-2xl border border-white/60 bg-ios-surface/80 backdrop-blur-xl shadow-2xl font-sans font-bold text-ios-black',
        }}
      />
      
      {/* 侧边栏：左侧固定，高斯模糊 */}
      <aside className="relative z-20 h-full w-72 shrink-0">
        <Sidebar activeTab={activeTab} backendStatus={backendStatus} onTabChange={setActiveTab} />
      </aside>

      {/* 主内容区：右侧滚动，头部固定 */}
      <main className="relative flex flex-1 flex-col overflow-hidden pl-8 pt-2">
        
        {/* Header: 标题与全局操作 */}
        <header className="mb-8 flex shrink-0 items-end justify-between pr-4">
          <div>
            <h2 className="text-4xl font-[800] tracking-tight italic text-ios-black">
              {activeTab === 'devices' ? '设备管理' :
               activeTab === 'workflows' ? '工作流程设计' : 'Marketplace'}
            </h2>
            <div className="mt-2 h-1.5 w-16 rounded-full bg-ios-accent" />
          </div>

          <div className="flex gap-4">
            <HeaderButton icon={<Terminal size={20} />} />
            <HeaderButton icon={<Settings size={20} />} onClick={() => setSettingsOpen(true)} />
          </div>
        </header>

        {/* 滚动视窗 */}
        <div className="custom-scrollbar h-full overflow-y-auto">
          {activeTab === 'devices' && <DevicesPage />}
          {activeTab === 'plugins' && (
            <div className="flex h-64 items-center justify-center rounded-[32px] border border-white/60 bg-ios-surface/40 font-bold text-ios-gray backdrop-blur-md">
              PLUGIN MANAGER COMING SOON
            </div>
          )}
          {activeTab === 'market' && (
            <div className="flex h-64 items-center justify-center rounded-ios-md border border-black/5 bg-ios-surface/50 font-bold text-ios-gray">
              MARKETPLACE COMING SOON
            </div>
          )}
        </div>
      </main>

      <SettingsPanel isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  );
}

const HeaderButton = ({ icon, onClick }: { icon: React.ReactNode; onClick?: () => void }) => (
  <button
    onClick={onClick}
    className="flex h-12 w-12 items-center justify-center rounded-2xl border border-white/60 bg-ios-surface/40 text-ios-black shadow-sm backdrop-blur-md transition-transform active:scale-95 hover:bg-ios-surface/60"
  >
    {icon}
  </button>
);

export default App;
