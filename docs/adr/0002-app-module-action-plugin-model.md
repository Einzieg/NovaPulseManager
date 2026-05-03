# ADR 0002: App / Module / Action Plugin Model

Accepted.

Plugins are application extension packages. Workflow nodes reference actions by
`{app_id}.{module_id}.{action_id}`. Legacy task plugins are bridged through a
legacy action adapter.
