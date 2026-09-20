#!/usr/bin/env python3
"""Fetch CircleCI job/step output for CI diagnostics.

Usage:
  CIRCLECI_TOKEN=... python scripts/circleci_lint_logs.py 2088

The token is read from CIRCLECI_TOKEN or CIRCLECI_CLI_TOKEN.
It is never printed. For CircleCI Cloud, the project slug is:
  gh/Akil-Ibrahim/Pharmaviyum-CRM
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

BASE_URL = "https://circleci.com/api/v2"
PROJECT_SLUG = "gh/Akil-Ibrahim/Pharmaviyum-CRM"


def get_json(path: str, token: str) -> Any:
    request = urllib.request.Request(
        BASE_URL + path,
        headers={
            "Accept": "application/json",
            "Circle-Token": token,
            "User-Agent": "pharmaviyum-circleci-diagnostics/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"CircleCI API {exc.code}: {body}") from exc


def main() -> int:
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        print(f"Usage: {sys.argv[0]} <circleci-job-number>", file=sys.stderr)
        return 2

    token = os.getenv("CIRCLECI_TOKEN") or os.getenv("CIRCLECI_CLI_TOKEN")
    if not token:
        print(
            "Set CIRCLECI_TOKEN (or CIRCLECI_CLI_TOKEN) before running.",
            file=sys.stderr,
        )
        return 2

    job_number = sys.argv[1]
    job = get_json(f"/project/{PROJECT_SLUG}/job/{job_number}", token)
    steps = get_json(f"/project/{PROJECT_SLUG}/{job_number}/steps", token)

    print("=== CircleCI job ===")
    print(f"number: {job.get('number')}")
    print(f"name: {job.get('name')}")
    print(f"status: {job.get('status')}")
    print(f"started_at: {job.get('started_at')}")
    print(f"stopped_at: {job.get('stopped_at')}")
    print(f"web_url: {job.get('web_url')}")

    print("\n=== Step output URLs ===")
    for step in steps.get("steps", []):
        print(f"\n[{step.get('name')}]")
        for action in step.get("actions", []):
            print(
                f"  status={action.get('status')} "
                f"output_url={action.get('output_url')}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
