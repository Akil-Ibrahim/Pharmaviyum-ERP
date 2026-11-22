# Ansible Testing Guide

## Supported toolchain

The Ansible controller currently uses CPython 3.14.10. Install the versions declared by the repository:

```bash
python -m pip install -r requirements.txt
ansible-galaxy collection install -r requirements.yml
```

The Python package versions for Ansible, ansible-core, ansible-lint, yamllint and Molecule are pinned in `requirements.txt`. **The Galaxy collections in `requirements.yml` currently have no version constraints**, and the CI workflows upgrade pip before installation. Therefore the complete Ansible controller toolchain is not yet fully reproducible: collection or bootstrap-tool versions may change between runs. Treat collection pinning and pip bootstrap pinning as outstanding release-engineering work; do not describe the entire Ansible toolchain as fully pinned until those inputs are locked and reviewed. Update pins through a reviewed dependency change.

## Run the test suite

Run from the `ansible/` directory:

```bash
./scripts/test.sh
```

The validation helper is fail-closed (`set -Eeuo pipefail`) and stops at the first failed stage. It runs YAML lint, production-profile Ansible lint, fleet/recovery/off-site-backup guardrail scripts, syntax checks for every top-level playbook against the isolated Lab inventory, and the default Molecule scenario. A zero exit status means each of these stages completed successfully in that local environment; it does not prove that a real pharmacy host, remote backup repository, or Production deployment is operational. CI remains the required merge gate.

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

Molecule uses a privileged Docker container with systemd for the current Docker-role scenario. This is a disposable container test, not a real remote Pharmacy Edge server. Run it only in an isolated CI runner or disposable development environment; never point it at a pharmacy host.

## Real Lab host (separate from Molecule)

The repository has a separate inventory at `inventory/lab/hosts.yml`. It expects these runtime environment variables: `PHARMAVIYUM_LAB_EDGE_HOST`, `PHARMAVIYUM_LAB_EDGE_USER`, and `PHARMAVIYUM_LAB_POSTGRES_PASSWORD`, plus the release inputs and Docker package pins required by the playbook. The inventory file alone does not prove that a lab VM exists or that credentials are configured.

The current GitHub Actions workflows do **not** SSH to this host or run the deployment playbook against it. `ansible-quality.yml` only uses the lab inventory for syntax checks; that does not establish remote connectivity or deployment success. A real lab deployment is a separate, explicitly approved operation, and must only be run after verifying that the environment variables point to a disposable, non-production lab host.

From the `ansible/` directory, after the lab host and protected runtime variables have been provisioned:

```bash
ansible-playbook -i inventory/lab/hosts.yml playbooks/deploy.yml --limit pharmacy-edge-lab-01
```

Do not run this command in CI until a dedicated protected Lab environment, scoped credentials, approval gate, and safe teardown/recovery procedure are in place.

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
- Use synthetic/local inventories for guardrail tests, Molecule's own Docker inventory for container tests, and `inventory/lab/hosts.yml` only for an explicitly approved real Lab host run.
- Never run production deployment, migration, backup, restore or rollback as part of a documentation/test command.
- Keep Vault passwords and all credentials in a protected secret store; never put them in shell arguments, committed files or CI logs.
- Treat a clean second run (idempotence) as a required acceptance signal for configuration roles, while documenting tasks that are intentionally state-changing.
