from typing import Any

from sqlalchemy import Select, Update, Delete, Insert
from sqlalchemy.dialects import mysql


def parse_to_list(value: Any, separator: str = ",") -> list[str]:
    if isinstance(value, str):
        if separator in value:
            return [v.strip() for v in value.split(separator) if v.strip()]
        return [value.strip()]
    elif isinstance(value, list):
        return [str(v).strip() for v in value]
    else:
        raise ValueError(f"Cannot parse value to list: {value}")


def parse_stmt_to_str(stmt: Select | Update | Delete | Insert) -> str:
    compiled = stmt.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True})
    return compiled.string
