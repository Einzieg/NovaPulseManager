import React, { useState, useEffect } from 'react';
import { Search, Puzzle, ChevronRight, Info, Loader2 } from 'lucide-react';
import { clsx } from 'clsx';
import websocketService from '../../services/websocket';

interface Plugin {
  id: string;
  name: string;
  description: string;
  category?: string;
  version?: string;
  author?: string;
}

const PluginSidebar: React.FC = () => {
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const fetchPlugins = async () => {
      try {
        setLoading(true);
        const data = await websocketService.getPluginList();
        const pluginList = Array.isArray(data?.plugins) ? data.plugins : (Array.isArray(data) ? data : []);
        setPlugins(pluginList);
      } catch (error) {
        console.error('Failed to fetch plugins:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPlugins();
  }, []);

  const onDragStart = (event: React.DragEvent, plugin: Plugin) => {
    event.dataTransfer.setData('application/reactflow', JSON.stringify(plugin));
    event.dataTransfer.effectAllowed = 'move';
  };

  const normalizedQuery = searchQuery.toLowerCase();
  const filteredPlugins = plugins.filter((plugin) => {
    const name = (plugin.name ?? '').toLowerCase();
    const id = (plugin.id ?? '').toLowerCase();
    return name.includes(normalizedQuery) || id.includes(normalizedQuery);
  });

  return (
    <aside className="w-80 h-full bg-ios-bg/90 backdrop-blur-[60px] border-r border-gray-200/40 flex flex-col shadow-[4px_0_32px_rgba(0,0,0,0.04)] z-10">
      {/* Header */}
      <div className="p-8 pb-6">
        <div className="flex items-center gap-4 mb-8">
          <div className="w-12 h-12 rounded-[20px] bg-ios-surface shadow-[0_8px_16px_-4px_rgba(0,0,0,0.05)] flex items-center justify-center border border-white/80 relative overflow-hidden group">
            <div className="absolute inset-0 bg-gradient-to-br from-gray-50 to-transparent opacity-50" />
            <Puzzle size={22} className="text-gray-900 relative z-10" />
          </div>
          <div>
            <h3 className="text-base font-extrabold tracking-tight text-gray-900 leading-none mb-1.5">流程库</h3>
            <p className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">组件</p>
          </div>
        </div>

        {/* Search Box - 精密喷砂质感 */}
        <div className="relative group">
          <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
            <Search size={14} className="text-gray-400 group-focus-within:text-gray-900 transition-colors" />
          </div>
          <input
            type="text"
            placeholder="搜索流程..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className={clsx(
              "w-full bg-gray-200/30 border-none rounded-2xl py-3.5 pl-11 pr-4 text-sm font-medium",
              "placeholder:text-gray-400 focus:ring-2 focus:ring-gray-900/5 transition-all outline-none",
              "shadow-[inset_0_2px_4px_rgba(0,0,0,0.03)]" // 营造凹陷感
            )}
          />
        </div>
      </div>

      {/* Plugin List */}
      <div className="flex-1 overflow-y-auto px-6 pb-6 space-y-4 custom-scrollbar">
        {loading ? (
          <div className="h-40 flex flex-col items-center justify-center gap-3 text-gray-400">
            <Loader2 size={20} className="animate-spin" />
            <span className="text-[10px] font-bold uppercase tracking-widest">Loading Plugins</span>
          </div>
        ) : filteredPlugins.length > 0 ? (
          filteredPlugins.map((plugin) => (
            <div
              key={plugin.id}
              draggable
              onDragStart={(e) => onDragStart(e, plugin)}
              className={clsx(
                "group relative p-5 rounded-[32px] bg-ios-surface/40 border border-white/60 cursor-grab active:cursor-grabbing",
                "hover:bg-ios-surface/80 hover:shadow-[0_20px_40px_-12px_rgba(0,0,0,0.08)] hover:scale-[1.02]",
                "transition-all duration-500 ease-[cubic-bezier(0.23,1,0.32,1)] active:scale-[0.98]",
                "overflow-hidden"
              )}
            >
              {/* Glass Highlight */}
              <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/80 to-transparent" />
              
              <div className="flex items-start justify-between mb-2">
                <span className="text-[9px] font-black text-gray-400 uppercase tracking-[0.15em] bg-gray-100/50 px-2 py-0.5 rounded-full">
                  {plugin.category ?? plugin.version ?? 'PLUGIN'}
                </span>
                <ChevronRight size={12} className="text-gray-300 group-hover:text-gray-900 group-hover:translate-x-0.5 transition-all" />
              </div>
              <h4 className="text-sm font-bold text-gray-900 mb-1.5 tracking-tight">{plugin.name}</h4>
              <p className="text-[11px] text-gray-500 leading-relaxed line-clamp-2 font-medium">
                {plugin.description}
              </p>
              
              {/* 物理描边增强 */}
              <div className="absolute inset-0 rounded-[32px] border border-gray-200/10 pointer-events-none" />
            </div>
          ))
        ) : (
          <div className="h-40 flex flex-col items-center justify-center text-center px-4">
            <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">找不到可用流程</p>
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className="p-6 border-t border-gray-200/40 bg-ios-surface/20">
        <div className="flex items-center gap-3 text-gray-400">
          <Info size={14} />
          <span className="text-[10px] font-bold uppercase tracking-widest">拖曳以添加节点</span>
        </div>
      </div>
    </aside>
  );
};

export default PluginSidebar;
