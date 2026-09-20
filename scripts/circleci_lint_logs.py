#!/usr/bin/env python3
"""Collect failed CircleCI job output into a single diagnostics artifact.

The generated file is written to ci-diagnostics/circleci-lint.log in the CI
workspace and uploaded by CircleCI as an artifact. Credentials are never
written to the artifact.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

V1_BASE_URL = "https://circleci.com/api/v1.1"
V1_PROJECT_SLUG = "github/Akil-Ibrahim/Pharmaviyum-CRM"
USER_AGENT = "pharmaviyum-circleci-diagnostics/2.0"
OUTPUT_FILE = Path("ci-diagnostics/circleci-lint.log")


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


def fetch_output(output_url: str, token: str) -> list[dict[str, Any]]:
    request = urllib.request.Request(
        output_url,
        headers={
            "Accept": "application/json",
            "Circle-Token": token,
            "User-Agent": USER_AGENT,
        },
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

    token = (
        os.getenv("CIRCLECI_PERSONAL_TOKEN")
        or os.getenv("CIRCLECI_TOKEN")
        or os.getenv("CIRCLECI_CLI_TOKEN")
    )
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as log:
        if not token:
            log.write(
                "CircleCI diagnostics unavailable: no diagnostic token is configured.\n"
            )
            return 0

        job_number = sys.argv[1]
        build_url = f"{V1_BASE_URL}/project/{V1_PROJECT_SLUG}/{job_number}"

        try:
            build = request_json(build_url, token)
        except RuntimeError as exc:
            log.write(f"Failed to fetch CircleCI job metadata: {exc}\n")
            return 0

        log.write("=== CircleCI job ===\n")
        for key in (
            "build_num",
            "status",
            "outcome",
            "lifecycle",
            "fail_reason",
            "start_time",
            "stop_time",
            "build_url",
        ):
            log.write(f"{key}: {build.get(key)}\n")

        log.write("\n=== CircleCI steps ===\n")
        failed = False
        for step in build.get("steps", []):
            for action in step.get("actions", []):
                status = action.get("status")
                exit_code = action.get("exit_code")
                name = step.get("name")
                log.write(
                    f"step={name!r} status={status!r} exit_code={exit_code!r}\n"
                )

                if status not in {"failed", "error", "timed_out"}:
                    continue

                failed = True
                log.write(
                    f"\n--- Failed step output: {name} / {status} ---\n"
                )
                output_url = action.get("output_url")
                if not output_url:
                    log.write("No output URL supplied by CircleCI.\n")
                    continue

                try:
                    output = fetch_output(output_url, token)
                except RuntimeError as exc:
                    log.write(f"Could not fetch output: {exc}\n")
                    continue

                for chunk in output:
                    message = chunk.get("message")
                    if message:
                        log.write(
                            message,
                            end="" if message.endswith("\n") else "\n",
                        )

        if not failed:
            log.write("\nNo failed step action found.\n")

    print(f"Diagnostics written to {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
