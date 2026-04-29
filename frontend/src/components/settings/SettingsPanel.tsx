import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { toast } from 'sonner';
import websocketService from '../../services/websocket';
import type { ConfigData } from '../../types/api.generated';
import SettingsGroup from './SettingsGroup';
import SettingsSelect from './SettingsSelect';
import SettingsInput from './SettingsInput';
import ThemeSegmentedControl from './ThemeSegmentedControl';

const CAP_TOOL_OPTIONS = ['MuMu', 'MiniCap', 'DroidCast', 'ADB'];
const TOUCH_TOOL_OPTIONS = ['MuMu', 'MiniTouch', 'MaaTouch', 'ADB'];

const DEFAULT_CONFIG: ConfigData = {
  dark_mode: true,
  cap_tool: 'MuMu',
  touch_tool: 'MaaTouch',
  email: null,
  password: null,
  receiver: null,
};

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

const SettingsPanel = ({ isOpen, onClose }: SettingsPanelProps) => {
  const [config, setConfig] = useState<ConfigData>(DEFAULT_CONFIG);
  const [loading, setLoading] = useState(false);

  const fetchConfig = useCallback(async () => {
    try {
      const data = await websocketService.getConfig();
      setConfig({ ...DEFAULT_CONFIG, ...data });
    } catch {
      toast.error('加载配置失败');
    }
  }, []);

  useEffect(() => {
    if (isOpen) fetchConfig();
  }, [isOpen, fetchConfig]);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', config.dark_mode);
    localStorage.setItem('dark_mode', String(config.dark_mode));
  }, [config.dark_mode]);

  const patch = <K extends keyof ConfigData>(key: K, value: ConfigData[K]) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      await websocketService.updateConfig(config);
      toast.success('设置已保存');
      onClose();
    } catch {
      toast.error('保存失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-40 bg-black/20 backdrop-blur-sm"
          />

          {/* Panel */}
          <motion.aside
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            className="fixed right-0 top-0 z-50 flex h-full w-[420px] flex-col border-l border-white/60 bg-ios-bg/80 shadow-2xl backdrop-blur-zen"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 pt-8 pb-4">
              <h2 className="text-xl font-[800] tracking-tight text-ios-black">设置</h2>
              <button
                onClick={onClose}
                className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/60 bg-ios-surface/40 text-ios-black shadow-sm backdrop-blur-md transition-transform active:scale-90 hover:bg-ios-surface/60"
              >
                <X size={18} />
              </button>
            </div>

            {/* Content */}
            <div className="custom-scrollbar flex-1 space-y-4 overflow-y-auto px-6 py-4">
              <SettingsGroup title="外观">
                <ThemeSegmentedControl
                  darkMode={config.dark_mode}
                  onChange={(v) => patch('dark_mode', v)}
                />
              </SettingsGroup>

              <SettingsGroup title="操作设置">
                <SettingsSelect
                  label="截图工具"
                  value={config.cap_tool}
                  options={CAP_TOOL_OPTIONS}
                  onChange={(v) => patch('cap_tool', v)}
                />
                <SettingsSelect
                  label="点击工具"
                  value={config.touch_tool}
                  options={TOUCH_TOOL_OPTIONS}
                  onChange={(v) => patch('touch_tool', v)}
                />
              </SettingsGroup>

              <SettingsGroup title="邮件通知">
                <SettingsInput
                  label="邮箱"
                  value={config.email ?? ''}
                  placeholder="sender@example.com"
                  onChange={(v) => patch('email', v || null)}
                />
                <SettingsInput
                  label="授权码"
                  value={config.password ?? ''}
                  type="password"
                  placeholder="SMTP 授权码"
                  onChange={(v) => patch('password', v || null)}
                />
                <SettingsInput
                  label="收件人"
                  value={config.receiver ?? ''}
                  placeholder="receiver@example.com"
                  onChange={(v) => patch('receiver', v || null)}
                />
              </SettingsGroup>
            </div>

            {/* Footer */}
            <div className="flex gap-3 border-t border-white/60 px-6 py-5">
              <button
                onClick={onClose}
                className="flex-1 rounded-2xl border border-black/5 bg-ios-surface/50 py-3 text-sm font-bold text-ios-black backdrop-blur-md transition-colors hover:bg-ios-surface/70 active:scale-[0.98]"
              >
                取消
              </button>
              <button
                onClick={handleSave}
                disabled={loading}
                className="flex-1 rounded-2xl bg-ios-accent py-3 text-sm font-bold text-ios-on-accent shadow-lg transition-all hover:opacity-90 active:scale-[0.98] disabled:opacity-50"
              >
                {loading ? '保存中…' : '保存'}
              </button>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
};

export default SettingsPanel;
