#!/usr/bin/env python3

from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent
    project = root / "src"
    tests = root / "tests"

    # Black is required by CI; formatting is enforced in check mode.
    # Run it directly from the repo root.
    import subprocess

    subprocess.run(["python", "-m", "black", str(project), str(tests)], check=True)


if __name__ == "__main__":
    main()
