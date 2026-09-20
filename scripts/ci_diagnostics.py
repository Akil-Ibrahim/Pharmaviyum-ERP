#!/usr/bin/env python3
"""Collect deterministic CI diagnostics into one machine-readable report."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPORT = Path("ci-diagnostics")
REPORT.mkdir(exist_ok=True)
OUT = REPORT / "latest.log"

COMMANDS = [
    ("ruff", ["ruff", "check", "src", "tests"]),
    ("black", ["black", "--check", "--diff", "src", "tests"]),
    ("isort", ["isort", "--check-only", "--diff", "--profile", "black", "src", "tests"]),
    ("mypy", ["mypy", "--explicit-package-bases", "src/pharmaviyum/"]),
]

def run(name: str, command: list[str]) -> dict[str, Any]:
    process = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "name": name,
        "command": " ".join(command),
        "returncode": process.returncode,
        "stdout": process.stdout,
        "stderr": process.stderr,
    }

def main() -> int:
    results = [run(name, command) for name, command in COMMANDS]
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }
    OUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with OUT.open("a", encoding="utf-8") as stream:
        stream.write("\n\n===== HUMAN-READABLE SUMMARY =====\n")
        for result in results:
            stream.write(
                f"[{result['name']}] exit={result['returncode']}\n"
                f"{result['stdout']}{result['stderr']}\n"
            )

    return 0 if all(result["returncode"] == 0 for result in results) else 1

if __name__ == "__main__":
    raise SystemExit(main())
