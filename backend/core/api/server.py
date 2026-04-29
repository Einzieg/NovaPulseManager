from __future__ import annotations

import logging

import uvicorn

_logger = logging.getLogger(__name__)


class _HealthCheckFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        return "/api/v1/health" not in msg


async def start_api_server(app, host: str, port: int) -> None:
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    logging.getLogger("uvicorn.access").addFilter(_HealthCheckFilter())
    server = uvicorn.Server(config)
    _logger.info("FastAPI server starting on %s:%s", host, port)
    await server.serve()

