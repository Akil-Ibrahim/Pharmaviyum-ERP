# Развёртывание Demo Pharmaviyum в FastAPI Cloud

Это руководство описывает только развёртывание публичной Demo. Workflow .github/workflows/deploy-fastapi-cloud.yml не должен обращаться к Production. Хостинг Production, credentials развёртывания, release automation, миграции БД и эксплуатационные процедуры управляются за пределами этого публичного репозитория.

## 1. Граница окружений

- Публичный адрес Demo: https://pharmaviyum-erp.fastapicloud.dev.
- Demo размещается в FastAPI Cloud и использует изолированные сервисы PostgreSQL/pgvector и Redis.
- В Demo разрешены только синтетические данные. Запрещено подключать Demo к Production БД, Redis, identity providers, signing secrets или API credentials.
- Приложение поддерживает runtime-значения development, staging и production. Для hosted Demo используется ENVIRONMENT=staging: это включает безопасный staging/production-grade профиль, но не означает, что Demo является Production.
- Production использует тот же технологический стек приложения, за исключением хостинга и развёртывания: они выполняются на отдельно управляемой платформе. Сведения о провайдере и операции Production находятся за пределами этого репозитория.

## 2. Workflow развёртывания Demo

Workflow запускается вручную из main. Он собирает frontend, проверяет CI для точного выбранного commit, выполняет read-only проверку схемы изолированной Demo БД, развёртывает приложение в Demo FastAPI Cloud и запускает HTTP smoke checks.

Порядок:

Pull Request -> обязательные CI и security checks -> merge в main -> ручной запуск Deploy Demo to FastAPI Cloud -> approval Demo environment (если настроен) -> deployment и Demo smoke checks -> проверка логов и live Demo.

Push или merge сами по себе не запускают deployment. Этот workflow не развёртывает Production и не выполняет Alembic migrations.

## 3. GitHub Actions secrets

Настройте следующие secrets в защищённом GitHub Actions environment demo-pharmaviyum-erp:

- FASTAPI_CLOUD_DEMO_TOKEN — deploy token, предназначенный для приложения Demo.
- FASTAPI_CLOUD_DEMO_APP_ID — ID приложения Demo в FastAPI Cloud.
- DEMO_DATABASE_URL — URL изолированной Demo БД; используется для read-only проверки совместимости схемы.
- VITE_CLERK_PUBLISHABLE_KEY — необязательный публичный frontend build key, только если он нужен текущей конфигурации входа.

Не используйте Production credentials и не направляйте Demo secrets на Production-ресурсы. Workflow намеренно не читает FASTAPI_CLOUD_APP_ID, FASTAPI_CLOUD_TOKEN, DATABASE_URL или secrets Production environment.

## 4. Конфигурация Demo в FastAPI Cloud

Настройте переменные приложения Demo отдельно от Production:

| Переменная | Требование для Demo |
|---|---|
| ENVIRONMENT | staging — поддерживаемый безопасный runtime-профиль Demo |
| DEBUG | false |
| LOG_LEVEL | INFO |
| DATABASE_URL | URL изолированной Demo PostgreSQL в async-формате |
| PGVECTOR_DATABASE_URL | URL Demo PostgreSQL/pgvector |
| REDIS_URL | Отдельный endpoint managed Redis для Demo |
| SECRET_KEY | Уникальный секрет только для Demo, не менее 32 символов |
| CORS_ORIGINS | Точный HTTPS origin Demo |
| USE_CLOUD_LLM | true, если включён AI-профиль Demo |
| CLOUD_LLM_PROVIDER | qwencloud для описанного Demo-профиля |
| Переменные QwenCloud | Demo API key, endpoint, model, timeout и quota guard согласно руководству QwenCloud Demo |

База Demo, vector store и Redis должны быть provisioned независимо. FastAPI Cloud не создаёт эти сервисы автоматически. Фактические версии hosted-БД и расширения проверяются отдельно; целевые версии совместимости нельзя выдавать за наблюдаемые версии.

## 5. Ручная процедура deployment

1. Влейте проверенное изменение в main после успешного прохождения обязательных CI checks.
2. Откройте workflow Deploy Demo to FastAPI Cloud в GitHub Actions.
3. Запустите workflow вручную из main, указав утверждённый Demo change/ticket reference.
4. Пройдите approval для environment demo-pharmaviyum-erp, если он настроен.
5. Убедитесь, что workflow завершился успешно, и проверьте live Demo.

Workflow checkout-ит точный выбранный commit и добавляет его SHA в build metadata; собирает React frontend и подготавливает static assets; ожидает успешного CI именно для этого commit из main; проверяет только Demo deploy token, app ID и database URL; read-only запросами проверяет Alembic heads Demo и наличие обязательной inventory ledger table; отправляет deployment в FastAPI Cloud; ожидает, пока /version подтвердит ожидаемый commit, staging для core/application/auth environments, выключенный debug и CPython 3.15.0; проверяет /health, /ready, frontend SPA routes, обработку неверных credentials и защиту POS.

Workflow должен завершаться ошибкой, если отсутствует любой обязательный Demo secret или live runtime не соответствует ожидаемому commit и Demo profile.

## 6. Миграции БД и безопасность данных

Workflow развёртывания Demo не запускает Alembic migrations. Изменения схемы требуют отдельной проверки и утверждения операции над Demo БД, подтверждённого backup/restore path и post-migration validation.

Production migrations и операции над Production БД не выполняются этим workflow и не настраиваются через этот публичный репозиторий. Не переносите Production connection strings, migration credentials или environment variables в Demo.

Успешный deployment не импортирует каталог лекарств и не создаёт аптечные бизнес-данные автоматически. Используйте только документированные процедуры импорта и проверки синтетических данных.

## 7. Ограничения runtime и эксплуатации

- Workflow фиксирует CPython 3.15.0; фактическую версию после deployment необходимо проверить через /version.
- Native FastAPI Cloud автоматически не устанавливает системные OCR-пакеты из Dockerfile. OCR нужно проверять отдельно или использовать внешний OCR service.
- Celery workers/Beat и внешние OTLP collectors этим web deployment workflow не запускаются.
- Успешный CI или deployment не доказывает production readiness всех аптечных процессов, AI provider quota, OCR, workers, Edge/offline mode или целевой capacity.

## 8. Правила безопасности

- Используйте отдельные credentials Demo с минимально необходимыми правами.
- В Demo разрешены только синтетические данные; не размещайте реальные данные пациентов, рецепты, клиентов или аптечные транзакции.
- Не публикуйте secrets, connection strings и неотредактированные operational logs.
- Не обходите branch protection, CI, environment approvals и release gates.
- Никогда не используйте этот workflow для развёртывания или изменения Production.
