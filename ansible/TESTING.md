# Ansible Testing Guide

## Supported toolchain

Use the repository-pinned controller toolchain rather than installing floating latest versions:

```bash
python -m pip install -r requirements.txt
ansible-galaxy collection install -r requirements.yml
```

The CI controller currently uses Python 3.14.10. Tool versions are pinned in `requirements.txt`; update them through a reviewed dependency change.

## Run the test suite

Run from the `ansible/` directory:

```bash
./scripts/test.sh
```

The script runs the repository's YAML lint, Ansible lint, syntax/guardrail checks and configured Molecule tests. A successful local run is useful evidence, but the protected GitHub Actions checks remain the merge gate.

## Molecule

The default scenario targets the Docker-role test container named `pharmaviyum-ansible-test`:

```bash
molecule test -s default
molecule test -s default -- --debug
```

For an iterative development cycle:

```bash
molecule converge -s default
molecule idempotence -s default
molecule verify -s default
molecule destroy -s default
```

To open the test container after a successful converge:

```bash
molecule login -s default -h pharmaviyum-ansible-test
```

Molecule uses a privileged Docker container with systemd for the current Docker-role scenario. Run it only in an isolated CI runner or disposable development environment; never point it at a pharmacy host.

## Fleet and recovery guardrails

Run these from `ansible/`:

```bash
# A 100-site inventory is allowed as an architecture fixture;
# the selected execution wave is capped at 10 by default.
bash tests/test_fleet_selection.sh

# Synthetic localhost-only inventories; no pharmacy host is contacted.
bash tests/test_recovery_guardrails.sh
bash tests/test_offsite_backup_guardrails.sh
```

These scripts test preflight/guardrail behavior. They do not prove that a real fleet, remote backup repository, or disaster-recovery procedure is operational.

## Lint and syntax checks

```bash
yamllint -c .yamllint .
ansible-lint --profile production
pre-commit run --all-files
```

Use check mode only for tasks/modules that implement it meaningfully:

```bash
ansible-playbook -i inventory/lab/hosts.yml playbooks/deploy.yml \
  --limit pharmacy-edge-lab-01 --check --diff
```

Check mode is not a substitute for a disposable lab run. Review any task that uses `command`, `shell`, external APIs, Docker operations or handlers separately because check-mode prediction may be incomplete.

## CI workflows

The repository already defines Ansible CI workflows; do not create a duplicate workflow from an old example:

- `.github/workflows/ansible.yml` runs the broader Ansible quality/test pipeline.
- `.github/workflows/ansible-quality.yml` runs the focused quality and syntax checks.

Inspect the workflow files for the current triggers, Python version, pinned dependencies and exact test commands. CI results must be green before merging Ansible changes.

## Production safety

- Always pass the intended inventory explicitly; do not rely on the production default in `ansible.cfg`.
- Use a synthetic/local inventory for guardrail tests and the isolated lab inventory for Molecule or deployment validation.
- Never run production deployment, migration, backup, restore or rollback as part of a documentation/test command.
- Keep Vault passwords and all credentials in a protected secret store; never put them in shell arguments, committed files or CI logs.
- Treat a clean second run (idempotence) as a required acceptance signal for configuration roles, while documenting tasks that are intentionally state-changing.
