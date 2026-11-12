# Ansible Testing Guide

## Prerequisites

```bash
pip install molecule molecule-plugins[docker] ansible-lint yamllint pre-commit
```

## Quick Start

### Run All Tests

```bash
./scripts/test.sh
```

### Run Molecule Tests

```bash
# Run the repository's default Docker-role scenario
molecule test -s default

# Test with debug output
molecule test --debug
```

### Test pharmacy fleet selection

```bash
# Verify that a ten-site wave can be selected from a 100-site inventory,
# while an eleven-site wave and a 101-site inventory fail closed.
bash tests/test_fleet_selection.sh
```

### Test restore and rollback recovery guardrails

```bash
# Exercise approval gates using synthetic localhost-only inventories.
bash tests/test_recovery_guardrails.sh
```

### Linting

```bash
# YAML syntax
yamllint -c .yamllint .

# Ansible best practices
ansible-lint --profile production

# Pre-commit hooks
pre-commit run --all-files
```

## Development Workflow

1. **Before commit:**
```bash
   pre-commit install
   pre-commit run --all-files
```

2. **Test changes:**
```bash
   molecule converge  # Quick test without destroy
   molecule verify    # Run verification only
```

3. **Debug:**
```bash
   molecule login -h ubuntu-focal  # SSH into test container
```

## CI/CD Integration

Add to GitHub Actions (`.github/workflows/ansible-test.yml`):

```yaml
name: Ansible Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install molecule molecule-plugins[docker] ansible-lint
      - name: Run tests
        run: ./scripts/test.sh
```
