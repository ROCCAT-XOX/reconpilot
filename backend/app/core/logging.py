"""Structured logging configuration using structlog.

JSON output in production, human-readable in development.
Request-ID tracking through all requests.
"""

import logging
import sys
import uuid
from contextvars import ContextVar

import structlog

# Context variable for request ID tracking
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def add_request_id(logger, method_name, event_dict):
    """Add request_id from context variable to all log entries."""
    req_id = request_id_var.get()
    if req_id:
        event_dict["request_id"] = req_id
    return event_dict


def setup_logging(environment: str = "development", log_level: str = "INFO") -> None:
    """Configure structlog and stdlib logging.

    Args:
        environment: 'production' for JSON, anything else for console.
        log_level: Python log level string.
    """
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        add_request_id,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if environment == "production":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Quiet noisy loggers
    for name in ("uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(name).setLevel(logging.WARNING)


def generate_request_id() -> str:
    """Generate a short request ID."""
    return uuid.uuid4().hex[:12]
