"""Validate the CPython 3.15 runtime and critical application imports.

Run after installing the project with `uv sync --frozen`.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import sys

MINIMUM_VERSION = (3, 15, 0)
MAXIMUM_VERSION = (3, 16)

CRITICAL_PACKAGES = (
    "fastapi",
    "pydantic",
    "sqlalchemy",
    "asyncpg",
    "psycopg",
    "redis",
    "celery",
    "langgraph",
)


def main() -> int:
    current = sys.version_info[:3]
    print(f"Python runtime: {sys.version}")

    if current < MINIMUM_VERSION or current[:2] >= MAXIMUM_VERSION:
        print(
            "ERROR: expected CPython >=3.15,<3.16; 
            f"found {current[0]}.{current[1]}.{current[2]}"
        )
        return 1

    for module in CRITICAL_PACKAGES:
        try:
            importlib.import_module(module)
            package_name = "SQLAlchemy" if module == "sqlalchemy" else module
            version = importlib.metadata.version(package_name)
            print(f"OK {module} {version}")
        except Exception as exc:  # noqa: BLE001 - report any import/runtime incompatibility
            print(f"ERROR {module}: {type(exc).__name__}: {exc}")
            return 1

    print("CPython 3.15 critical dependency compatibility check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
