# Pharmaviyum PostgreSQL Backup & Restore

Pharmaviyum includes a portable PostgreSQL backup/restore mechanism designed for the Render Free PostgreSQL 30-day limitation.

Render Free Postgres does not provide managed backups and expires after 30 days. The application therefore must export the database to storage outside Render before the database expires. See the Render documentation for the current Free Postgres limitations.

## Architecture

```
Render PostgreSQL
      |
      | pg_dump -Fc
      v
CircleCI scheduled backup
      |
      | S3-compatible object storage
      v
Long-term backup archive
```

The repository provides:

- `scripts/backup_to_s3.sh` — creates a PostgreSQL custom-format dump and uploads it.
- `scripts/restore_from_s3.sh` — downloads a selected dump and restores it.
- CircleCI backup workflow — can be triggered automatically by a CircleCI Schedule Trigger or manually with `run_backup=true`.

GitHub Actions is deliberately not used for backups, preserving the project's GitHub Actions minutes.

## Required CircleCI variables

Set these as protected project/environment variables or in a restricted CircleCI context:

- `DATABASE_URL` — Render PostgreSQL external connection string.
- `BACKUP_S3_URI` — e.g. `s3://my-bucket/pharmaviyum/postgres`.
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_DEFAULT_REGION`

For S3-compatible providers such as Cloudflare R2, also set:

- `AWS_S3_ENDPOINT_URL`

Never commit database URLs, access keys, secret keys, or backup files to Git.

## Automatic schedule

Create a CircleCI **Schedule Trigger** for the `main` branch and set the pipeline parameter:

`run_backup=true`

A daily schedule is appropriate for this mechanism. CircleCI Schedule Triggers are configured in the CircleCI project settings; they do not consume GitHub Actions minutes.

## Manual backup

Run the CircleCI pipeline with:

`run_backup=true`

The backup job will create a timestamped `.dump` file and upload it to the configured object-storage prefix.

## Restore

1. Create a new PostgreSQL database.
2. Set `DATABASE_URL` to the target database.
3. Set `BACKUP_OBJECT` to the exact object name, for example `pharmaviyum_20260922T020000Z.dump`.
4. Set `ALLOW_DESTRUCTIVE_RESTORE=true`.
5. Run the restore command:

```bash
./scripts/restore_from_s3.sh
```

The restore uses `pg_restore --clean --if-exists`, so the target database must be treated as disposable or explicitly approved for replacement.

## Important

The backup mechanism is portable and protects the database beyond Render's 30-day Free Postgres lifetime, but it does not automatically create an external storage account or credentials. Those must be configured once in CircleCI.

Redis is separate: Render Free Key Value is in-memory and can lose its contents on restart. The application should therefore treat Redis as a cache/queue, not the source of truth.
