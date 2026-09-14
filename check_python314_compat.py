"""
Quick compatibility check for Python 3.14.

Run this before building Docker image to catch issues early:
    python check_python314_compat.py
"""
import sys

def check():
    print(f"Python version: {sys.version}")
    
    if sys.version_info < (3, 14):
        print(f"⚠️  Warning: Expected Python 3.14, got {sys.version_info.major}.{sys.version_info.minor}")
        print("   Some features may not work as expected.")
        return False
    
    print("✅ Python 3.14 detected")
    
    # Check critical imports
    critical_packages = [
        "fastapi",
        "pydantic",
        "sqlalchemy",
        "redis",
        "celery",
        "langchain_core",
    ]
    
    missing = []
    for pkg in critical_packages:
        try:
            __import__(pkg)
            print(f"✅ {pkg} available")
        except ImportError:
            missing.append(pkg)
            print(f"❌ {pkg} NOT available")
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("   Run: pip install -r requirements-ai.txt")
        return False
    
    print("\n✅ All critical packages available for Python 3.14")
    return True


if __name__ == "__main__":
    success = check()
    sys.exit(0 if success else 1)
