import React, { useState, useEffect } from 'react';
import { 
  Plus, 
  RefreshCw, 
  Play, 
  Square, 
  Settings2,
  Monitor,
  Cpu, 
  Activity,
  AlertCircle,
  Search,
  LayoutGrid,
  List as ListIcon
} from 'lucide-react';
import { toast } from 'sonner';
import websocketService from '../services/websocket';
import DeviceCard from '../components/devices/DeviceCard';
import DeviceCreateModal from '../components/devices/DeviceCreateModal';
import DeviceEditModal from '../components/devices/DeviceEditModal';
import ConfirmModal from '../components/common/ConfirmModal';
import { clsx } from 'clsx';
import type { ModuleItem } from '../types/api.generated';

export default function DevicesPage() {
  const [devices, setDevices] = useState<ModuleItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  
  // Modals state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingDevice, setEditingDevice] = useState<ModuleItem | null>(null);
  const [deletingDevice, setDeletingDevice] = useState<ModuleItem | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchDevices = async () => {
    setIsLoading(true);
    try {
      const response = await websocketService.getModuleList();
      setDevices(response.modules || []);
    } catch (error) {
      console.error('Failed to fetch devices:', error);
      toast.error('获取设备列表失败');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
    
    // 订阅状态更新
    const handleStatusUpdate = (event: Event) => {
      const customEvent = event as CustomEvent;
      const update = customEvent.detail;
      if (update && update.module_name) {
        setDevices(prev => prev.map(d => 
          d.name === update.module_name ? { ...d, is_running: update.is_running } : d
        ));
      }
    };

    window.addEventListener('module-status', handleStatusUpdate);
    return () => window.removeEventListener('module-status', handleStatusUpdate);
  }, []);

  const handleStartDevice = async (device: ModuleItem) => {
    if (!device.current_workflow_id) {
      toast.error('未设置当前工作流', {
        description: '请先在编辑设备中选择或创建一个工作流'
      });
      return;
    }
    try {
      await websocketService.startWorkflow(device.name, device.current_workflow_id);
      setDevices(prev => prev.map(d =>
        d.name === device.name ? { ...d, is_running: true } : d
      ));
      toast.success(`正在启动: ${device.name}`);
    } catch (error) {
      toast.error('启动失败');
    }
  };

  const handleStopDevice = async (device: ModuleItem) => {
    try {
      await websocketService.stopWorkflow(device.name);
      setDevices(prev => prev.map(d =>
        d.name === device.name ? { ...d, is_running: false } : d
      ));
      toast.success(`正在停止: ${device.name}`);
    } catch (error) {
      toast.error('停止失败');
    }
  };

  const handleDeleteDevice = async (device: ModuleItem) => {
    if (device.is_running) {
      toast.error('设备运行中，无法删除');
      return;
    }
    setDeletingDevice(device);
  };

  const confirmDeleteDevice = async () => {
    if (!deletingDevice) return;
    
    setIsDeleting(true);
    try {
      await websocketService.deleteDevice({ device_id: deletingDevice.id });
      toast.success('设备已删除');
      fetchDevices();
      setDeletingDevice(null);
    } catch (error) {
      toast.error('删除失败');
    } finally {
      setIsDeleting(false);
    }
  };

  const filteredDevices = devices.filter(d => 
    d.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    d.port.toString().includes(searchQuery)
  );

  return (
    <div className="min-h-screen p-8 pb-24">
      {/* Header Section */}
      <header className="mb-10 flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
        <div>
          <div className="mb-2 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-ios-accent text-ios-on-accent shadow-lg">
              <Cpu size={20} />
            </div>
            <h1 className="text-3xl font-[900] italic tracking-tighter text-ios-black uppercase">
              Cluster Manager
            </h1>
          </div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-ios-gray opacity-60">
            {devices.length} Devices Connected • {devices.filter(d => d.is_running).length} Active
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Search Bar */}
          <div className="relative group">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-ios-gray group-focus-within:text-ios-black transition-colors" size={16} />
            <input 
              type="text"
              placeholder="SEARCH DEVICES..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="h-12 w-64 rounded-2xl border border-white/60 bg-ios-surface/50 pl-11 pr-4 text-[10px] font-black tracking-widest uppercase text-ios-black placeholder:text-ios-gray/40 focus:bg-ios-surface focus:outline-none focus:ring-2 focus:ring-black/5 transition-all shadow-sm"
            />
          </div>

          {/* View Toggle */}
          <div className="flex h-12 items-center rounded-2xl border border-white/60 bg-ios-surface/50 p-1 shadow-sm">
            <button 
              onClick={() => setViewMode('grid')}
              className={clsx(
                "flex h-full items-center gap-2 rounded-xl px-4 transition-all",
                viewMode === 'grid' ? "bg-ios-surface text-ios-black shadow-sm" : "text-ios-gray hover:text-ios-black"
              )}
            >
              <LayoutGrid size={16} />
            </button>
            <button 
              onClick={() => setViewMode('list')}
              className={clsx(
                "flex h-full items-center gap-2 rounded-xl px-4 transition-all",
                viewMode === 'list' ? "bg-ios-surface text-ios-black shadow-sm" : "text-ios-gray hover:text-ios-black"
              )}
            >
              <ListIcon size={16} />
            </button>
          </div>

          <button 
            onClick={fetchDevices}
            className="flex h-12 w-12 items-center justify-center rounded-2xl border border-white/60 bg-ios-surface/50 text-ios-gray hover:bg-ios-surface hover:text-ios-black active:scale-95 transition-all shadow-sm"
          >
            <RefreshCw size={18} className={isLoading ? "animate-spin" : ""} />
          </button>

          <button 
            onClick={() => setShowCreateModal(true)}
            className="flex h-12 items-center gap-2 rounded-2xl bg-ios-accent px-6 text-ios-on-accent shadow-xl hover:opacity-90 active:scale-95 transition-all"
          >
            <Plus size={18} />
            <span className="text-[10px] font-black uppercase tracking-widest">Add Device</span>
          </button>
        </div>
      </header>

      {/* Main Content */}
      {isLoading && devices.length === 0 ? (
        <div className="flex h-[50vh] items-center justify-center">
          <div className="flex flex-col items-center gap-4">
            <div className="h-12 w-12 animate-spin rounded-full border-4 border-ios-accent border-t-transparent" />
            <p className="text-[10px] font-black uppercase tracking-widest text-ios-gray">Initializing Cluster...</p>
          </div>
        </div>
      ) : filteredDevices.length === 0 ? (
        <div className="flex h-[50vh] flex-col items-center justify-center rounded-[40px] border-2 border-dashed border-black/5 bg-ios-surface/30 backdrop-blur-sm">
          <AlertCircle size={48} className="mb-4 text-ios-gray/20" />
          <h3 className="text-lg font-extrabold text-ios-black">No Devices Found</h3>
          <p className="text-xs font-bold uppercase tracking-widest text-ios-gray/60">Try adjusting your search or add a new device</p>
        </div>
      ) : viewMode === 'grid' ? (
        <div className="flex w-full max-w-[1680px] flex-wrap justify-center gap-6 mx-auto">
          {filteredDevices.map(device => (
            <div key={device.id} className="group relative w-[380px] max-w-full">
              <DeviceCard 
                module={device} 
                onStart={() => handleStartDevice(device)}
                onStop={() => handleStopDevice(device)}
                onEdit={() => setEditingDevice(device)}
                onDelete={() => handleDeleteDevice(device)}
              />
            </div>
          ))}
        </div>
      ) : (
        /* List View */
        <div className="overflow-hidden rounded-[32px] border border-white/60 bg-ios-surface/80 shadow-xl backdrop-blur-xl">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-black/5">
                <th className="px-8 py-5 text-[10px] font-black uppercase tracking-widest text-ios-gray">Status</th>
                <th className="px-8 py-5 text-[10px] font-black uppercase tracking-widest text-ios-gray">Device Name</th>
                <th className="px-8 py-5 text-[10px] font-black uppercase tracking-widest text-ios-gray">Port / Index</th>
                <th className="px-8 py-5 text-[10px] font-black uppercase tracking-widest text-ios-gray">Current Workflow</th>
                <th className="px-8 py-5 text-right text-[10px] font-black uppercase tracking-widest text-ios-gray">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-black/5">
              {filteredDevices.map(device => (
                <tr key={device.id} className="group hover:bg-black/[0.02] transition-colors">
                  <td className="px-8 py-4">
                    <div className={clsx(
                      "flex h-8 w-8 items-center justify-center rounded-lg",
                      device.is_running ? "bg-emerald-100 text-emerald-600" : "bg-gray-100 text-gray-400"
                    )}>
                      <Activity size={16} className={device.is_running ? "animate-pulse" : ""} />
                    </div>
                  </td>
                  <td className="px-8 py-4">
                    <div className="flex items-center gap-3">
                      <Monitor size={16} className="text-ios-gray" />
                      <span className="text-sm font-bold text-ios-black">{device.name}</span>
                    </div>
                  </td>
                  <td className="px-8 py-4">
                    <span className="text-xs font-mono font-bold text-ios-gray">
                      {device.port} <span className="mx-2 opacity-20">|</span> #{device.simulator_index}
                    </span>
                  </td>
                  <td className="px-8 py-4">
                    {device.current_workflow_id ? (
                      <div className="inline-flex items-center gap-2 rounded-full bg-ios-accent/5 px-3 py-1">
                        <div className="h-1.5 w-1.5 rounded-full bg-ios-accent" />
                        <span className="text-[10px] font-bold text-ios-black uppercase tracking-tight">Active Workflow</span>
                      </div>
                    ) : (
                      <span className="text-[10px] font-bold text-ios-gray/40 uppercase italic">None Assigned</span>
                    )}
                  </td>
                  <td className="px-8 py-4">
                    <div className="flex items-center justify-end gap-2">
                      {device.is_running ? (
                        <button 
                          onClick={() => handleStopDevice(device)}
                          className="flex h-9 items-center gap-2 rounded-xl bg-rose-500 px-4 text-white shadow-md hover:bg-rose-600 active:scale-95 transition-all"
                        >
                          <Square size={14} fill="currentColor" />
                          <span className="text-[9px] font-black uppercase tracking-widest">Stop</span>
                        </button>
                      ) : (
                        <button 
                          onClick={() => handleStartDevice(device)}
                          disabled={!device.current_workflow_id}
                          className="flex h-9 items-center gap-2 rounded-xl bg-ios-accent px-4 text-ios-on-accent shadow-md hover:opacity-90 active:scale-95 transition-all disabled:opacity-20"
                        >
                          <Play size={14} fill="currentColor" />
                          <span className="text-[9px] font-black uppercase tracking-widest">Start</span>
                        </button>
                      )}
                      <button 
                        onClick={() => setEditingDevice(device)}
                        className="flex h-9 w-9 items-center justify-center rounded-xl border border-black/5 bg-ios-surface text-ios-black hover:bg-gray-50 active:scale-90 transition-all"
                      >
                        <Settings2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modals */}
      {showCreateModal && (
        <DeviceCreateModal 
          onClose={() => setShowCreateModal(false)} 
          onSuccess={fetchDevices} 
        />
      )}
      
      {editingDevice && (
        <DeviceEditModal
          device={editingDevice}
          onClose={() => setEditingDevice(null)}
          onSuccess={fetchDevices}
        />
      )}

      <ConfirmModal
        isOpen={!!deletingDevice}
        title="删除设备"
        description={`确定要删除设备 "${deletingDevice?.name}" 吗？此操作不可撤销。`}
        confirmText="删除"
        cancelText="取消"
        isDanger
        isLoading={isDeleting}
        onConfirm={confirmDeleteDevice}
        onCancel={() => setDeletingDevice(null)}
      />
    </div>
  );
}
