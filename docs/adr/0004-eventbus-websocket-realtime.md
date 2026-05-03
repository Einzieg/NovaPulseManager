# ADR 0004: EventBus + WebSocket Realtime

Accepted.

Realtime state changes are published to `EventBus`. `WebSocketHub` subscribes
and broadcasts events to connected clients. WebSocket is for realtime push, not
primary CRUD/RPC transport.
