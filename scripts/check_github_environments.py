import re
from pathlib import Path

CANONICAL_ENVIRONMENT = "production-pharmaviyum-erp"
workflow_dir = Path(".github/workflows")
errors = []

# GitHub environment names are case-insensitive. Validate the literal spelling
# in every job-level environment declaration so a differently-cased alias
# cannot silently become the documented production name.
environment_name = re.compile(
    r"^\s{6}environment:\s*\n\s{8}name:\s*([A-Za-z0-9_.-]+)\s*$",
    re.MULTILINE,
)

for path in sorted((*workflow_dir.rglob("*.yml"), *workflow_dir.rglob("*.yaml"))):
    content = path.read_text(encoding="utf-8")
    for match in environment_name.finditer(content):
        actual = match.group(1)
        if actual != CANONICAL_ENVIRONMENT:
            errors.append(f"{path}: expected {CANONICAL_ENVIRONMENT!r}, found {actual!r}")

if errors:
    print("ERROR: non-canonical GitHub Environment reference detected:")
    for error in errors:
        print(f" - {error}")
    raise SystemExit(1)

print(
    "Environment guard passed: every declared production environment uses "
    f"the canonical name {CANONICAL_ENVIRONMENT!r}."
)
