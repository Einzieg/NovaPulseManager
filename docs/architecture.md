# Architecture

NovaPulseManager now separates transport, application services, domain objects,
and infrastructure adapters.

Dependency direction:

```text
backend/core/api + backend/core/websocket -> backend/application -> backend/domain
backend/application -> backend/models + backend/infrastructure
backend/infrastructure -> concrete plugin/realtime implementations
backend/plugins -> domain action/runtime contracts
```

Key runtime concepts:

- Device: emulator or ADB target stored in `DeviceConfig`.
- Application: automation app package discovered by `PluginCatalog`.
- Module: application feature group.
- Action: smallest workflow executable unit, referenced by `app.module.action`.
- WorkflowRun: in-memory run lifecycle exposed by `RunService`.
- EventBus + WebSocketHub: realtime run/node/log events.

Legacy compatibility remains available through deprecated HTTP routes and
`LegacyPluginActionAdapter`.
