"""Centralized logging configuration with per-request trace ID.

Every log line includes a ``request_id`` so that all entries produced
during a single HTTP request can be correlated.  The ID is propagated
via :pymod:`contextvars` and injected by :class:`RequestIdFilter`.

Usage in any module::

    import logging
    logger = logging.getLogger(__name__)
    logger.info("something happened")  # request_id is added automatically

The middleware in ``main.py`` sets the context var for each request.
"""

import logging
import sys
import uuid
from contextvars import ContextVar

# ── Request context ───────────────────────────────────────────────────────

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


def generate_request_id() -> str:
    """Return a short, unique request identifier."""
    return uuid.uuid4().hex[:12]


# ── Filter ────────────────────────────────────────────────────────────────


class RequestIdFilter(logging.Filter):
    """Inject ``request_id`` from the current context into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get("-")  # type: ignore[attr-defined]
        return True


# ── Setup ─────────────────────────────────────────────────────────────────

_LOG_FORMAT = "%(asctime)s %(levelname)-7s [%(request_id)s] %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: str = "INFO") -> None:
    """Configure the root logger with a consistent format.

    Should be called **once** at application startup (before any log
    output).  After this call every ``logging.getLogger(...)`` in the
    process inherits the format and the :class:`RequestIdFilter`.

    Args:
        level: Root log level name (DEBUG / INFO / WARNING / ERROR).
    """
    root = logging.getLogger()
    root.setLevel(level.upper())

    if root.handlers:
        root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    handler.addFilter(RequestIdFilter())
    root.addHandler(handler)

    # Quiet down noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("watchfiles").setLevel(logging.WARNING)
