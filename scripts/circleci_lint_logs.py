#!/usr/bin/env python3
"""Collect failed CircleCI output and optionally publish it to GitHub.

CircleCI always writes the diagnostic report to circleci-diagnostics.log and
uploads it as an artifact. When GITHUB_TOKEN is configured, the report is
also committed to the dedicated ci-diagnostics branch so it can be inspected
through the repository API without modifying dev/main.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

V1_BASE_URL = "https://circleci.com/api/v1.1"
V1_PROJECT_SLUG = "github/Akil-Ibrahim/Pharmaviyum-CRM"
GITHUB_REPOSITORY = "Akil-Ibrahim/Pharmaviyum-CRM"
DIAGNOSTICS_BRANCH = "ci-diagnostics"
USER_AGENT = "pharmaviyum-circleci-diagnostics/3.0"
OUTPUT_FILE = Path("circleci-diagnostics.log")


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


def publish_to_github() -> None:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN is not configured; keeping diagnostics as an artifact.")
        return

    subprocess.run(
        ["git", "config", "user.name", "CircleCI Diagnostics"],
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "circleci-diagnostics@users.noreply.github.com"],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "config",
            "credential.helper",
            "!f() { echo username=x-access-token; echo password=$GITHUB_TOKEN; }; f",
        ],
        check=True,
    )
    subprocess.run(
        ["git", "fetch", "origin", f"refs/heads/{DIAGNOSTICS_BRANCH}:refs/remotes/origin/{DIAGNOSTICS_BRANCH}"],
        check=False,
    )

    branch_exists = subprocess.run(
        ["git", "show-ref", "--verify", f"refs/remotes/origin/{DIAGNOSTICS_BRANCH}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0

    if branch_exists:
        subprocess.run(
            ["git", "checkout", "-B", DIAGNOSTICS_BRANCH, f"origin/{DIAGNOSTICS_BRANCH}"],
            check=True,
        )
    else:
        subprocess.run(
            ["git", "checkout", "-B", DIAGNOSTICS_BRANCH],
            check=True,
        )

    subprocess.run(["git", "add", str(OUTPUT_FILE)], check=True)
    subprocess.run(
        ["git", "commit", "-m", f"ci: update diagnostics for build {os.environ.get('CIRCLE_BUILD_NUM', 'unknown')}"],
        check=False,
    )
    subprocess.run(
        ["git", "push", "origin", f"HEAD:{DIAGNOSTICS_BRANCH}"],
        check=True,
    )
    print(f"Diagnostics published to {GITHUB_REPOSITORY}:{DIAGNOSTICS_BRANCH}")


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
                log.write(f"\n--- Failed step output: {name} / {status} ---\n")
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
    try:
        publish_to_github()
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"GitHub diagnostics publication failed: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
