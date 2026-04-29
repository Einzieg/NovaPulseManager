import React from 'react';
import { motion } from 'framer-motion';
import { LayoutGrid, Puzzle, ShoppingCart, Activity, GitBranch } from 'lucide-react';
import { clsx } from 'clsx';

const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;

interface SidebarProps {
  activeTab: string;
  backendStatus: 'checking' | 'connected' | 'disconnected';
  onTabChange: (tab: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ activeTab, backendStatus, onTabChange }) => {
  const statusConfig =
    backendStatus === 'connected'
      ? { dot: 'bg-green-500', ping: 'bg-green-400', text: '在线', showPing: true }
      : backendStatus === 'disconnected'
        ? { dot: 'bg-rose-500', ping: 'bg-rose-400', text: '离线', showPing: false }
        : { dot: 'bg-amber-500', ping: 'bg-amber-400', text: '检测中', showPing: true };

  return (
    <div className="flex h-full flex-col rounded-ios border border-white/60 bg-ios-surface/40 shadow-glass backdrop-blur-zen">
      {/* Logo Area */}
      <div className="mb-10 px-8 pt-10">
        <h1 className="text-2xl font-[900] italic tracking-tighter text-ios-black">
          NOVA PULSE
        </h1>
        <p className="mt-1 text-[10px] font-bold uppercase tracking-[0.25em] text-ios-gray opacity-60">
          Manager v2.0
        </p>
      </div>

      {/* Navigation Items */}
      <nav className="flex-1 space-y-3 px-4">
        <NavItem
          id="devices"
          label="设备集群"
          icon={<LayoutGrid size={20} />}
          active={activeTab === 'devices'}
          onClick={() => onTabChange('devices')}
        />
        <NavItem
          id="plugins"
          label="插件管理"
          icon={<Puzzle size={20} />}
          active={activeTab === 'plugins'}
          onClick={() => onTabChange('plugins')}
        />
        <NavItem 
          id="market" 
          label="任务市场" 
          icon={<ShoppingCart size={20} />} 
          active={activeTab === 'market'} 
          onClick={() => onTabChange('market')} 
        />
      </nav>

      {/* Backend Status Footer */}
      <div className="p-4">
        <div className="flex items-center gap-3 rounded-ios-md border border-black/5 bg-ios-black/5 px-5 py-4">
          <div className="relative flex h-3 w-3">
            {statusConfig.showPing && (
              <span
                className={`absolute inline-flex h-full w-full animate-ping rounded-full ${statusConfig.ping} opacity-75`}
              />
            )}
            <span className={`relative inline-flex h-3 w-3 rounded-full ${statusConfig.dot}`} />
          </div>
          <div>
             <div className="text-[10px] font-bold uppercase tracking-widest text-ios-black/60">服务</div>
             <div className="text-xs font-bold text-ios-black">{statusConfig.text}</div>
          </div>
        </div>
      </div>
    </div>
  );
};

const NavItem = ({ id, label, icon, active, onClick }: any) => (
  <motion.button
    whileTap={{ scale: 0.96 }}
    onClick={onClick}
    className={clsx(
      "group relative flex w-full items-center gap-4 rounded-[28px] px-6 py-4 transition-all duration-300",
      active 
        ? "bg-ios-accent text-ios-on-accent shadow-lg"
        : "text-ios-black/60 hover:bg-ios-surface/50 hover:text-ios-black"
    )}
  >
    {icon}
    <span className="text-sm font-bold tracking-tight">{label}</span>
    {active && (
      <motion.div 
        layoutId="active-dot"
        className="ml-auto h-1.5 w-1.5 rounded-full bg-ios-on-accent"
      />
    )}
  </motion.button>
);


export default Sidebar;
