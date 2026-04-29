import { useState, useEffect, useRef } from 'react';

import type { LogEntry } from '../types/api.generated';

interface LogViewerProps {
  moduleName?: string;
}

export default function LogViewer({ moduleName }: LogViewerProps) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleLog = (event: CustomEvent<LogEntry>) => {
      const log = event.detail;
      if (!moduleName || log.module === moduleName) {
        setLogs(prev => [...prev.slice(-999), log]);
      }
    };

    window.addEventListener('task-log', handleLog as EventListener);
    return () => window.removeEventListener('task-log', handleLog as EventListener);
  }, [moduleName]);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'ERROR': return 'text-red-600';
      case 'WARNING': return 'text-yellow-600';
      case 'INFO': return 'text-blue-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="h-64 overflow-y-auto rounded-lg border border-black/5 bg-black/5 p-4 font-mono text-sm">
      {logs.map((log, i) => (
        <div key={i} className="mb-1">
          <span className="text-gray-400">{new Date(log.timestamp * 1000).toLocaleTimeString()}</span>
          {' '}
          <span className={getLevelColor(log.level)}>[{log.level}]</span>
          {' '}
          <span className="text-gray-700">{log.message}</span>
        </div>
      ))}
      <div ref={logEndRef} />
    </div>
  );
}