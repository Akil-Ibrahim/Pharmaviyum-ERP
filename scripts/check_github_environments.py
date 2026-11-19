from pathlib import Path
import re

# GitHub automatically creates an Environment when a workflow references a
# previously unknown name. Keep production references on a strict allowlist so
# retired spellings cannot silently recreate deleted Environments.
ALLOWED_PRODUCTION_ENVIRONMENT = "production-pharmaviyum-erp"
workflow_dir = Path(".github/workflows")
errors = []

for path in sorted((*workflow_dir.rglob("*.yml"), *workflow_dir.rglob("*.yaml"))):
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"^(?P<indent>\s*)environment\s*:\s*(?P<value>.*)$", line)
        if not match:
            continue

        indent = len(match.group("indent"))
        value = match.group("value").strip()
        if value:
            # Scalar environment declarations are not permitted for production
            # workflows: use an explicit, reviewable name mapping.
            if "production" in value.lower():
                errors.append(f"{path}:{index + 1}: production environment must use an explicit name mapping")
            continue

        environment_name = None
        for child_index in range(index + 1, len(lines)):
            child = lines[child_index]
            if not child.strip() or child.lstrip().startswith("#"):
                continue
            child_indent = len(child) - len(child.lstrip())
            if child_indent <= indent:
                break
            name_match = re.match(r"^\\s+name\\s*:\\s*(.*?)\\s*$", child)
            if name_match:
                environment_name = name_match.group(1).strip().strip("\\'\\\"")
                break

        if environment_name and "production" in environment_name.lower():
            if environment_name != ALLOWED_PRODUCTION_ENVIRONMENT:
                errors.append(
                    f"{path}:{index + 1}: forbidden production environment "
                    f"{environment_name!r}; only {ALLOWED_PRODUCTION_ENVIRONMENT!r} is allowed"
                )

if errors:
    print("ERROR: retired or unapproved production GitHub Environment reference detected:")
    for error in errors:
        print(f" - {error}")
    raise SystemExit(1)

print(
    "Environment guard passed: production workflows may reference only "
    f"{ALLOWED_PRODUCTION_ENVIRONMENT!r}."
)
