"""Quick compatibility check for the project's supported Python version.

Run after installing dependencies with `uv sync --frozen`.
"""

import sys


def check() -> bool:
    print(f"Python version: {sys.version}")

    if sys.version_info < (3, 14):
        print(
            "⚠️  Warning: Expected Python 3.14, got "
            f"{sys.version_info.major}.{sys.version_info.minor}"
        )
        return False

    print("✅ Python 3.14 detected")

    critical_packages = [
        "fastapi",
        "pydantic",
        "sqlalchemy",
        "redis",
        "celery",
        "langchain_core",
    ]
    missing = []

    for package in critical_packages:
        try:
            __import__(package)
            print(f"✅ {package} available")
        except ImportError:
            missing.append(package)
            print(f"❌ {package} NOT available")

    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("   Run: uv sync --frozen")
        return False

    print("\n✅ All critical packages are available for Python 3.14")
    return True


if __name__ == "__main__":
    sys.exit(0 if check() else 1)
