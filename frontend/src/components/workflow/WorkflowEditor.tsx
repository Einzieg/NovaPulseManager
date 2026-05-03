import React, { useState, useCallback, useEffect, useRef } from 'react';
import ReactFlow, {
  addEdge,
  Background,
  Controls,
  Connection,
  Edge,
  Node,
  useNodesState,
  useEdgesState,
  Panel,
  MarkerType,
  ReactFlowProvider,
  getOutgoers,
} from 'reactflow';
import 'reactflow/dist/style.css';

import PluginNode from './PluginNode';
import PluginSidebar from './PluginSidebar';
import NodeConfigPanel from './NodeConfigPanel';
import WorkflowLog from './WorkflowLog';
import { toast } from 'sonner';
import websocketService from '../../services/websocket';
import { WorkflowData, NodeStatusUpdate } from '../../types/api.generated';
import ConfirmModal from '../common/ConfirmModal';
import { Save, Play, Trash2, Zap, Plus, Layers } from 'lucide-react';
import { clsx } from 'clsx';

const nodeTypes = {
  plugin: PluginNode,
};

interface WorkflowEditorProps {
  moduleName: string;
  workflowId?: string;
  deviceId?: number;
}

const WorkflowEditorContent: React.FC<WorkflowEditorProps> = ({ moduleName, workflowId, deviceId }) => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [reactFlowInstance, setReactFlowInstance] = useState<any>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [currentWorkflowId, setCurrentWorkflowId] = useState<string>(
    workflowId || `workflow_${moduleName}_${Date.now()}`
  );
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  // Sync currentWorkflowId with prop
  useEffect(() => {
    if (workflowId) {
      setCurrentWorkflowId(workflowId);
    }
  }, [workflowId]);

  const selectedNode = nodes.find(n => n.id === selectedNodeId) || null;

  // Load Workflow Data
  useEffect(() => {
    const loadWorkflow = async () => {
      try {
        let response;
        if (workflowId) {
          // If workflowId is provided, load that specific workflow
          response = await websocketService.getWorkflow(workflowId, moduleName);
        } else {
          // Fallback to loading the default/active workflow for the module
          response = await websocketService.loadWorkflow(moduleName);
        }

        if (response && response.workflow_data) {
          const data = response.workflow_data;
          
          // If we loaded by moduleName (default), update the ID
          if (!workflowId && response.workflow_id) {
            setCurrentWorkflowId(response.workflow_id);
          }

          const flowNodes: Node[] = (data.nodes || []).map((n: any) => ({
            id: n.id,
            type: 'plugin',
            position: n.position,
            data: {
              label: n.action_id || n.plugin_id?.split('.').pop() || n.action_ref?.split('.').pop() || n.id,
              plugin_id: n.plugin_id || n.action_ref,
              app_id: n.app_id,
              module_id: n.module_id,
              action_id: n.action_id,
              action_ref: n.action_ref,
              device_id: n.device_id ?? deviceId ?? null,
              status: 'idle',
              config: n.config || {}
            },
          }));

          const flowEdges: Edge[] = (data.edges || []).map((e: any) => ({
            id: e.id,
            source: e.source,
            target: e.target,
            animated: false,
            style: { stroke: '#94a3b8', strokeWidth: 2 },
            markerEnd: { type: MarkerType.ArrowClosed, color: '#94a3b8' },
          }));

          setNodes(flowNodes);
          setEdges(flowEdges);
          toast.success('工作流已加载');
        }
      } catch (error) {
        console.error('Failed to load workflow:', error);
        toast.error('工作流加载失败');
      }
    };

    loadWorkflow();
  }, [moduleName, setNodes, setEdges]);

  // Listen for status updates
  useEffect(() => {
    websocketService.onNodeStatus((update: NodeStatusUpdate) => {
      setNodes((nds) =>
        nds.map((node) => {
          if (node.id === update.node_id) {
            return {
              ...node,
              data: { ...node.data, status: update.status },
            };
          }
          return node;
        })
      );
    });
  }, [setNodes]);

  const isValidConnection = useCallback(
    (connection: Connection) => {
      const { source, target } = connection;
      if (source === target) return false;

      // DAG Validation: Check if target already leads back to source
      const checkCycle = (node: Node, visited = new Set<string>()): boolean => {
        if (node.id === source) return true;
        if (visited.has(node.id)) return false;
        visited.add(node.id);

        const outgoers = getOutgoers(node, nodes, edges);
        return outgoers.some((outgoer) => checkCycle(outgoer, visited));
      };

      const targetNode = nodes.find((n) => n.id === target);
      if (!targetNode) return false;

      return !checkCycle(targetNode);
    },
    [nodes, edges]
  );

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNodeId(node.id);
  }, []);

  const onDeleteNode = useCallback((nodeId: string) => {
    setNodes((nds) => nds.filter((node) => node.id !== nodeId));
    setEdges((eds) => eds.filter((edge) => edge.source !== nodeId && edge.target !== nodeId));
    setSelectedNodeId(null);
  }, [setNodes, setEdges]);

  const onConnect = useCallback(
    (params: Connection) => {
      if (!isValidConnection(params)) {
        console.warn('Connection would create a cycle (DAG violation)');
        return;
      }

      setEdges((eds) =>
        addEdge(
          {
            ...params,
            animated: true,
            style: { stroke: '#1C1C1E', strokeWidth: 2, opacity: 0.4 },
            markerEnd: { type: MarkerType.ArrowClosed, color: '#1C1C1E' },
          },
          eds
        )
      );
    },
    [setEdges, isValidConnection]
  );

  const onSave = useCallback(async (silent = false) => {
    if (nodes.length === 0 && !silent) return;
    
    setIsSaving(true);
    try {
      const workflowData = {
        schema_version: 2,
        id: currentWorkflowId,
        name: `${moduleName} Workflow`,
        description: `Workflow for module ${moduleName}`,
        module_name: moduleName,
        nodes: nodes.map((n) => ({
          id: n.id,
          type: 'action',
          plugin_id: n.data.plugin_id,
          app_id: n.data.app_id,
          module_id: n.data.module_id,
          action_id: n.data.action_id,
          action_ref: n.data.action_ref,
          device_id: n.data.device_id ?? deviceId ?? null,
          position: n.position,
          config: n.data.config || {},
        })),
        edges: edges.map((e) => ({
          id: e.id,
          source: e.source,
          target: e.target,
        })),
      };
      await websocketService.saveWorkflow(moduleName, workflowData);
      setLastSaved(new Date());
      setHasUnsavedChanges(false);
      
      if (!silent) {
        toast.success('工作流已保存', {
          description: `${nodes.length} 个节点, ${edges.length} 个连接`,
        });
      }
    } catch (error) {
      console.error('Save failed:', error);
      if (!silent) {
        toast.error('保存失败', {
          description: error instanceof Error ? error.message : '未知错误',
        });
      }
    } finally {
      setIsSaving(false);
    }
  }, [currentWorkflowId, moduleName, nodes, edges, deviceId]);

  // Auto-save logic
  useEffect(() => {
    if (nodes.length === 0) return;
    
    setHasUnsavedChanges(true);
    const timer = setTimeout(() => {
      onSave(true);
    }, 3000);

    return () => clearTimeout(timer);
  }, [nodes, edges, onSave]);

  const onStart = async () => {
    try {
      // 执行前先保存
      await onSave();
      
      toast.info('工作流执行中...', {
        description: `执行顺序: ${nodes.length} 个节点`,
      });
      
      const run = await websocketService.startRun(currentWorkflowId);
      if (run?.run_id) {
        toast.success('工作流已启动', { description: `Run ID: ${run.run_id}` });
      }
    } catch (error) {
      console.error('Start failed:', error);
      toast.error('执行失败', {
        description: error instanceof Error ? error.message : '未知错误',
      });
    }
  };

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      if (!reactFlowWrapper.current || !reactFlowInstance) return;

      const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
      const actionData = JSON.parse(event.dataTransfer.getData('application/reactflow'));

      if (typeof actionData === 'undefined' || !actionData) {
        return;
      }

      const actionRef = actionData.action_ref || actionData.id;
      const [appId, moduleId, actionId] = actionRef.split('.');

      const position = reactFlowInstance.project({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      });

      const newNode: Node = {
        id: crypto.randomUUID(),
        type: 'plugin',
        position,
        data: {
          label: actionData.name || actionId || actionRef,
          plugin_id: actionData.plugin_id || actionRef,
          app_id: actionData.app_id || appId,
          module_id: actionData.module_id || moduleId,
          action_id: actionData.action_id || actionId,
          action_ref: actionRef,
          device_id: deviceId ?? null,
          status: 'idle',
          config: {},
        },
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [reactFlowInstance, setNodes, deviceId]
  );

  const onUpdateNodeConfig = useCallback((nodeId: string, config: Record<string, any>) => {
    setNodes((nds) =>
      nds.map((node) =>
        node.id === nodeId
          ? { ...node, data: { ...node.data, config } }
          : node
      )
    );
  }, [setNodes]);

  return (
    <div className="flex w-full h-full bg-transparent">
      {/* Sidebar */}
      <PluginSidebar />

      {/* Main Editor Area */}
      <div className="flex-1 relative overflow-hidden" ref={reactFlowWrapper}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onPaneClick={() => setSelectedNodeId(null)}
          onInit={setReactFlowInstance}
          onDrop={onDrop}
          onDragOver={onDragOver}
          nodeTypes={nodeTypes}
          fitView
          className="bg-ios-bg"
        >
          <Background color="#D1D1D6" gap={24} size={1} />
          
          <Controls
            showInteractive={false}
            className="!bg-ios-surface/60 !backdrop-blur-2xl !border-white/40 !shadow-2xl !rounded-3xl !m-6 overflow-hidden !border"
          />
          
          {/* Top Toolbar */}
          <Panel position="top-right" className="flex items-center gap-4 p-6">
            {/* Save Status Indicator */}
            <div className={clsx(
              'flex items-center gap-2 px-4 py-2 rounded-full transition-all duration-500',
              'bg-ios-surface/40 backdrop-blur-md border border-white/60 shadow-sm',
              hasUnsavedChanges ? 'opacity-100' : 'opacity-60'
            )}>
              <div className={clsx(
                'w-1.5 h-1.5 rounded-full',
                isSaving ? 'bg-amber-400 animate-pulse' : (hasUnsavedChanges ? 'bg-blue-400' : 'bg-emerald-400')
              )} />
              <span className="text-[9px] font-bold uppercase tracking-tighter text-gray-500">
                {isSaving ? 'Saving...' : (hasUnsavedChanges ? 'Unsaved Changes' : `Saved ${lastSaved?.toLocaleTimeString() || ''}`)}
              </span>
            </div>

            <button
              onClick={() => onSave(false)}
              disabled={isSaving}
              className={clsx(
                'group flex items-center gap-2.5 px-6 py-3 rounded-[24px] font-bold text-[10px] tracking-widest transition-all',
                'bg-ios-surface/80 backdrop-blur-xl text-gray-900 shadow-[0_12px_24px_-8px_rgba(0,0,0,0.1)]',
                'border border-white/60 hover:bg-ios-surface active:scale-95 disabled:opacity-50'
              )}
            >
              <Save size={14} className={clsx('transition-transform group-hover:scale-110', isSaving && 'animate-pulse')} />
              <span>保存</span>
            </button>

            <button
              onClick={onStart}
              className={clsx(
                'group flex items-center gap-2.5 px-8 py-3 rounded-[24px] font-bold text-[10px] tracking-widest transition-all',
                'bg-ios-accent text-ios-on-accent shadow-[0_20px_40px_-12px_rgba(0,0,0,0.4)]',
                'hover:opacity-90 active:scale-95'
              )}
            >
              <Zap size={14} fill="currentColor" className="transition-transform group-hover:scale-110 group-hover:rotate-12" />
              <span>执行</span>
            </button>
          </Panel>

          {/* Bottom Actions */}
          <Panel position="bottom-left" className="p-6">
             <button
               onClick={() => setShowClearConfirm(true)}
               className="p-4 rounded-full bg-ios-surface/40 backdrop-blur-xl border border-white/60 text-rose-500 shadow-lg hover:bg-rose-50 transition-all active:scale-90"
             >
               <Trash2 size={20} />
             </button>
          </Panel>
        </ReactFlow>

        <ConfirmModal
          isOpen={showClearConfirm}
          title="清空画布"
          description="确定要清空所有节点吗？此操作不可撤销。"
          confirmText="清空"
          cancelText="取消"
          isDanger
          onConfirm={() => {
            setNodes([]);
            setEdges([]);
            setShowClearConfirm(false);
          }}
          onCancel={() => setShowClearConfirm(false)}
        />

        {/* Empty State Guidance */}
        {nodes.length === 0 && (
          <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
            <div className="flex flex-col items-center gap-6 animate-in fade-in zoom-in duration-700">
              <div className="w-24 h-24 rounded-[40px] bg-ios-surface/40 backdrop-blur-2xl border border-white/60 shadow-[0_32px_64px_-16px_rgba(0,0,0,0.08)] flex items-center justify-center">
                <Plus size={32} className="text-gray-300" />
              </div>
              <div className="text-center space-y-2">
                <h3 className="text-lg font-extrabold tracking-tight text-gray-900">开始设计</h3>
                <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">从侧边栏拖动插件开始</p>
              </div>
            </div>
          </div>
        )}

        {/* Node Configuration Panel */}
        <NodeConfigPanel
          node={selectedNode}
          deviceName={moduleName}
          onClose={() => setSelectedNodeId(null)}
          onDelete={onDeleteNode}
          onUpdateConfig={onUpdateNodeConfig}
        />

        {/* Execution Log Panel */}
        <Panel position="bottom-right" className="p-6 pointer-events-auto">
          <WorkflowLog />
        </Panel>
      </div>
    </div>
  );
};

const WorkflowEditor: React.FC<WorkflowEditorProps> = (props) => (
  <ReactFlowProvider>
    <WorkflowEditorContent {...props} />
  </ReactFlowProvider>
);

export default WorkflowEditor;
