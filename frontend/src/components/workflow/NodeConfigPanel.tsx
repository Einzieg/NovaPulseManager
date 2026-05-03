import React, { useEffect, useState } from 'react';
import { X, Settings2, Save, Trash2, AlertCircle } from 'lucide-react';
import { clsx } from 'clsx';
import { Node } from 'reactflow';
import { toast } from 'sonner';

interface NodeConfigPanelProps {
  node: Node | null;
  deviceName: string;
  onClose: () => void;
  onDelete: (nodeId: string) => void;
  onUpdateConfig: (nodeId: string, config: Record<string, any>) => void;
}

const NodeConfigPanel: React.FC<NodeConfigPanelProps> = ({
  node,
  deviceName,
  onClose,
  onDelete,
  onUpdateConfig,
}) => {
  const [configText, setConfigText] = useState('{}');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!node) return;
    setConfigText(JSON.stringify(node.data.config || {}, null, 2));
    setError(null);
  }, [node?.id, node?.data.config]);

  if (!node) return null;

  const handleSave = () => {
    try {
      const parsed = configText.trim() ? JSON.parse(configText) : {};
      if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') {
        throw new Error('Config must be a JSON object');
      }
      onUpdateConfig(node.id, parsed);
      setError(null);
      toast.success('节点配置已更新');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'JSON 格式错误';
      setError(message);
      toast.error('配置格式错误', { description: message });
    }
  };

  const rows = [
    ['Device', `${deviceName}${node.data.device_id ? ` (#${node.data.device_id})` : ''}`],
    ['App', node.data.app_id || '-'],
    ['Module', node.data.module_id || '-'],
    ['Action', node.data.action_id || '-'],
    ['Action Ref', node.data.action_ref || node.data.plugin_id || '-'],
  ];

  return (
    <aside
      className={clsx(
        'absolute top-6 right-6 bottom-6 w-[400px] z-50 flex flex-col',
        'bg-ios-surface/40 backdrop-blur-[60px] rounded-[48px]',
        'border border-white/60 shadow-[0_32px_64px_-16px_rgba(0,0,0,0.12)]',
        'transition-all duration-500 ease-[cubic-bezier(0.23,1,0.32,1)]',
        'animate-in slide-in-from-right-12 fade-in'
      )}
    >
      <div className="p-8 pb-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-[20px] bg-ios-surface shadow-[0_8px_16px_-4px_rgba(0,0,0,0.05)] flex items-center justify-center border border-white/80">
            <Settings2 size={22} className="text-gray-900" />
          </div>
          <div>
            <h3 className="text-base font-extrabold tracking-tight text-gray-900 leading-none mb-1.5">
              NODE CONFIG
            </h3>
            <p className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">
              {node.data.action_ref || node.data.plugin_id}
            </p>
          </div>
        </div>
        <button onClick={onClose} className="p-3 rounded-full hover:bg-ios-surface/60 transition-colors active:scale-90">
          <X size={20} className="text-gray-400" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-8 space-y-5 custom-scrollbar">
        <section className="space-y-2">
          {rows.map(([label, value]) => (
            <div key={label} className="rounded-2xl bg-gray-100/40 px-4 py-3">
              <div className="text-[9px] font-black uppercase tracking-widest text-gray-400">{label}</div>
              <div className="mt-1 break-all text-xs font-bold text-gray-900">{value}</div>
            </div>
          ))}
        </section>

        <section>
          <label className="mb-2 block text-[10px] font-black uppercase tracking-widest text-gray-400">
            Node config JSON
          </label>
          <textarea
            value={configText}
            onChange={(e) => setConfigText(e.target.value)}
            spellCheck={false}
            className={clsx(
              'h-56 w-full resize-none rounded-2xl border-none bg-gray-100/50 p-4 font-mono text-xs text-gray-900',
              'shadow-[inset_0_2px_4px_rgba(0,0,0,0.03)] outline-none focus:ring-2 focus:ring-gray-900/5'
            )}
          />
          {error && (
            <div className="mt-3 flex items-center gap-2 rounded-2xl bg-rose-50 p-3 text-xs text-rose-500">
              <AlertCircle size={14} />
              <span>{error}</span>
            </div>
          )}
        </section>
      </div>

      <div className="p-8 mt-auto">
        <div className="flex gap-3">
          <button
            onClick={() => onDelete(node.id)}
            className={clsx(
              'flex-1 flex items-center justify-center gap-2 py-4 rounded-[24px] font-bold text-[10px] tracking-widest transition-all',
              'bg-rose-50 text-rose-500 border border-rose-100 hover:bg-rose-100 active:scale-95'
            )}
          >
            <Trash2 size={14} />
            <span>删除节点</span>
          </button>
          <button
            onClick={handleSave}
            className={clsx(
              'flex-1 flex items-center justify-center gap-2 py-4 rounded-[24px] font-bold text-[10px] tracking-widest transition-all',
              'bg-ios-accent text-ios-on-accent shadow-[0_16px_32px_-8px_rgba(0,0,0,0.3)] hover:opacity-90 active:scale-95'
            )}
          >
            <Save size={14} />
            <span>保存</span>
          </button>
        </div>
      </div>
    </aside>
  );
};

export default NodeConfigPanel;
