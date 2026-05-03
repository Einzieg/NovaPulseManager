# Plugin Development

New plugins are application extension packages:

```text
backend/plugins/{app_id}/
  manifest.json
  runtime.py
  modules/{module_id}/
    manifest.json
    actions.py
```

Application manifests use `kind = "application"` and declare a runtime class.
Module manifests use `kind = "module"` and declare actions. Each action gets a
global reference:

```text
{app_id}.{module_id}.{action_id}
```

Action classes inherit `backend.domain.action.ActionBase`. Runtime classes
inherit `backend.domain.app.AppRuntimeBase`.

Legacy task plugins under `backend/plugins/*_task` remain supported through
`backend.infrastructure.plugins.legacy_adapter.LegacyPluginActionAdapter`.
