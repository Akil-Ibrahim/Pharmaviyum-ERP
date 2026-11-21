# Runbook релиза Demo в FastAPI Cloud

## Область действия

FastAPI Cloud размещает только публичную Demo Pharmaviyum. GitHub Actions выполняет CI; workflow .github/workflows/deploy-fastapi-cloud.yml запускается вручную и развёртывает только изолированное приложение Demo. Production использует тот же технологический стек приложения на отдельно управляемой платформе хостинга. Deployment Production, миграции и эксплуатационная автоматизация находятся за пределами этого публичного репозитория.

Этот runbook описывает workflow Demo и не утверждает, что deployment уже завершился успешно или что Production readiness подтверждена.

## Предварительные условия развёртывания Demo

- Создано отдельное приложение Demo в FastAPI Cloud и связано с этим репозиторием.
- В защищённом GitHub Actions environment demo-pharmaviyum-erp настроены FASTAPI_CLOUD_DEMO_TOKEN и FASTAPI_CLOUD_DEMO_APP_ID.
- DEMO_DATABASE_URL указывает только на изолированную Demo БД.
- Переменные приложения Demo настроены согласно [руководству FastAPI Cloud Demo](../deployment/FASTAPI_CLOUD.ru.md).
- Для Demo отдельно provisioned PostgreSQL с pgvector и managed Redis.
- В Demo используются только синтетические данные.

## Процесс релиза Demo

1. Создайте pull request в main.
2. Проверьте изменения и дождитесь успешного завершения обязательных GitHub Actions checks.
3. Выполняйте merge только после прохождения обязательных проверок.
4. Вручную запустите Deploy Demo to FastAPI Cloud из main с утверждённым Demo change reference.
5. Пройдите approval Demo environment, если он настроен.
6. Проверьте deployment status и logs.
7. Проверьте /version, /health, /ready, негативный сценарий авторизации, frontend routes и защиту POS.

Отправка deployment-команды не означает успешный rollout. Workflow должен подтвердить точный commit SHA и staging runtime profile, используемый Demo.

## Безопасность Demo БД

Публичный workflow deployment Demo выполняет read-only проверку совместимости схемы и не запускает Alembic migrations. Изменение схемы Demo требует отдельной утверждённой операции, backup/restore evidence и post-migration validation. Никогда не используйте Production credentials или данные в Demo.

## Ограничения runtime, которые необходимо учитывать

- Native FastAPI Cloud deployment автоматически не устанавливает исполняемый файл Tesseract и OCR language packs из Dockerfile.
- Celery/background jobs требуют отдельного worker process и не запускаются web deployment workflow.
- PostgreSQL/pgvector и Redis-compatible infrastructure provisioned отдельно от web application.
- Перед каждым релизом Demo сверяйте имена environment variables с активными application settings.

## Граница Production

Публичный runbook и его workflows не развёртывают, не мигрируют и не администрируют Production. Хостинг Production и release procedures управляются отдельно с соблюдением применимых ограничений конфиденциальности.
