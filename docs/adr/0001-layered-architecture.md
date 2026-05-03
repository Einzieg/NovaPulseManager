# ADR 0001: Layered Architecture

Accepted.

Business operations live in `backend/application/services`. Transport adapters
in REST/WebSocket handlers delegate to services and no longer contain direct
Peewee CRUD logic.
