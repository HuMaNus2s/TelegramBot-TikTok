# logger.py — минимальная рабочая версия

import structlog
from structlog import get_logger
from structlog.contextvars import merge_contextvars
from structlog.processors import (
    add_log_level,
    format_exc_info,
    StackInfoRenderer,
    TimeStamper,
)

structlog.configure(
    processors=[
        merge_contextvars,
        add_log_level,
        StackInfoRenderer(),
        format_exc_info,
        TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
        structlog.dev.ConsoleRenderer(colors=True),  # красиво в терминале
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

log = get_logger("myapp")

# Тест
if __name__ == "__main__":
    log.info("Тест прошёл", version="1.0")
    try:
        1 / 0
    except Exception:
        log.exception("Деление на ноль")