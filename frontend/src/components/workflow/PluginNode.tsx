import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Box, Activity, CheckCircle2, AlertCircle, Settings2 } from 'lucide-react';
import { clsx } from 'clsx';
import { WorkflowStatus } from '../../types/workflow';

export interface PluginNodeData {
  label: string;
  plugin_id: string;
  status?: WorkflowStatus | 'idle';
  config?: Record<string, any>;
}

const PluginNode = ({ data, selected }: NodeProps<PluginNodeData>) => {
  const status = data.status || 'idle';

  return (
    <div
      className={clsx(
        'relative min-w-[220px] p-4 rounded-[28px] transition-all duration-300',
        'bg-ios-surface/40 backdrop-blur-[40px]',
        'border border-white/60 shadow-[0_24px_48px_-12px_rgba(0,0,0,0.08)]',
        'ring-1 ring-gray-200/40',
        selected && 'ring-2 ring-black/20 shadow-[0_32px_64px_-16px_rgba(0,0,0,0.12)] scale-[1.02]',
        'active:scale-[0.98]'
      )}
    >
      {/* Status Indicator Glow */}
      <div
        className={clsx(
          'absolute -top-1 -right-1 w-3 h-3 rounded-full blur-[2px]',
          status === 'idle' && 'bg-gray-400',
          status === 'running' && 'bg-blue-500 animate-pulse',
          status === 'completed' && 'bg-emerald-500',
          status === 'failed' && 'bg-rose-500'
        )}
      />

      <div className="flex items-center gap-3">
        <div className={clsx(
          'p-2.5 rounded-2xl bg-gray-100/50 shadow-inner',
          'flex items-center justify-center'
        )}>
          <Box size={20} className="text-gray-600" />
        </div>
        
        <div className="flex-1 overflow-hidden">
          <div className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-0.5">
            {data.plugin_id}
          </div>
          <div className="text-sm font-extrabold tracking-tight text-gray-900 truncate">
            {data.label}
          </div>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          {status === 'running' && <Activity size={14} className="text-blue-500 animate-spin" />}
          {status === 'completed' && <CheckCircle2 size={14} className="text-emerald-500" />}
          {status === 'failed' && <AlertCircle size={14} className="text-rose-500" />}
          <span className={clsx(
            'text-[10px] font-bold uppercase tracking-wider',
            status === 'idle' && 'text-gray-400',
            status === 'running' && 'text-blue-600',
            status === 'completed' && 'text-emerald-600',
            status === 'failed' && 'text-rose-600'
          )}>
            {status}
          </span>
        </div>

        <button className="p-1.5 rounded-xl hover:bg-gray-100/80 transition-colors">
          <Settings2 size={14} className="text-gray-400" />
        </button>
      </div>

      {/* Handles */}
      <Handle
        type="target"
        position={Position.Left}
        className="!w-3 !h-3 !bg-ios-surface !border-2 !border-gray-200 !-left-1.5"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="!w-3 !h-3 !bg-ios-surface !border-2 !border-gray-200 !-right-1.5"
      />
    </div>
  );
};

export default memo(PluginNode);