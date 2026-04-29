import asyncio
import logging
from typing import Any, Dict, List, Optional

import networkx as nx

from backend.core.NovaException import TaskAbortedError, TaskCompleted
from backend.core.plugins.manager import PluginManager


class WorkflowExecutor:
    """工作流执行器,管理基于DAG的多插件顺序执行"""

    def __init__(
        self,
        workflow_data: dict,
        plugin_manager: PluginManager,
        ws_server=None,
        module_name: str = None,
    ):
        """初始化工作流执行器。

        Args:
            workflow_data: 工作流数据,包含nodes和edges
            plugin_manager: 插件管理器实例
            ws_server: WebSocket服务器实例,用于状态推送
            module_name: 模块名称
        """

        self.workflow_data = workflow_data
        self.plugin_manager = plugin_manager
        self.ws_server = ws_server
        self.module_name = module_name or workflow_data.get("module_name", "unknown")
        self.logger = logging.getLogger(__name__)

        # 构建DAG并计算执行顺序
        self.graph = self._build_dag()
        self.execution_order = list(nx.topological_sort(self.graph))

        self.logger.info(f"WorkflowExecutor 初始化为 {len(self.execution_order)} 节点")

    def _build_dag(self) -> nx.DiGraph:
        """构建有向无环图(DAG)。

        Returns:
            networkx.DiGraph: 构建的有向图

        Raises:
            ValueError: 如果工作流包含环路
        """

        graph = nx.DiGraph()

        # 添加节点
        for node in self.workflow_data.get("nodes", []):
            graph.add_node(node["id"], **node)

        # 添加边(表示依赖关系)
        for edge in self.workflow_data.get("edges", []):
            graph.add_edge(edge["source"], edge["target"])

        # 验证无环性
        if not nx.is_directed_acyclic_graph(graph):
            raise ValueError("工作流程包含周期——DAG结构无效")

        self.logger.info(
            f"DAG 成功构建 {graph.number_of_nodes()} 节点 和 {graph.number_of_edges()} 边界"
        )
        return graph

    async def execute(self) -> None:
        """按拓扑排序顺序执行所有节点。

        Raises:
            Exception: 如果任何节点执行失败
        """

        self.logger.info(f"启动工作流程执行: {self.workflow_data.get('name', 'Unnamed')}")

        for node_id in self.execution_order:
            node = self.graph.nodes[node_id]
            plugin_id = node.get("plugin_id")

            if not plugin_id:
                self.logger.warning(f"节点 {node_id} 没有 plugin_id, 跳过")
                continue

            self.logger.info(f"执行节点 {node_id} (插件: {plugin_id})")
            await self._notify_status(node_id, "running")

            try:
                plugin = self.plugin_manager.load_plugin(plugin_id, self.module_name)
                await plugin.prepare()

                try:
                    await plugin.execute()
                except TaskCompleted as e:
                    self.logger.info(f"节点 {node_id} 正常结束: {e}")
                finally:
                    try:
                        await plugin.cleanup()
                    except Exception as cleanup_error:
                        self.logger.error(
                            f"节点 {node_id} cleanup 失败: {cleanup_error}",
                            exc_info=True,
                        )

                await self._notify_status(node_id, "completed")
                self.logger.info(f"节点 {node_id} 成功完成")

            except TaskAbortedError as e:
                error_msg = str(e)
                self.logger.warning(f"节点 {node_id} 中止: {error_msg}")
                await self._notify_status(node_id, "failed", error_msg)
                raise  # 终止整个工作流执行

            except Exception as e:
                error_msg = str(e)
                self.logger.error(f"节点 {node_id} 失败: {error_msg}", exc_info=True)
                await self._notify_status(node_id, "failed", error_msg)
                raise  # 终止整个工作流执行

        self.logger.info("工作流执行成功完成")

    async def _notify_status(
        self,
        node_id: str,
        status: str,
        error: Optional[str] = None,
    ) -> None:
        """通过WebSocket推送节点执行状态到前端。

        Args:
            node_id: 节点ID
            status: 状态 (running|completed|failed)
            error: 错误信息(可选)
        """

        if not self.ws_server:
            return

        payload: dict[str, Any] = {
            "module_name": self.module_name,
            "workflow_id": self.workflow_data.get("id", "unknown"),
            "node_id": node_id,
            "status": status,
        }

        if error:
            payload["error"] = error

        try:
            await self.ws_server.broadcast("workflow.node_status", payload)
            self.logger.debug(f"节点发送状态更新 {node_id}: {status}")
        except Exception as e:
            self.logger.error(f"未能发送状态更新: {e}")

    def get_execution_order(self) -> List[str]:
        """获取节点执行顺序"""

        return self.execution_order.copy()

    def validate(self) -> Dict[str, Any]:
        """验证工作流有效性。"""

        issues = []

        # 检查是否有节点
        if not self.workflow_data.get("nodes"):
            issues.append("Workflow has no nodes")

        # 检查孤立节点
        for node in self.workflow_data.get("nodes", []):
            node_id = node["id"]
            if self.graph.degree(node_id) == 0:
                issues.append(f"Node {node_id} is isolated (no connections)")

        # 检查插件是否存在
        for node in self.workflow_data.get("nodes", []):
            plugin_id = node.get("plugin_id")
            if not plugin_id:
                issues.append(f"Node {node['id']} has no plugin_id")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "node_count": len(self.execution_order),
            "execution_order": self.execution_order,
        }
