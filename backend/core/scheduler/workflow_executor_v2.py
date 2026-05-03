from __future__ import annotations

import logging
from typing import Any

import networkx as nx

from backend.application.services.workflow_compat import normalize_workflow_graph
from backend.domain.action import ActionExecutionContext
from backend.models import DeviceConfig


class ActionExecutionContextFactory:
    def __init__(
        self,
        *,
        event_bus: Any = None,
        logger: Any = None,
        cancellation_token: Any = None,
    ):
        self.event_bus = event_bus
        self.logger = logger or logging.getLogger(__name__)
        self.cancellation_token = cancellation_token

    async def create(
        self,
        *,
        run_id: str,
        workflow_id: str | None,
        node: dict[str, Any],
    ) -> ActionExecutionContext:
        device_id = int(node.get("device_id") or 0)
        device = None
        device_name = str(node.get("device_name") or "")
        if device_id:
            device = DeviceConfig.get_or_none(DeviceConfig.id == device_id)
            if device is not None:
                device_name = device.name

        node_config = dict(node.get("config") or {})

        return ActionExecutionContext(
            run_id=run_id,
            workflow_id=workflow_id,
            node_id=node.get("id"),
            device_id=device_id,
            device_name=device_name,
            device=device,
            app_id=node["app_id"],
            module_id=node["module_id"],
            action_id=node["action_id"],
            action_ref=node["action_ref"],
            app_config={},
            module_config={},
            action_config={},
            node_config=node_config,
            effective_config=dict(node_config),
            event_bus=self.event_bus,
            logger=self.logger,
            cancellation_token=self.cancellation_token,
        )


class WorkflowExecutorV2:
    def __init__(
        self,
        *,
        workflow_data: dict[str, Any],
        run_id: str,
        app_runtime_manager,
        action_factory,
        context_factory: ActionExecutionContextFactory,
    ):
        self.workflow_data = normalize_workflow_graph(workflow_data)
        self.run_id = run_id
        self.app_runtime_manager = app_runtime_manager
        self.action_factory = action_factory
        self.context_factory = context_factory
        self.logger = logging.getLogger(__name__)
        self.graph = self._build_dag()
        self.execution_order = list(nx.topological_sort(self.graph))

    def _build_dag(self) -> nx.DiGraph:
        graph = nx.DiGraph()

        for node in self.workflow_data.get("nodes", []):
            graph.add_node(node["id"], **node)

        for edge in self.workflow_data.get("edges", []):
            graph.add_edge(edge["source"], edge["target"])

        if not nx.is_directed_acyclic_graph(graph):
            raise ValueError("工作流程包含周期——DAG结构无效")

        return graph

    async def execute(self) -> None:
        workflow_id = self.workflow_data.get("id")

        for node_id in self.execution_order:
            node = dict(self.graph.nodes[node_id])
            if node.get("type") != "action":
                continue

            ctx = await self.context_factory.create(
                run_id=self.run_id,
                workflow_id=workflow_id,
                node=node,
            )

            await self.app_runtime_manager.ensure_app_ready(
                device_id=ctx.device_id,
                app_id=ctx.app_id,
                ctx=ctx,
            )

            action = self.action_factory.create(ctx.action_ref, ctx)
            try:
                await action.prepare()
                await action.execute()
            finally:
                await action.cleanup()

    def get_execution_order(self) -> list[str]:
        return self.execution_order.copy()
