from pathlib import Path

# Keep the retired environment name out of workflow files. Build it from
# fragments so this guard does not match itself.
forbidden = "Production – " + "pharmaviyum-erp"
workflow_dir = Path(".github/workflows")
matches = []

for path in sorted((*workflow_dir.rglob("*.yml"), *workflow_dir.rglob("*.yaml"))):
    content = path.read_text(encoding="utf-8")
    if forbidden in content:
        matches.append(str(path))

if matches:
    print("ERROR: retired GitHub Environment reference detected:")
    for path in matches:
        print(f" - {path}")
    raise SystemExit(1)

print("Environment guard passed: retired production environment is not referenced.")
