from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
MIGRATION_SCRIPT = REPOSITORY_ROOT / "scripts" / "test_migrations.sh"


def run_migration_script(
    tmp_path: Path,
    *,
    database_url: str | None = None,
    migration_url: str | None = "postgresql+asyncpg://postgres:postgres@localhost:5432/pharmaviyum_test",
    allowed_hosts: str | None = None,
    allow_destructive: str | None = "1",
) -> tuple[subprocess.CompletedProcess[str], str]:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_uv = fake_bin / "uv"
    call_log = tmp_path / "uv-calls.log"
    fake_uv.write_text(
        "#!/usr/bin/env bash\n"
        'printf "%s\\n" "$*" >> "$UV_CALL_LOG"\n',
        encoding="utf-8",
    )
    fake_uv.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env.get('PATH', '')}"
    env["UV_CALL_LOG"] = str(call_log)
    env.pop("DATABASE_URL", None)
    env.pop("MIGRATION_TEST_DATABASE_URL", None)
    env.pop("MIGRATION_TEST_ALLOWED_HOSTS", None)
    env.pop("ALLOW_DESTRUCTIVE_MIGRATION_TESTS", None)

    if database_url is not None:
        env["DATABASE_URL"] = database_url
    if migration_url is not None:
        env["MIGRATION_TEST_DATABASE_URL"] = migration_url
    if allowed_hosts is not None:
        env["MIGRATION_TEST_ALLOWED_HOSTS"] = allowed_hosts
    if allow_destructive is not None:
        env["ALLOW_DESTRUCTIVE_MIGRATION_TESTS"] = allow_destructive

    result = subprocess.run(
        [str(MIGRATION_SCRIPT)],
        cwd=REPOSITORY_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    return result, call_log.read_text(encoding="utf-8") if call_log.exists() else ""


@pytest.mark.unit
def test_migration_lifecycle_allows_local_disposable_database(tmp_path: Path) -> None:
    result, calls = run_migration_script(tmp_path)

    assert result.returncode == 0, result.stderr
    assert "pharmaviyum_test" in result.stdout
    assert calls.count("run --locked alembic current") == 2
    assert "run --locked alembic upgrade head" in calls
    assert "run --locked alembic downgrade base" in calls


@pytest.mark.unit
def test_migration_lifecycle_rejects_remote_host_without_exact_allowlist(
    tmp_path: Path,
) -> None:
    result, calls = run_migration_script(
        tmp_path,
        migration_url="postgresql+asyncpg://user:secret@db.example.net:5432/pharmaviyum_test",
    )

    assert result.returncode == 2
    assert "is not loopback" in result.stderr
    assert calls == ""


@pytest.mark.unit
def test_migration_lifecycle_allows_explicitly_allowlisted_remote_test_host(
    tmp_path: Path,
) -> None:
    result, calls = run_migration_script(
        tmp_path,
        migration_url="postgresql+asyncpg://user:secret@db.example.net:5432/pharmaviyum_test",
        allowed_hosts="other.example.net, db.example.net",
    )

    assert result.returncode == 0, result.stderr
    assert "db.example.net" in result.stdout
    assert "run --locked alembic downgrade base" in calls


@pytest.mark.unit
def test_migration_lifecycle_rejects_database_name_without_test_token(
    tmp_path: Path,
) -> None:
    result, calls = run_migration_script(
        tmp_path,
        migration_url="postgresql+asyncpg://user:secret@localhost:5432/pharmaviyum_contest",
    )

    assert result.returncode == 2
    assert "distinct 'test' or 'testing' token" in result.stderr
    assert calls == ""


@pytest.mark.unit
def test_migration_lifecycle_requires_explicit_destructive_opt_in(
    tmp_path: Path,
) -> None:
    result, calls = run_migration_script(tmp_path, allow_destructive=None)

    assert result.returncode == 2
    assert "ALLOW_DESTRUCTIVE_MIGRATION_TESTS=1" in result.stderr
    assert calls == ""


@pytest.mark.unit
def test_migration_lifecycle_never_falls_back_to_database_url(tmp_path: Path) -> None:
    result, calls = run_migration_script(
        tmp_path,
        migration_url=None,
        database_url="postgresql+asyncpg://user:secret@localhost:5432/pharmaviyum_test",
    )

    assert result.returncode == 2
    assert "MIGRATION_TEST_DATABASE_URL is required" in result.stderr
    assert calls == ""
