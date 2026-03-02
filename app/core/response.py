"""Unified API response model.

Every endpoint returns the same JSON shape::

    {
        "code": 0,
        "message": "success",
        "data": ...
    }

Use ``Result.ok(data)`` / ``Result.fail(code, msg)`` as convenience
constructors, or return a ``Result(...)`` directly.
"""

from typing import Any

from pydantic import BaseModel


class Result(BaseModel):
    """Standard response envelope."""

    code: int = 0
    message: str = "success"
    data: Any | None = None

    @classmethod
    def ok(cls, data: Any = None, message: str = "success") -> "Result":
        """Shorthand for a successful response."""
        return cls(code=0, message=message, data=data)

    @classmethod
    def fail(cls, code: int, message: str = "error", data: Any = None) -> "Result":
        """Shorthand for a failed response."""
        return cls(code=code, message=message, data=data)
