# ADR 0003: Workflow Run Model

Accepted.

Starting a workflow creates a `run_id`. `RunService` tracks run state and
enforces one active run per device/module name.
