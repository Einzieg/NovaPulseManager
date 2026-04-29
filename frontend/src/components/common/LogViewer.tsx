import React, { useState, useEffect } from 'react';
import { Virtuoso } from 'react-virtuoso';
import { clsx } from 'clsx';

interface LogViewerProps {
  moduleName?: string;
  compact?: boolean;
}

const LogViewer = ({ moduleName, compact }: LogViewerProps) => {
  const [logs, setLogs] = useState<string[]>([]);
  
  useEffect(() => {
    const handleLog = (event: Event) => {
      const customEvent = event as CustomEvent;
      const data = customEvent.detail;
      
      // 如果指定了 moduleName，则只显示该模块的日志
      if (moduleName && data.module !== moduleName) {
        return;
      }

      const time = new Date().toLocaleTimeString();
      const logMessage = `[${time}] ${data.level || 'INFO'}: ${data.message}`;
      setLogs(prev => [...prev.slice(-200), logMessage]);
    };

    window.addEventListener('task-log', handleLog);
    return () => window.removeEventListener('task-log', handleLog);
  }, [moduleName]);

  // 模拟一些初始日志（可选）
  useEffect(() => {
    if (logs.length === 0) {
      setLogs([`[${new Date().toLocaleTimeString()}] SYSTEM: Initializing log stream for ${moduleName || 'all modules'}...`]);
    }
  }, [moduleName]);

  return (
    <div className={clsx(
      "h-full w-full overflow-hidden font-mono text-gray-400 shadow-inner transition-all",
      compact ? "bg-transparent p-2 text-[9px]" : "rounded-ios-md bg-[#111111] p-4 text-[10px]"
    )}>
      <Virtuoso
        data={logs}
        followOutput={'auto'}
        itemContent={(index, log) => (
          <div className="flex py-0.5 leading-relaxed">
            {!compact && <span className="mr-3 w-6 shrink-0 text-right text-gray-600 opacity-50">{index}</span>}
            <span className="truncate text-gray-300">
              {log.includes('INFO') && <span className="text-blue-400 mr-1">INFO</span>}
              {log.includes('ERROR') && <span className="text-rose-400 mr-1">ERROR</span>}
              {log.includes('SUCCESS') && <span className="text-emerald-400 mr-1">SUCCESS</span>}
              {log.replace(/\[.*?\] (INFO|ERROR|SUCCESS|SYSTEM):/, '')}
            </span>
          </div>
        )}
      />
    </div>
  );
};

export default LogViewer;
