# Pharmaviyum PostgreSQL Backup & Restore

Pharmaviyum uses CircleCI to create encrypted PostgreSQL backups and stores them as **GitHub Release Assets** in the private repository. This avoids GitHub Actions minutes and does not require a separate storage provider.

## Architecture

```
Render PostgreSQL
      |
      | pg_dump -Fc
      v
CircleCI scheduled backup
      |
      | AES-256 encrypted dump
      v
Private GitHub Release Asset
      |
      | selected release
      v
CircleCI restore -> PostgreSQL
```

GitHub supports release assets through its Releases API. Each release asset can be up to 2 GiB.

The dump is **not committed to Git history**. It is uploaded only as a release asset.

## Required CircleCI variables

Configure these as protected project/environment variables or in a restricted CircleCI context:

- `DATABASE_URL` — Render PostgreSQL connection string.
- `GITHUB_REPOSITORY` — `ibrahimengpy/Pharmaviyum-CRM`.
- `GITHUB_BACKUP_TOKEN` — fine-grained GitHub token with repository Contents write permission so CircleCI can create releases and upload assets.
- `BACKUP_ENCRYPTION_KEY` — strong secret used to encrypt/decrypt the database dump.

Never commit database URLs, GitHub tokens, encryption keys, or backup files to Git.

## Automatic schedule

Create a CircleCI **Schedule Trigger** for the `main` branch with:

`run_backup=true`

A daily schedule is recommended.

GitHub Actions is deliberately not used for backups, preserving the project's Actions minutes.

## Backup

The backup job:

1. Creates a PostgreSQL custom-format dump with `pg_dump`.
2. Encrypts the dump with AES-256-CBC + PBKDF2.
3. Creates a prerelease tagged `db-backup-YYYYMMDDTHHMMSSZ`.
4. Uploads the encrypted `.dump.enc` file as the release asset.
5. Removes the local temporary files.

A release asset is limited to 2 GiB, so the job fails safely if the encrypted dump reaches that limit. citeturn0search2

## Restore

Restore only into a disposable/new target database unless replacement has been explicitly approved.

Required variables:

- `DATABASE_URL`
- `GITHUB_REPOSITORY`
- `GITHUB_BACKUP_TOKEN`
- `BACKUP_TAG`
- `BACKUP_ENCRYPTION_KEY`
- `ALLOW_DESTRUCTIVE_RESTORE=true`

Run:

```bash
./scripts/restore_from_github_release.sh
```

The script locates the selected GitHub Release, downloads its encrypted asset through the GitHub Releases API, decrypts it, and runs `pg_restore --clean --if-exists`.

GitHub's Releases API supports creating releases and uploading/deleting release assets.

## Retention

Backups remain available until their GitHub Releases/assets are deleted. The initial implementation does not automatically delete old backups.

For production, keep a defined retention policy (for example, 90 daily backups) and add automated cleanup after the backup flow has been validated.

## Important

This is a practical zero-cost interim backup design for the current project. GitHub recommends storing generated files outside Git itself, which is why the database dumps are release assets rather than repository files.

For a future enterprise deployment, move long-term backups to dedicated object storage with immutable retention, separate credentials, and an independent failure domain.

Redis remains a cache/queue and is not treated as the source of truth.
