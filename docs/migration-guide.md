# Migration Guide

## Workflow storage

`Workflow.graph_json` is the v2 graph source. During database initialization,
legacy `workflow_data` rows are normalized to schema v2 and copied into
`graph_json`. Row counts are preserved.

## Legacy workflow nodes

Legacy node `plugin_id` values are mapped as follows:

```text
start_task / start-task       -> nova_iron_galaxy.startup.launch
permanent_task / permanent-task -> nova_iron_galaxy.permanent.run
order_task / order-task       -> nova_iron_galaxy.order.run
radar_task / radar-task       -> nova_iron_galaxy.radar.run
```

## Deprecated APIs

Old RPC-style HTTP routes remain available but are marked deprecated. New code
should use the resource API documented in `docs/api.md`.

## Legacy tables

`Module` and legacy `PluginConfig` tables are no longer created by default.
Set `NOVA_INIT_LEGACY_TABLES=1` or call `init_database(include_legacy=True)` only
for legacy migration tools.
