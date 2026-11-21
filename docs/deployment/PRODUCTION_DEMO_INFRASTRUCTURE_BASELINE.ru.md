## Единый baseline инфраструктуры Production и Demo

Это каноническая политика версий инфраструктуры для hosted Production и Demo. Не переносите устаревшие версии БД, Redis или ссылки на выведенных из эксплуатации провайдеров из исторических заметок в новые deployment-конфигурации.

| Компонент | Baseline Production | Baseline Demo | Подтверждение / правило |
|---|---|---|---|
| Размещение приложения | FastAPI Cloud | FastAPI Cloud | Hosted-приложение развёртывается защищённым workflow с ручным approval. |
| PostgreSQL | Neon PostgreSQL 18, проект `pharmaviyum-production`, ID проекта `odd-fog-77928192`, default branch `production` | Отдельная изолированная БД/branch PostgreSQL 18 | Production-проект и major-версия проверены в Neon 21.11.2026. Изоляцию Demo и фактическую версию её сервера необходимо проверить до заявления о готовности Demo. |
| Векторное расширение | Целевая версия pgvector 0.8.7; фактическую версию проверить в hosted-БД | Целевая версия pgvector 0.8.7; фактическую версию проверить | Версия PostgreSQL и версия расширения pgvector — разные параметры. |
| Redis | Managed Redis integration; целевая совместимая версия Redis 8.8.4, если провайдер позволяет зафиксировать её | Отдельная managed Redis integration; та же цель Redis 8.8.4 | Точная версия managed-сервера контролируется провайдером и здесь независимо не подтверждена. Проверять через `INFO server` или metadata провайдера; не выдавать target за фактическую версию. |
| Redis-клиент приложения | redis-py 8.1.0 | redis-py 8.1.0 | Зафиксирован в `pyproject.toml` и `uv.lock`. |
| Python runtime | CPython 3.15.0 | CPython 3.15.0 | Зафиксирован в `pyproject.toml`, `.python-version` и deployment checks. |

### Разделение окружений и правила данных

- Production и Demo обязаны использовать разные database credentials, экземпляры/branches БД, Redis credentials/endpoints, signing secrets и provider/API credentials. Demo никогда не должен подключаться к Production БД или Redis namespace.
- В Demo разрешены только синтетические данные. Запрещено импортировать реальные данные пациентов, рецепты, клиентов, аптечные транзакции и конфиденциальную бизнес-информацию.
- Neon Production — авторитетная hosted-реляционная БД. Локальный PostgreSQL в Compose предназначен только для disposable development/CI и не является Production-БД.
- Managed Redis — эфемерный слой cache/coordination, а не авторитетный ledger продаж, отпуска, остатков или аудита. Постоянные бизнес-записи хранятся в PostgreSQL.
- Connection strings и credentials хранятся только в FastAPI Cloud environment variables и защищённых GitHub Actions secrets. В документации разрешено указывать провайдера, проект, branch и версию, но запрещено публиковать credentials и URL подключения.
- Целевая версия не доказывает, что именно она запущена. Для каждого окружения подтвердите фактическую версию сервера, версию расширения, connectivity, backup/PITR policy и readiness.
- Смена major-версии PostgreSQL требует отдельного утверждённого плана backup, проверки совместимости, миграции, тестового восстановления, maintenance window и rollback. Нельзя подключать существующий data volume к другой major-версии PostgreSQL.
- Не используйте выведенную из эксплуатации инфраструктуру Render как действующую зависимость Production или Demo.

Запись live-проверки обновляется при каждой замене hosted-БД или cache. См. [руководство FastAPI Cloud](deployment/FASTAPI_CLOUD.ru.md) и [Production operations runbook](operations/PRODUCTION_OPERATIONS_RUNBOOK.ru.md).

