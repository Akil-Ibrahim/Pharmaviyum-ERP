#!/usr/bin/env python3
"""
Script to add auth routers to main.py.

Run this script once to integrate auth module into your application.
Usage: python scripts/add_auth_to_main.py
"""
import re
from pathlib import Path

MAIN_PY_PATH = Path("backend/app/main.py")


def add_auth_routers():
    """Add auth router imports and registrations to main.py."""
    
    if not MAIN_PY_PATH.exists():
        print(f"❌ Error: {MAIN_PY_PATH} not found")
        return False
    
    content = MAIN_PY_PATH.read_text()
    
    # Check if already added
    if "from .modules.auth import login_router, users_router" in content:
        print("ℹ️  Auth routers already added to main.py")
        return True
    
    # Add imports after existing imports
    import_section = """
# Authentication routes (from ibrahimengpy template)
from .modules.auth import login_router, users_router
"""
    
    # Find the last import line and add after it
    lines = content.split('\n')
    last_import_idx = -1
    
    for i, line in enumerate(lines):
        if line.strip().startswith('from ') or line.strip().startswith('import '):
            last_import_idx = i
    
    if last_import_idx == -1:
        print("❌ Could not find imports in main.py")
        return False
    
    # Insert import after last import
    lines.insert(last_import_idx + 1, import_section)
    content = '\n'.join(lines)
    
    # Add router registration
    # Find "app.include_router(patients_router" or similar
    router_pattern = r'(app\.include_router\(\w+router[^)]*\))'
    
    if re.search(router_pattern, content):
        # Add auth routers after the first include_router call
        replacement = r'''\1

# Auth routers (from ibrahimengpy template)
app.include_router(login_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")'''
        
        content = re.sub(router_pattern, replacement, content, count=1)
    else:
        # Append at the end if no routers found
        content += """

# Auth routers (from ibrahimengpy template)
app.include_router(login_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
"""
    
    MAIN_PY_PATH.write_text(content)
    print(f"✅ Auth routers added to {MAIN_PY_PATH}")
    return True


if __name__ == "__main__":
    if add_auth_routers():
        print("\n🎉 Integration complete!")
        print("\nNext steps:")
        print("  1. Run migrations: alembic revision --autogenerate -m 'Add User table'")
        print("  2. Apply migrations: alembic upgrade head")
        print("  3. Create superuser: python scripts/create_superuser.py")
        print("  4. Start app: uvicorn app.main:app --reload")
    else:
        print("\n❌ Integration failed")
