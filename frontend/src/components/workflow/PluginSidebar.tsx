import React, { useState, useEffect } from 'react';
import { Search, Puzzle, ChevronRight, Info, Loader2 } from 'lucide-react';
import { clsx } from 'clsx';
import websocketService from '../../services/websocket';
import type { AppItem } from '../../api/apps';
import type { ActionItem } from '../../api/actions';

const PluginSidebar: React.FC = () => {
  const [apps, setApps] = useState<AppItem[]>([]);
  const [actions, setActions] = useState<ActionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const fetchActions = async () => {
      try {
        setLoading(true);
        const [appsData, actionsData] = await Promise.all([
          websocketService.getAppList(),
          websocketService.getActionList(),
        ]);
        setApps(Array.isArray(appsData?.apps) ? appsData.apps : []);
        setActions(Array.isArray(actionsData?.actions) ? actionsData.actions : []);
      } catch (error) {
        console.error('Failed to fetch actions:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchActions();
  }, []);

  const onDragStart = (event: React.DragEvent, action: ActionItem) => {
    event.dataTransfer.setData('application/reactflow', JSON.stringify(action));
    event.dataTransfer.effectAllowed = 'move';
  };

  const normalizedQuery = searchQuery.toLowerCase();
  const filteredActions = actions.filter((action) => {
    const haystack = [
      action.name,
      action.action_ref,
      action.app_id,
      action.module_id,
      action.action_id,
    ].join(' ').toLowerCase();
    return haystack.includes(normalizedQuery);
  });
  const appNameById = new Map(apps.map((app) => [app.id, app.name]));
  const groupedActions = filteredActions.reduce<Record<string, ActionItem[]>>((acc, action) => {
    const key = `${action.app_id}/${action.module_id}`;
    acc[key] = acc[key] || [];
    acc[key].push(action);
    return acc;
  }, {});

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
            <h3 className="text-base font-extrabold tracking-tight text-gray-900 leading-none mb-1.5">Action 库</h3>
            <p className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">APP / MODULE</p>
          </div>
        </div>

        {/* Search Box - 精密喷砂质感 */}
        <div className="relative group">
          <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
            <Search size={14} className="text-gray-400 group-focus-within:text-gray-900 transition-colors" />
          </div>
          <input
            type="text"
            placeholder="搜索 Action..."
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
            <span className="text-[10px] font-bold uppercase tracking-widest">Loading Actions</span>
          </div>
        ) : filteredActions.length > 0 ? (
          Object.entries(groupedActions).map(([group, groupActions]) => {
            const [appId, moduleId] = group.split('/');
            return (
              <div key={group} className="space-y-2">
                <div className="px-2">
                  <p className="text-[10px] font-black text-gray-500 uppercase tracking-[0.18em]">
                    {appNameById.get(appId) || appId}
                  </p>
                  <p className="text-[9px] font-bold text-gray-400 uppercase tracking-widest">
                    {moduleId}
                  </p>
                </div>
                {groupActions.map((action) => (
                  <div
                    key={action.action_ref}
                    draggable
                    onDragStart={(e) => onDragStart(e, action)}
                    className={clsx(
                      "group relative p-5 rounded-[32px] bg-ios-surface/40 border border-white/60 cursor-grab active:cursor-grabbing",
                      "hover:bg-ios-surface/80 hover:shadow-[0_20px_40px_-12px_rgba(0,0,0,0.08)] hover:scale-[1.02]",
                      "transition-all duration-500 ease-[cubic-bezier(0.23,1,0.32,1)] active:scale-[0.98]",
                      "overflow-hidden"
                    )}
                  >
                    <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/80 to-transparent" />
                    <div className="flex items-start justify-between mb-2">
                      <span className="text-[9px] font-black text-gray-400 uppercase tracking-[0.15em] bg-gray-100/50 px-2 py-0.5 rounded-full">
                        {action.action_ref}
                      </span>
                      <ChevronRight size={12} className="text-gray-300 group-hover:text-gray-900 group-hover:translate-x-0.5 transition-all" />
                    </div>
                    <h4 className="text-sm font-bold text-gray-900 mb-1.5 tracking-tight">{action.name}</h4>
                    <p className="text-[11px] text-gray-500 leading-relaxed line-clamp-2 font-medium">
                      {action.description}
                    </p>
                    <div className="absolute inset-0 rounded-[32px] border border-gray-200/10 pointer-events-none" />
                  </div>
                ))}
              </div>
            );
          })
        ) : (
          <div className="h-40 flex flex-col items-center justify-center text-center px-4">
            <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">找不到可用 Action</p>
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
