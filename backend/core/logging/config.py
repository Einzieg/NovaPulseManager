from __future__ import annotations

import logging
from typing import Optional


DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def get_json_formatter() -> logging.Formatter:
    """返回 JSON formatter；若未安装 structlog 则回退到普通 formatter。"""

    try:
        import structlog
        from structlog.processors import JSONRenderer
        from structlog.stdlib import ProcessorFormatter
    except ModuleNotFoundError:
        return logging.Formatter(DEFAULT_LOG_FORMAT)

    foreign_pre_chain = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"),
    ]

    return ProcessorFormatter(
        processor=JSONRenderer(),
        foreign_pre_chain=foreign_pre_chain,
    )


def configure_logging(level: int = logging.INFO) -> None:
    """配置 structlog + stdlib logging，以 JSON 作为统一输出格式。"""

    try:
        import structlog
    except ModuleNotFoundError:
        logging.basicConfig(level=level, format=DEFAULT_LOG_FORMAT)
        return

    shared_processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"),
    ]

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            *shared_processors,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True,
    )

    handler = logging.StreamHandler()
    handler.setFormatter(get_json_formatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)
