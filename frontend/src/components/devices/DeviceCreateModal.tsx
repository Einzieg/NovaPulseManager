import React, { useEffect, useRef, useState } from 'react';
import { X, Save, Server, Hash, Monitor } from 'lucide-react';
import { toast } from 'sonner';
import websocketService from '../../services/websocket';
import { clsx } from 'clsx';

interface DeviceCreateModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

export default function DeviceCreateModal({ onClose, onSuccess }: DeviceCreateModalProps) {
  const [formData, setFormData] = useState({
    name: '',
    simulator_index: 0,
    port: 5555
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const nameInputRef = useRef<HTMLInputElement>(null);

  // UX: focus the first field when the modal opens.
  useEffect(() => {
    // Delay a tick to ensure the element is mounted and visible.
    const t = window.setTimeout(() => {
      nameInputRef.current?.focus({ preventScroll: true });
    }, 0);
    return () => window.clearTimeout(t);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await websocketService.createDevice(formData);
      toast.success('设备创建成功');
      onSuccess();
      onClose();
    } catch (error) {
      console.error('Failed to create device:', error);
      toast.error('创建失败', {
        description: error instanceof Error ? error.message : '未知错误'
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm p-4">
      <div className="w-full max-w-md overflow-hidden rounded-[32px] border border-white/60 bg-ios-surface/80 shadow-2xl backdrop-blur-xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-black/5 p-6">
          <h3 className="text-lg font-[800] italic tracking-tight text-ios-black">
            NEW DEVICE
          </h3>
          <button 
            onClick={onClose}
            className="rounded-full p-2 hover:bg-black/5 active:scale-90 transition-transform"
          >
            <X size={20} className="text-ios-gray" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div className="space-y-4">
            <div className="group">
              <label className="mb-2 flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-ios-gray">
                <Monitor size={12} />
                Device Name
              </label>
              <input
                type="text"
                required
                ref={nameInputRef}
                value={formData.name}
                onChange={e => setFormData(prev => ({ ...prev, name: e.target.value }))}
                className="w-full rounded-2xl border border-black/5 bg-ios-surface/50 px-4 py-3 font-bold text-ios-black placeholder:text-black/20 focus:border-ios-black/20 focus:bg-ios-surface focus:outline-none focus:ring-0 transition-all"
                placeholder="e.g. Pixel_7_Pro"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="group">
                <label className="mb-2 flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-ios-gray">
                  <Hash size={12} />
                  Sim Index
                </label>
                <input
                  type="number"
                  required
                  min={0}
                  value={formData.simulator_index}
                  onChange={e => setFormData(prev => ({ ...prev, simulator_index: parseInt(e.target.value) }))}
                  className="w-full rounded-2xl border border-black/5 bg-ios-surface/50 px-4 py-3 font-mono font-bold text-ios-black focus:border-ios-black/20 focus:bg-ios-surface focus:outline-none focus:ring-0 transition-all"
                />
              </div>

              <div className="group">
                <label className="mb-2 flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-ios-gray">
                  <Server size={12} />
                  ADB Port
                </label>
                <input
                  type="number"
                  required
                  value={formData.port}
                  onChange={e => setFormData(prev => ({ ...prev, port: parseInt(e.target.value) }))}
                  className="w-full rounded-2xl border border-black/5 bg-ios-surface/50 px-4 py-3 font-mono font-bold text-ios-black focus:border-ios-black/20 focus:bg-ios-surface focus:outline-none focus:ring-0 transition-all"
                />
              </div>
            </div>
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={isSubmitting}
              className={clsx(
                "flex w-full items-center justify-center gap-2 rounded-2xl bg-ios-accent py-4 text-ios-on-accent shadow-lg transition-all hover:opacity-90 active:scale-95",
                isSubmitting && "opacity-70 cursor-not-allowed"
              )}
            >
              <Save size={18} />
              <span className="text-xs font-bold tracking-widest uppercase">
                {isSubmitting ? 'Creating...' : 'Create Device'}
              </span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
