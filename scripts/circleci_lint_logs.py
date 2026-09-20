#!/usr/bin/env python3
"""Fetch CircleCI job logs for CI diagnostics.

Usage:
  CIRCLECI_TOKEN=... python scripts/circleci_lint_logs.py 2088

The token is read from CIRCLECI_TOKEN or CIRCLECI_CLI_TOKEN and is never
printed or committed. The script prints failed step output when available.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

BASE_URL = "https://circleci.com/api/v2"
V1_BASE_URL = "https://circleci.com/api/v1.1"
V2_PROJECT_SLUG = "gh/Akil-Ibrahim/Pharmaviyum-CRM"
V1_PROJECT_SLUG = "github/Akil-Ibrahim/Pharmaviyum-CRM"
USER_AGENT = "pharmaviyum-circleci-diagnostics/1.2"


def request_json(url: str, token: str) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Circle-Token": token,
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"CircleCI API {exc.code}: {body}") from exc


def fetch_output(output_url: str) -> list[dict[str, Any]]:
    request = urllib.request.Request(
        output_url,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"CircleCI output API {exc.code}: {body}") from exc
    return data if isinstance(data, list) else []


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
    job_url = f"{BASE_URL}/project/{V2_PROJECT_SLUG}/job/{job_number}"
    build_url = f"{V1_BASE_URL}/project/{V1_PROJECT_SLUG}/{job_number}"

    job = request_json(job_url, token)
    build = request_json(build_url, token)

    print("=== CircleCI job ===")
    print(f"number: {job.get('number')}")
    print(f"name: {job.get('name')}")
    print(f"status: {job.get('status')}")
    print(f"started_at: {job.get('started_at')}")
    print(f"stopped_at: {job.get('stopped_at')}")
    print(f"web_url: {job.get('web_url')}")

    print("\n=== Failed step output ===")
    failed = False
    for step in build.get("steps", []):
        for action in step.get("actions", []):
            status = action.get("status")
            output_url = action.get("output_url")
            if status not in {"failed", "error", "timed_out"}:
                continue

            failed = True
            print(f"\n--- {step.get('name')} / {status} ---")
            if not output_url:
                print("No output URL supplied by CircleCI.")
                continue

            try:
                output = fetch_output(output_url)
            except RuntimeError as exc:
                print(f"Could not fetch output: {exc}")
                continue

            for chunk in output:
                message = chunk.get("message")
                if message:
                    print(message, end="" if message.endswith("\n") else "\n")

    if not failed:
        print("No failed step action found.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
