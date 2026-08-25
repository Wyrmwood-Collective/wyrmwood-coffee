import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from pythonjsonlogger.json import JsonFormatter

from wyrmwood_coffee.settings import settings


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
    logging.basicConfig(level=settings.log_level, handlers=[handler])
