# Workflow Schema v2

Workflow graphs use `schema_version: 2`.

Action node shape:

```json
{
  "id": "node-1",
  "type": "action",
  "app_id": "nova_iron_galaxy",
  "module_id": "permanent",
  "action_id": "run",
  "action_ref": "nova_iron_galaxy.permanent.run",
  "device_id": 1,
  "position": { "x": 100, "y": 100 },
  "config": {}
}
```

Legacy workflow nodes with `plugin_id` are normalized by
`backend/application/services/workflow_compat.py`. The legacy `plugin_id` is
kept for compatibility, while action fields are added.

Stored workflows use `Workflow.graph_json` for v2 graphs. `workflow_data`
remains as a legacy compatibility copy during migration.
