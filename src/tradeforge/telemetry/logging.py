from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime

from tradeforge.config import get_settings

_logging_configured = False


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        fields = getattr(record, "tradeforge_fields", None)
        if isinstance(fields, dict):
            payload.update(fields)
        return json.dumps(payload, default=str)


def setup_logging(force: bool = False) -> None:
    global _logging_configured
    root_logger = logging.getLogger()
    if _logging_configured and not force:
        return
    settings = get_settings()
    handler = logging.StreamHandler(sys.stderr)
    if settings.log_format == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.log_level.upper())
    _logging_configured = True


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)


def log_event(logger: logging.Logger, level: int, message: str, **fields: object) -> None:
    logger.log(level, message, extra={"tradeforge_fields": fields})
