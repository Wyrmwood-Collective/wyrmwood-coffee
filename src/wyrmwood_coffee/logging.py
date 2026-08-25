import contextvars
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from pythonjsonlogger.json import JsonFormatter

from wyrmwood_coffee.settings import settings

# Holds the current request's context fields (method, path, payload, ...).
# Set once per request by RequestLoggingMiddleware; read by RequestContextFilter
# so every log record emitted during that request picks the fields up automatically.
request_context: contextvars.ContextVar[dict | None] = contextvars.ContextVar(
    "request_context", default=None
)


class RequestContextFilter(logging.Filter):
    """Stamps the current request's context fields onto every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        for key, value in (request_context.get() or {}).items():
            if not hasattr(record, key):
                setattr(record, key, value)
        return True


class AppJsonFormatter(JsonFormatter):
    def formatTime(self, record, datefmt=None):
        return datetime.fromtimestamp(
            record.created, tz=ZoneInfo("America/Chicago")
        ).isoformat()


def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(
        AppJsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(module)s %(funcName)s %(lineno)d %(message)s",  # noqa: E501
            rename_fields={
                "asctime": "timestamp",
                "levelname": "level",
                "name": "logger",
                "module": "module",
                "funcName": "function",
                "lineno": "line",
            },
        )
    )
    handler.addFilter(RequestContextFilter())
    logging.basicConfig(level=settings.log_level, handlers=[handler])
