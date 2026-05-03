# API

Resource API:

- `GET /api/v1/apps`
- `GET /api/v1/actions`
- `GET /api/v1/devices`
- `POST /api/v1/devices`
- `PATCH /api/v1/devices/{device_id}`
- `DELETE /api/v1/devices/{device_id}`
- `GET /api/v1/workflows?module_name=...`
- `POST /api/v1/workflows`
- `GET /api/v1/workflows/{workflow_id}`
- `PATCH /api/v1/workflows/{workflow_id}`
- `DELETE /api/v1/workflows/{workflow_id}`
- `POST /api/v1/workflows/{workflow_id}/runs`
- `GET /api/v1/runs`
- `GET /api/v1/runs/{run_id}`
- `POST /api/v1/runs/{run_id}/cancel`

Deprecated compatibility API remains registered for the legacy frontend and
old scripts. Deprecated routes are marked in Swagger.

WebSocket `/ws` is retained for realtime events:

- `run.status_changed`
- `workflow.node_status`
- `module.status`
- `log`
