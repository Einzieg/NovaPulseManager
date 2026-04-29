import React, { useState, useEffect, useCallback } from 'react';
import { X, Settings2, Save, Trash2, Loader2, AlertCircle, RefreshCw } from 'lucide-react';
import { clsx } from 'clsx';
import { Node } from 'reactflow';
import { toast } from 'sonner';
import websocketService from '../../services/websocket';

interface ConfigField {
  name: string;
  type: string;
  value: any;
  default: any;
}

const FIELD_LABELS: Record<string, string> = {
  normal_monster: '普通怪',
  elite_monster: '精英怪',
  red_monster: '红色怪',
  wreckage: '残骸',
  hidden_switch: '雷达开关',
  hidden_policy: '雷达策略',
  hidden_times: '雷达次数',
  hidden_wreckage: '雷达残骸',
  order_switch: '指令开关',
  order_policy: '指令策略',
  order_hasten_policy: '催促策略',
  order_speeduo_policy: '加速策略',
  order_times: '指令次数',
  autostart_simulator: '自动启动模拟器',
};

interface NodeConfigPanelProps {
  node: Node | null;
  deviceName: string;
  onClose: () => void;
  onDelete: (nodeId: string) => void;
}

const NodeConfigPanel: React.FC<NodeConfigPanelProps> = ({ node, deviceName, onClose, onDelete }) => {
  const [fields, setFields] = useState<ConfigField[]>([]);
  const [values, setValues] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadConfig = useCallback((pluginId: string, signal?: { cancelled: boolean }) => {
    setLoading(true);
    setError(null);
    websocketService
      .getPluginConfig(deviceName, pluginId)
      .then((res) => {
        if (signal?.cancelled) return;
        const list: ConfigField[] = res.fields || [];
        setFields(list);
        const init: Record<string, any> = {};
        for (const f of list) {
          init[f.name] = f.value;
        }
        setValues(init);
      })
      .catch((err) => {
        if (signal?.cancelled) return;
        console.error('Failed to load plugin config:', err);
        setFields([]);
        setError('加载配置失败');
      })
      .finally(() => {
        if (!signal?.cancelled) setLoading(false);
      });
  }, [deviceName]);

  useEffect(() => {
    if (!node) return;
    const pluginId = node.data.plugin_id;
    if (!pluginId || !deviceName) return;

    const signal = { cancelled: false };
    loadConfig(pluginId, signal);
    return () => { signal.cancelled = true; };
  }, [node?.id, node?.data.plugin_id, deviceName, loadConfig]);

  const handleChange = useCallback((name: string, value: any) => {
    setValues((prev) => ({ ...prev, [name]: value }));
  }, []);

  const handleSave = useCallback(async () => {
    if (!node) return;
    setSaving(true);
    try {
      await websocketService.updatePluginConfig(deviceName, node.data.plugin_id, values);
      toast.success('配置已保存');
    } catch (err) {
      console.error('Failed to save plugin config:', err);
      toast.error('保存失败');
    } finally {
      setSaving(false);
    }
  }, [node, deviceName, values]);

  if (!node) return null;

  const renderField = (field: ConfigField) => {
    const label = FIELD_LABELS[field.name] || field.name;
    const val = values[field.name];

    if (field.type === 'BooleanField') {
      return (
        <div key={field.name} className="flex items-center justify-between py-3 px-4 rounded-2xl bg-gray-100/50">
          <span className="text-sm font-medium text-gray-900">{label}</span>
          <button
            type="button"
            role="switch"
            aria-checked={!!val}
            aria-label={label}
            onClick={() => handleChange(field.name, !val)}
            className={clsx(
              'relative w-11 h-6 rounded-full transition-colors duration-200',
              val ? 'bg-ios-accent' : 'bg-gray-300'
            )}
          >
            <span
              className={clsx(
                'absolute top-0.5 left-0.5 w-5 h-5 bg-ios-surface rounded-full shadow transition-transform duration-200',
                val && 'translate-x-5'
              )}
            />
          </button>
        </div>
      );
    }

    if (field.type === 'IntegerField') {
      return (
        <div key={field.name} className="group">
          <label className="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2.5 ml-4">
            {label}
          </label>
          <input
            type="number"
            value={val ?? ''}
            onChange={(e) => {
              const parsed = parseInt(e.target.value);
              handleChange(field.name, isNaN(parsed) ? '' : parsed);
            }}
            className={clsx(
              'w-full bg-gray-100/50 border-none rounded-2xl py-4 px-5 text-sm font-medium text-gray-900',
              'placeholder:text-gray-400 focus:ring-2 focus:ring-gray-900/5 transition-all outline-none',
              'shadow-[inset_0_2px_4px_rgba(0,0,0,0.03)]'
            )}
          />
        </div>
      );
    }

    // CharField / default → text input
    return (
      <div key={field.name} className="group">
        <label className="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2.5 ml-4">
          {label}
        </label>
        <input
          type="text"
          value={val ?? ''}
          onChange={(e) => handleChange(field.name, e.target.value)}
          className={clsx(
            'w-full bg-gray-100/50 border-none rounded-2xl py-4 px-5 text-sm font-medium text-gray-900',
            'placeholder:text-gray-400 focus:ring-2 focus:ring-gray-900/5 transition-all outline-none',
            'shadow-[inset_0_2px_4px_rgba(0,0,0,0.03)]'
          )}
        />
      </div>
    );
  };

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
      {/* Header */}
      <div className="p-8 pb-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-[20px] bg-ios-surface shadow-[0_8px_16px_-4px_rgba(0,0,0,0.05)] flex items-center justify-center border border-white/80">
            <Settings2 size={22} className="text-gray-900" />
          </div>
          <div>
            <h3 className="text-base font-extrabold tracking-tight text-gray-900 leading-none mb-1.5">
              CONFIGURATION
            </h3>
            <p className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">
              {node.data.plugin_id}
            </p>
          </div>
        </div>
        <button onClick={onClose} className="p-3 rounded-full hover:bg-ios-surface/60 transition-colors active:scale-90">
          <X size={20} className="text-gray-400" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-8 space-y-4 custom-scrollbar">
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 size={24} className="animate-spin text-gray-400" />
          </div>
        ) : error ? (
          <div className="p-6 rounded-[32px] bg-rose-50/50 border border-rose-100 text-center space-y-3">
            <AlertCircle size={20} className="text-rose-400 mx-auto" />
            <p className="text-xs text-rose-500">{error}</p>
            <button
              onClick={() => loadConfig(node.data.plugin_id)}
              className="inline-flex items-center gap-1.5 text-[10px] font-bold text-rose-500 hover:text-rose-600 transition-colors"
            >
              <RefreshCw size={12} />
              重试
            </button>
          </div>
        ) : fields.length === 0 ? (
          <div className="p-6 rounded-[32px] bg-gray-100/30 border border-white/40 text-center">
            <p className="text-xs text-gray-500">该插件没有可配置的参数</p>
          </div>
        ) : (
          fields.map(renderField)
        )}
      </div>

      {/* Footer */}
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
            disabled={saving || loading || fields.length === 0 || !!error}
            className={clsx(
              'flex-1 flex items-center justify-center gap-2 py-4 rounded-[24px] font-bold text-[10px] tracking-widest transition-all',
              'bg-ios-accent text-ios-on-accent shadow-[0_16px_32px_-8px_rgba(0,0,0,0.3)] hover:opacity-90 active:scale-95',
              'disabled:opacity-50'
            )}
          >
            {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
            <span>{saving ? '保存中...' : '保存'}</span>
          </button>
        </div>
      </div>
    </aside>
  );
};

export default NodeConfigPanel;
