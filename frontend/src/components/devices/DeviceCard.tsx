import React from 'react';
import { Play, Square, Monitor, Hash, Server, Activity, Settings2, Trash2 } from 'lucide-react';
import LogViewer from '../common/LogViewer';
import { clsx } from 'clsx';
import type { ModuleItem } from '../../types/api.generated';

interface DeviceCardProps {
  module: ModuleItem;
  onStart: () => void;
  onStop: () => void;
  onEdit: () => void;
  onDelete: () => void;
}

const DeviceCard = ({ module, onStart, onStop, onEdit, onDelete }: DeviceCardProps) => {
  const isRunning = module.is_running;

  return (
    <div className="group relative overflow-hidden rounded-[40px] border border-white/60 bg-ios-surface/60 p-8 shadow-xl ring-1 ring-black/5 transition-all hover:bg-ios-surface/80 backdrop-blur-xl">
      
      {/* Header */}
      <div className="mb-8 flex items-start justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className={clsx(
              "h-2 w-2 rounded-full animate-pulse",
              isRunning ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]" : "bg-ios-gray/30"
            )} />
            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-ios-gray">
              {isRunning ? 'System Active' : 'Standby'}
            </span>
          </div>
          <h3 className="text-2xl font-[900] italic tracking-tighter text-ios-black uppercase">
            {module.name}
          </h3>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Secondary Actions (Hover visible) */}
          <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-all translate-x-2 group-hover:translate-x-0">
            <button 
              onClick={(e) => { e.stopPropagation(); onEdit(); }}
              className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/60 bg-ios-surface/80 text-ios-black shadow-sm backdrop-blur-md hover:bg-ios-surface active:scale-90 transition-all"
              title="Edit Device"
            >
              <Settings2 size={18} />
            </button>
            <button 
              onClick={(e) => { e.stopPropagation(); onDelete(); }}
              className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/60 bg-rose-50/80 text-rose-600 shadow-sm backdrop-blur-md hover:bg-rose-100 active:scale-90 transition-all"
              title="Delete Device"
            >
              <Trash2 size={18} />
            </button>
          </div>

          {/* Primary Action */}
          <button 
            onClick={isRunning ? onStop : onStart}
            disabled={!isRunning && !module.current_workflow_id}
            className={clsx(
              "flex h-14 w-14 items-center justify-center rounded-[22px] text-ios-on-accent shadow-2xl transition-all active:scale-90 disabled:opacity-20",
              isRunning ? "bg-ios-accent hover:opacity-90" : "bg-ios-accent hover:opacity-90"
            )}
          >
            {isRunning ? (
              <Square size={24} fill="currentColor" />
            ) : (
              <Play size={24} fill="currentColor" className="ml-1" />
            )}
          </button>
        </div>
      </div>

      {/* Device Specs (Physical Cut) */}
      <div className="mb-8 grid grid-cols-2 gap-3">
        <div className="flex items-center gap-3 rounded-2xl border border-black/5 bg-gray-100/50 p-3 shadow-inner">
          <Hash size={14} className="text-ios-gray" />
          <div>
            <p className="text-[8px] font-bold uppercase tracking-widest text-ios-gray/60">Index</p>
            <p className="font-mono text-xs font-bold text-ios-black">#{module.simulator_index}</p>
          </div>
        </div>
        <div className="flex items-center gap-3 rounded-2xl border border-black/5 bg-gray-100/50 p-3 shadow-inner">
          <Server size={14} className="text-ios-gray" />
          <div>
            <p className="text-[8px] font-bold uppercase tracking-widest text-ios-gray/60">Port</p>
            <p className="font-mono text-xs font-bold text-ios-black">{module.port}</p>
          </div>
        </div>
      </div>

      {/* Workflow Status */}
      <div className="mb-8">
        <div className="mb-3 flex items-center justify-between">
          <span className="text-[9px] font-black uppercase tracking-widest text-ios-gray">Current Workflow</span>
          {module.current_workflow_id ? (
            <span className="text-[9px] font-bold text-ios-black bg-ios-surface px-2 py-0.5 rounded-full border border-black/5 shadow-sm">ASSIGNED</span>
          ) : (
            <span className="text-[9px] font-bold text-rose-500">UNASSIGNED</span>
          )}
        </div>
        <div className="flex h-12 items-center justify-center rounded-2xl border border-dashed border-black/10 bg-ios-surface/40 px-4">
          {module.current_workflow_id ? (
            <div className="flex items-center gap-2">
              <Activity size={14} className={clsx("text-ios-black", isRunning && "animate-spin")} />
              <span className="text-[10px] font-bold text-ios-black uppercase tracking-tight truncate max-w-[120px]">
                {isRunning ? 'Running' : 'Workflow Ready'}
              </span>
            </div>
          ) : (
            <span className="text-[10px] font-bold text-ios-gray/30 uppercase italic">No Workflow Selected</span>
          )}
        </div>
      </div>

      {/* Logs Preview */}
      <div className="h-32 overflow-hidden rounded-2xl border border-black/5 bg-[#1C1C1E] shadow-2xl">
        <LogViewer moduleName={module.name} compact />
      </div>
    </div>
  );
};

export default DeviceCard;
