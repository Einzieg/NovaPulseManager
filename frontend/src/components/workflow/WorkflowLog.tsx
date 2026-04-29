import React, { useState, useEffect, useCallback } from 'react';
import { 
  Activity, 
  CheckCircle2, 
  Circle, 
  Clock, 
  AlertCircle, 
  ChevronRight, 
  ChevronDown,
  Terminal,
  History
} from 'lucide-react';
import { clsx } from 'clsx';
import websocketService from '../../services/websocket';
import { NodeStatusUpdate, WorkflowStatus } from '../../types/workflow';

interface LogEntry {
  nodeId: string;
  label: string;
  status: WorkflowStatus;
  startTime: number;
  endTime?: number;
  duration?: string;
  error?: string;
}

const WorkflowLog: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isExpanded, setIsExpanded] = useState(true);

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  useEffect(() => {
    const handleStatusUpdate = (update: NodeStatusUpdate) => {
      setLogs((prevLogs) => {
        const existingIndex = prevLogs.findIndex(l => l.nodeId === update.node_id);
        const now = Date.now();

        if (existingIndex >= 0) {
          const newLogs = [...prevLogs];
          const entry = { ...newLogs[existingIndex] };
          
          entry.status = update.status;
          if (update.status === 'completed' || update.status === 'failed') {
            entry.endTime = now;
            entry.duration = formatDuration(now - entry.startTime);
          }
          if (update.error) entry.error = update.error;
          
          newLogs[existingIndex] = entry;
          return newLogs;
        } else {
          // New entry (usually 'running')
          return [{
            nodeId: update.node_id,
            label: update.node_id.split('-')[0], // Fallback label
            status: update.status,
            startTime: now,
            error: update.error
          }, ...prevLogs];
        }
      });
    };

    websocketService.onNodeStatus(handleStatusUpdate);
    // Note: In a real app, we might want to clear logs when a new workflow starts
    // For now, we keep them as a session history
  }, []);

  if (!isExpanded) {
    return (
      <button
        onClick={() => setIsExpanded(true)}
        className={clsx(
          "flex items-center gap-3 p-4 rounded-[24px] transition-all active:scale-95",
          "bg-ios-surface/60 backdrop-blur-3xl border border-white/60 shadow-xl",
          "text-gray-900 hover:bg-ios-surface/80"
        )}
      >
        <History size={18} className="text-gray-500" />
        <span className="text-[10px] font-bold uppercase tracking-widest">执行日志</span>
        <ChevronRight size={14} className="text-gray-400" />
      </button>
    );
  }

  return (
    <div className={clsx(
      "w-80 flex flex-col max-h-[500px] transition-all duration-500 ease-in-out",
      "bg-ios-surface/40 backdrop-blur-[40px] rounded-[32px] shadow-[0_32px_64px_-16px_rgba(0,0,0,0.12)]",
      "border border-white/60 overflow-hidden"
    )}>
      {/* Header */}
      <div className="flex items-center justify-between p-5 border-b border-gray-200/20 bg-ios-surface/20">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-gray-900 text-white shadow-lg">
            <Terminal size={14} />
          </div>
          <h3 className="text-[11px] font-extrabold uppercase tracking-[0.2em] text-gray-900">
            控制台
          </h3>
        </div>
        <button 
          onClick={() => setIsExpanded(false)}
          className="p-2 hover:bg-gray-100/50 rounded-full transition-colors"
        >
          <ChevronDown size={16} className="text-gray-400" />
        </button>
      </div>

      {/* Log List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
        {logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 opacity-40">
            <Activity size={32} className="mb-3 text-gray-300 animate-pulse" />
            <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">等待执行...</p>
          </div>
        ) : (
          logs.map((log) => (
            <div 
              key={`${log.nodeId}-${log.startTime}`}
              className={clsx(
                "group relative p-4 rounded-2xl transition-all border",
                "bg-ios-surface/40 hover:bg-ios-surface/60",
                log.status === 'running' ? "border-blue-200/50 shadow-sm" : "border-transparent"
              )}
            >
              <div className="flex items-start gap-3">
                <div className="mt-1">
                  {log.status === 'running' && (
                    <div className="relative">
                      <Circle size={16} className="text-blue-500 animate-ping absolute opacity-20" />
                      <Activity size={16} className="text-blue-500 animate-pulse" />
                    </div>
                  )}
                  {log.status === 'completed' && <CheckCircle2 size={16} className="text-emerald-500" />}
                  {log.status === 'failed' && <AlertCircle size={16} className="text-rose-500" />}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] font-extrabold tracking-tight text-gray-900 truncate">
                      {log.label}
                    </span>
                    {log.duration && (
                      <div className="flex items-center gap-1 text-[9px] font-bold text-gray-400">
                        <Clock size={10} />
                        {log.duration}
                      </div>
                    )}
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <span className={clsx(
                      "text-[8px] font-black uppercase tracking-widest px-1.5 py-0.5 rounded-md",
                      log.status === 'running' && "bg-blue-50 text-blue-600",
                      log.status === 'completed' && "bg-emerald-50 text-emerald-600",
                      log.status === 'failed' && "bg-rose-50 text-rose-600"
                    )}>
                      {log.status}
                    </span>
                    <span className="text-[8px] font-bold text-gray-300">
                      {new Date(log.startTime).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </span>
                  </div>

                  {log.error && (
                    <p className="mt-2 text-[9px] font-medium text-rose-500 bg-rose-50/50 p-2 rounded-lg border border-rose-100/50">
                      {log.error}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Footer Stats */}
      <div className="p-4 bg-gray-50/30 border-t border-gray-200/20 flex items-center justify-between">
        <div className="flex gap-4">
          <div className="flex flex-col">
            <span className="text-[8px] font-bold text-gray-400 uppercase tracking-tighter">总节点数</span>
            <span className="text-xs font-black text-gray-900">{logs.length}</span>
          </div>
          <div className="flex flex-col">
            <span className="text-[8px] font-bold text-gray-400 uppercase tracking-tighter">成功</span>
            <span className="text-xs font-black text-emerald-600">{logs.filter(l => l.status === 'completed').length}</span>
          </div>
        </div>
        <button 
          onClick={() => setLogs([])}
          className="text-[9px] font-bold text-gray-400 hover:text-gray-900 transition-colors uppercase tracking-widest"
        >
          清空
        </button>
      </div>
    </div>
  );
};

export default WorkflowLog;