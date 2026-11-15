# Runbook релиза FastAPI Cloud

## Область действия

FastAPI Cloud — платформа hosted deployment приложения. GitHub Actions выполняет CI; отдельный workflow `.github/workflows/deploy-fastapi-cloud.yml` запускается вручную и развёртывает приложение при наличии обязательной конфигурации. Каноническая integration/release branch — `main`.

Этот документ описывает workflow репозитория. Он не утверждает, что deployment уже завершился успешно или production readiness подтверждена.

## Предварительные условия deployment

- Создано приложение FastAPI Cloud и связано с репозиторием/проектом.
- Настроены GitHub Actions secrets: `FASTAPI_CLOUD_TOKEN` и `FASTAPI_CLOUD_APP_ID`.
- Безопасно заданы обязательные FastAPI Cloud environment variables; см. [Runbook FastAPI Cloud](../deployment/FASTAPI_CLOUD.ru.md).
- Отдельно provisioned PostgreSQL с pgvector и доступный Redis-compatible service.
- До production traffic миграции БД однократно применены из доверенного окружения.
- Настроена frontend build configuration, включая Clerk publishable key, если включён соответствующий sign-in route.

## Процесс релиза

1. Создайте pull request в `main`.
2. Проверьте изменения и дождитесь успешного завершения обязательных GitHub Actions checks.
3. Выполняйте merge только после прохождения обязательных проверок.
4. Когда нужен релиз, вручную запустите workflow `Deploy to FastAPI Cloud`.
5. Проверьте deployment status и logs в FastAPI Cloud: отправленный deployment не обязательно успешен.
6. До использования реальных аптечных данных проверьте `/health`, `/ready`, authentication, доступность БД, критические аптечные процессы и AI requests.
7. При ошибке остановите promotion, изучите build/runtime logs и используйте поддерживаемый FastAPI Cloud recovery process после определения неисправной revision.

## Безопасность БД

Миграции — прямые изменения production. Предпочитайте backward-compatible expand/contract migrations. Не полагайтесь на автоматический schema downgrade как основной способ rollback. Для отдельно provisioned БД поддерживайте backup и проверенные restore procedures.

## Ограничения runtime, которые необходимо учитывать

- Native FastAPI Cloud deployment автоматически не устанавливает исполняемый файл Tesseract и OCR language packs из Dockerfile.
- Celery/background jobs требуют отдельного worker process и не запускаются web deployment workflow.
- PostgreSQL/pgvector и Redis-compatible infrastructure существуют отдельно от web deployment.
- Перед каждым релизом сверяйте имена environment variables с активными application settings.

## Текущий статус

В репозитории есть workflow ручного deployment в FastAPI Cloud. Production readiness остаётся неподтверждённой до проверки CI, deployment smoke tests, backup/restore, observability, работы background workers и recovery procedures.
