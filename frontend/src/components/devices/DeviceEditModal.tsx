import React, { useState, useEffect } from 'react';
import { X, Save, Server, Hash, Monitor, Trash2, Plus, GitBranch, Check, Play, Square } from 'lucide-react';
import { toast } from 'sonner';
import websocketService from '../../services/websocket';
import WorkflowEditor from '../workflow/WorkflowEditor';
import ConfirmModal from '../common/ConfirmModal';
import PromptModal from '../common/PromptModal';
import { clsx } from 'clsx';
import type { ModuleItem, WorkflowSummary } from '../../types/api.generated';

interface DeviceEditModalProps {
  device: ModuleItem;
  onClose: () => void;
  onSuccess: () => void;
}

export default function DeviceEditModal({ device, onClose, onSuccess }: DeviceEditModalProps) {
  // 1. 基础信息状态
  const [formData, setFormData] = useState({
    name: device.name,
    simulator_index: device.simulator_index,
    port: device.port
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 2. 工作流管理状态
  const [workflows, setWorkflows] = useState<WorkflowSummary[]>([]);
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(device.current_workflow_id || null);
  const [isLoadingWorkflows, setIsLoadingWorkflows] = useState(true);
  const [showEditor, setShowEditor] = useState(false);

  // Modal states
  const [showCreateWorkflow, setShowCreateWorkflow] = useState(false);
  const [deletingWorkflowId, setDeletingWorkflowId] = useState<string | null>(null);
  const [isDeletingWorkflow, setIsDeletingWorkflow] = useState(false);

  useEffect(() => {
    loadWorkflows();
  }, [device.name]);

  const loadWorkflows = async () => {
    setIsLoadingWorkflows(true);
    try {
      const response = await websocketService.listWorkflows(device.name);
      setWorkflows(response.workflows || []);
    } catch (error) {
      console.error('Failed to load workflows:', error);
    } finally {
      setIsLoadingWorkflows(false);
    }
  };

  const handleUpdateInfo = async (e: React.FormEvent) => {
    e.preventDefault();
    if (device.is_running) {
      toast.error('设备运行中，禁止修改基础信息');
      return;
    }
    setIsSubmitting(true);
    try {
      await websocketService.updateDevice({
        device_id: device.id,
        ...formData
      });
      toast.success('设备信息已更新');
      onSuccess();
    } catch (error) {
      toast.error('更新失败', { description: error instanceof Error ? error.message : '未知错误' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSetCurrentWorkflow = async (workflowId: string | null) => {
    try {
      await websocketService.setCurrentWorkflow(device.id, workflowId);
      setSelectedWorkflowId(workflowId);
      toast.success(workflowId ? '已切换当前工作流' : '已取消当前工作流');
      onSuccess();
    } catch (error) {
      toast.error('设置失败');
    }
  };

  const handleCreateWorkflow = async (name: string) => {
    const newId = `wf_${device.name}_${Date.now()}`;
    try {
      // 初始保存一个空工作流
      await websocketService.saveWorkflow(device.name, {
        id: newId,
        name: name,
        module_name: device.name,
        nodes: [],
        edges: []
      });
      await loadWorkflows();
      handleSetCurrentWorkflow(newId);
      toast.success('新工作流已创建');
      setShowCreateWorkflow(false);
    } catch (error) {
      toast.error('创建失败');
    }
  };

  const confirmDeleteWorkflow = async () => {
    if (!deletingWorkflowId) return;
    
    setIsDeletingWorkflow(true);
    try {
      await websocketService.deleteWorkflow(deletingWorkflowId);
      if (selectedWorkflowId === deletingWorkflowId) {
        setSelectedWorkflowId(null);
      }
      await loadWorkflows();
      toast.success('工作流已删除');
      setDeletingWorkflowId(null);
    } catch (error) {
      toast.error('删除失败');
    } finally {
      setIsDeletingWorkflow(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-md p-6">
      <div className="flex h-full max-h-[90vh] w-full max-w-6xl flex-col overflow-hidden rounded-[40px] border border-white/60 bg-ios-bg/90 shadow-2xl backdrop-blur-2xl">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-black/5 p-8">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-ios-accent text-ios-on-accent shadow-lg">
              <Monitor size={24} />
            </div>
            <div>
              <h3 className="text-xl font-[800] italic tracking-tight text-ios-black uppercase">
                Edit Device: {device.name}
              </h3>
              <p className="text-[10px] font-bold uppercase tracking-widest text-ios-gray opacity-60">
                ID: {device.id} • PORT: {device.port}
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="rounded-full p-3 hover:bg-black/5 active:scale-90 transition-transform"
          >
            <X size={24} className="text-ios-gray" />
          </button>
        </div>

        {/* Content Area */}
        <div className="flex flex-1 overflow-hidden">
          
          {/* Left Panel: Settings & Workflow List */}
          <div className="w-80 shrink-0 overflow-y-auto border-r border-black/5 p-8 space-y-10 custom-scrollbar">
            
            {/* Section: Basic Info */}
            <section>
              <h4 className="mb-6 text-[10px] font-black uppercase tracking-[0.2em] text-ios-gray">Basic Settings</h4>
              <form onSubmit={handleUpdateInfo} className="space-y-5">
                <div className="space-y-4">
                  <div className="group">
                    <label className="mb-2 block text-[9px] font-bold uppercase tracking-widest text-ios-gray/60 ml-2">Name</label>
                    <input
                      type="text"
                      value={formData.name}
                      disabled={device.is_running}
                      onChange={e => setFormData(prev => ({ ...prev, name: e.target.value }))}
                      className="w-full rounded-xl border border-black/5 bg-ios-surface/50 px-4 py-2.5 text-sm font-bold text-ios-black focus:bg-ios-surface focus:outline-none transition-all disabled:opacity-50"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="group">
                      <label className="mb-2 block text-[9px] font-bold uppercase tracking-widest text-ios-gray/60 ml-2">Index</label>
                      <input
                        type="number"
                        value={formData.simulator_index}
                        disabled={device.is_running}
                        onChange={e => setFormData(prev => ({ ...prev, simulator_index: parseInt(e.target.value) }))}
                        className="w-full rounded-xl border border-black/5 bg-ios-surface/50 px-4 py-2.5 text-sm font-mono font-bold text-ios-black focus:bg-ios-surface focus:outline-none transition-all disabled:opacity-50"
                      />
                    </div>
                    <div className="group">
                      <label className="mb-2 block text-[9px] font-bold uppercase tracking-widest text-ios-gray/60 ml-2">Port</label>
                      <input
                        type="number"
                        value={formData.port}
                        disabled={device.is_running}
                        onChange={e => setFormData(prev => ({ ...prev, port: parseInt(e.target.value) }))}
                        className="w-full rounded-xl border border-black/5 bg-ios-surface/50 px-4 py-2.5 text-sm font-mono font-bold text-ios-black focus:bg-ios-surface focus:outline-none transition-all disabled:opacity-50"
                      />
                    </div>
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={isSubmitting || device.is_running}
                  className="flex w-full items-center justify-center gap-2 rounded-xl bg-ios-surface border border-black/5 py-3 text-[10px] font-bold tracking-widest uppercase text-ios-black shadow-sm hover:bg-gray-50 active:scale-95 transition-all disabled:opacity-30"
                >
                  <Save size={14} />
                  Update Info
                </button>
              </form>
            </section>

            {/* Section: Workflows */}
            <section>
              <div className="mb-6 flex items-center justify-between">
                <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-ios-gray">Workflows</h4>
                <button
                  onClick={() => setShowCreateWorkflow(true)}
                  className="rounded-full p-1.5 text-ios-black hover:bg-black/5 transition-colors"
                >
                  <Plus size={16} />
                </button>
              </div>

              <div className="space-y-2">
                {isLoadingWorkflows ? (
                  <div className="py-4 text-center text-[10px] font-bold text-ios-gray animate-pulse">LOADING...</div>
                ) : workflows.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-black/10 p-6 text-center">
                    <p className="text-[10px] font-bold text-ios-gray/40 uppercase tracking-widest">No Workflows</p>
                  </div>
                ) : (
                  workflows.map(wf => (
                    <div 
                      key={wf.workflow_id}
                      className={clsx(
                        "group relative flex items-center justify-between rounded-2xl border p-3 transition-all cursor-pointer",
                        selectedWorkflowId === wf.workflow_id 
                          ? "border-ios-accent bg-ios-accent text-ios-on-accent shadow-md"
                          : "border-black/5 bg-ios-surface/40 hover:bg-ios-surface/80"
                      )}
                      onClick={() => handleSetCurrentWorkflow(wf.workflow_id)}
                    >
                      <div className="flex items-center gap-3 overflow-hidden">
                        <GitBranch size={14} className={selectedWorkflowId === wf.workflow_id ? "text-white/60" : "text-ios-gray"} />
                        <span className="truncate text-xs font-bold tracking-tight">{wf.name}</span>
                      </div>
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        {selectedWorkflowId === wf.workflow_id && <Check size={14} className="mr-1" />}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setDeletingWorkflowId(wf.workflow_id);
                          }}
                          className={clsx(
                            "rounded-lg p-1.5 transition-colors",
                            selectedWorkflowId === wf.workflow_id ? "hover:bg-ios-surface/20 text-white" : "hover:bg-rose-50 text-rose-500"
                          )}
                        >
                          <Trash2 size={12} />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </section>
          </div>

          {/* Right Panel: Workflow Editor */}
          <div className="flex-1 relative bg-ios-bg/50">
            {!selectedWorkflowId ? (
              <div className="flex h-full flex-col items-center justify-center p-12 text-center">
                <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-[32px] bg-ios-surface/40 border border-white/60 shadow-sm">
                  <GitBranch size={32} className="text-ios-gray/30" />
                </div>
                <h5 className="text-lg font-extrabold text-ios-black tracking-tight">未选择工作流</h5>
                <p className="mt-2 max-w-xs text-xs font-medium text-ios-gray leading-relaxed">
                  请从左侧列表选择一个工作流进行编辑，或点击 "+" 号创建一个新的流程。
                </p>
              </div>
            ) : (
              <div className="h-full w-full animate-in fade-in duration-500">
                <WorkflowEditor 
                  key={selectedWorkflowId} 
                  moduleName={device.name} 
                  workflowId={selectedWorkflowId} 
                />
              </div>
            )}
          </div>
        </div>
      </div>

      <PromptModal
        isOpen={showCreateWorkflow}
        title="新建工作流"
        description="请输入新工作流的名称"
        placeholder="例如: 每日任务流程"
        confirmText="创建"
        cancelText="取消"
        onConfirm={handleCreateWorkflow}
        onCancel={() => setShowCreateWorkflow(false)}
      />

      <ConfirmModal
        isOpen={!!deletingWorkflowId}
        title="删除工作流"
        description="确定要删除此工作流吗？此操作不可撤销。"
        confirmText="删除"
        cancelText="取消"
        isDanger
        isLoading={isDeletingWorkflow}
        onConfirm={confirmDeleteWorkflow}
        onCancel={() => setDeletingWorkflowId(null)}
      />
    </div>
  );
}
