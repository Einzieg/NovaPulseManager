from __future__ import annotations

from copy import deepcopy
from typing import Any

from backend.infrastructure.plugins.legacy_adapter import LEGACY_ACTION_REF_MAP


def normalize_workflow_graph(graph: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(graph)
    if normalized.get("schema_version") == 2:
        return normalized

    for node in normalized.get("nodes", []):
        plugin_id = node.get("plugin_id")
        if plugin_id and "action_ref" not in node:
            action_ref = LEGACY_ACTION_REF_MAP.get(plugin_id)
            if action_ref:
                app_id, module_id, action_id = action_ref.split(".", 2)
                node["type"] = "action"
                node["app_id"] = app_id
                node["module_id"] = module_id
                node["action_id"] = action_id
                node["action_ref"] = action_ref

    normalized["schema_version"] = 2
    return normalized
