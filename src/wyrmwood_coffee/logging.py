import contextvars
import logging
from datetime import datetime
from functools import cache
from typing import Any
from zoneinfo import ZoneInfo

from pydantic import BaseModel
from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers import JsonLexer
from pythonjsonlogger.json import JsonFormatter
from sqlalchemy.orm import InstrumentedAttribute

REDACTED = "***REDACTED***"


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


class Sensitive:
    """Marker for fields that must be redacted before logging.

    Usage: `password: Annotated[str, Sensitive]`
    """


@cache
def sensitive_field_names() -> set[str]:
    """Field names marked `Sensitive` across every known Pydantic model."""
    from wyrmwood_coffee.settings import Settings

    names: set[str] = set()
    seen: set[type[BaseModel]] = set()
    stack = [*BaseModel.__subclasses__(), Settings]
    while stack:
        model = stack.pop()
        if model in seen:
            continue
        seen.add(model)
        stack.extend(model.__subclasses__())
        for name, field_info in model.model_fields.items():
            if Sensitive in field_info.metadata:
                names.add(name)
    return names


def _redact_value(value: Any, names: set[str]) -> Any:
    if isinstance(value, dict):
        return {
            key: (REDACTED if key in names else _redact_value(val, names))
            for key, val in value.items()
        }
    if isinstance(value, list):
        return [_redact_value(item, names) for item in value]
    return value


def redact_dict(
    data: dict[str, Any], sensitive_names: set[str] | None = None
) -> dict[str, Any]:
    """Mask any key in `data` known to be sensitive, at any nesting depth."""
    names = sensitive_field_names() if sensitive_names is None else sensitive_names
    return _redact_value(data, names)


class ResourceLogger:
    """
    A wrapper for logging.Logger

    Defines common logging operations related to resource lifecyle events.
    """

    def __init__(self, logger: logging.Logger, resource_class: type):
        self.logger = logger
        self.resource_name = resource_class.__name__

    def _log_result(self, msg: str, **kwargs):
        extra: dict = {"resource_type": self.resource_name} | kwargs
        self.logger.info(msg, stacklevel=3, extra=extra)

    def log_resource_created(self, resource_id: int):
        self._log_result("Resource created", resource_id=resource_id)

    def log_resource_updated(self, resource_id: int):
        self._log_result("Resource updated", resource_id=resource_id)

    def log_resource_patched(self, resource_id: int, fields_modified: set[str]):
        self._log_result(
            "Resource patched",
            resource_id=resource_id,
            fields_modified=sorted(fields_modified),
        )

    def log_resource_deleted(self, resource_id: int):
        self._log_result("Resource deleted", resource_id=resource_id)

    def log_resource_not_found(self, resource_id: int):
        self._log_result("Resource not found", resource_id=resource_id)

    def log_attrs_not_unique(self, attributes: list[InstrumentedAttribute]):
        self._log_result(
            "Attribute combination not unique",
            attributes=[str(prop) for prop in attributes],
        )

    def log_deletion_conflict(
        self, resource_id: int, rule: str, conflicts: dict[type, list[int]]
    ):
        self._log_result(
            "Resource deletion blocked by conflict",
            resource_id=resource_id,
            rule=rule,
            conflicts=[
                {"model": model.__name__, "ids": ids}
                for model, ids in conflicts.items()
            ],
        )


class AppJsonFormatter(JsonFormatter):
    def formatTime(self, record, datefmt=None):
        return datetime.fromtimestamp(
            record.created, tz=ZoneInfo("America/Chicago")
        ).isoformat()


class DevJsonFormatter(AppJsonFormatter):
    """Pretty-prints and colors log output for local development."""

    def format(self, record: logging.LogRecord) -> str:
        return highlight(super().format(record), JsonLexer(), Terminal256Formatter())


def setup_logging():
    from wyrmwood_coffee.settings import Environment, settings

    fmt = "%(asctime)s %(levelname)s %(name)s %(module)s %(funcName)s %(lineno)d %(message)s"  # noqa: E501
    rename_fields = {
        "asctime": "timestamp",
        "levelname": "level",
        "name": "logger",
        "module": "module",
        "funcName": "function",
        "lineno": "line",
    }

    handler = logging.StreamHandler()
    if settings.app_environment == Environment.DEV:
        handler.setFormatter(
            DevJsonFormatter(fmt, rename_fields=rename_fields, json_indent=2)
        )
    else:
        handler.setFormatter(AppJsonFormatter(fmt, rename_fields=rename_fields))
    handler.addFilter(RequestContextFilter())
    logging.basicConfig(level=settings.log_level, handlers=[handler])
