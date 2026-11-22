# Настройка окружения — Pharmaviyum ERP/CRM

Руководство описывает конфигурацию локальной разработки, Demo на FastAPI Cloud и Production на аптечном сервере под управлением Ansible. Секреты храните только в локальных игнорируемых файлах или менеджере секретов. Не добавляйте реальные credentials в Git.

Production работает на аптечном сервере и provision/release выполняется через Ansible; PostgreSQL и supporting services находятся локально в рамках утверждённого Pharmacy Edge deployment profile. Demo размещается в FastAPI Cloud с изолированными Demo data services. Запрещено совместно использовать credentials БД, application secrets, cache namespaces и данные между окружениями. См. [границу развёртывания Production/Demo](../deployment/PRODUCTION_DEMO_INFRASTRUCTURE_BASELINE.ru.md) и [Ansible rollout Pharmacy Edge](../devops/PHARMACY_EDGE_ANSIBLE_ROLLOUT.ru.md).

## 1. Источники конфигурации и приоритет

Используйте источники в следующем порядке:

1. `src/pharmaviyum/core/config.py` и код валидации провайдеров определяют фактические настройки runtime.
2. `.env.example` — шаблон локальной разработки.
3. `.env.prod.example` — пример для Docker/on-premises, а не экспорт секретов FastAPI Cloud.
4. [Runbook FastAPI Cloud](../deployment/FASTAPI_CLOUD.ru.md) — инструкция размещённого приложения.

Приложение читает переменные через Pydantic Settings. Имена переменных чувствительны к регистру: используйте точные имена в верхнем регистре из шаблонов и runbook.

Не создавайте устаревшие файлы `.env.development` или `.env.production`. Для локальной разработки используйте `.env`. Переменные Demo задавайте в изолированном окружении FastAPI Cloud, а credentials Demo deployment — в защищённом GitHub Environment для Demo. Production configuration применяется через проверенный Ansible Pharmacy Edge profile с использованием защищённых per-site secret sources; не помещайте реальные Production values в FastAPI Cloud или публичные GitHub secrets.

## 2. Локальная разработка

Создайте локальный файл из шаблона:

```bash
cp .env.example .env
```

Перед запуском проверьте значения. Шаблон содержит локальные endpoints и демонстрационные значения; не переносите его без изменений в production.

Compose stack репозитория включает PostgreSQL с pgvector, Redis, Ollama, FastAPI, Celery worker/Beat и локальные компоненты OpenTelemetry.

```bash
docker compose up --build
docker compose ps
docker compose logs -f api
```

Локальные адреса:

| Сервис | Адрес |
|---|---|
| FastAPI | `http://localhost:8000` |
| Swagger UI | `http://localhost:8000/docs` |
| OpenAPI schema | `http://localhost:8000/openapi.json` |
| Prometheus metrics | `http://localhost:8000/metrics` |
| Jaeger UI (Compose) | `http://localhost:16686` |
| OTLP/gRPC receiver | `localhost:4317` |
| OTLP/HTTP receiver | `http://localhost:4318` |

Внутри Docker Compose межсервисные подключения должны использовать DNS-имена сервисов (`postgres`, `redis`, `ollama`), а не `localhost`. Процесс, запущенный непосредственно на машине разработчика, обычно использует `localhost` и опубликованные порты. Не смешивайте host и container database URLs.

Полезные команды:

```bash
docker compose down
docker compose logs -f celery-worker
./scripts/test.sh unit
./scripts/test.sh integration
./scripts/test.sh all
uv run --locked ruff check src/
uv run --locked mypy --explicit-package-bases src/pharmaviyum/
```

Не используйте `docker compose down -v`, если намеренно не удаляете локальные тома PostgreSQL, Redis и Ollama.

## 3. Основные переменные приложения

| Переменная | Назначение | Рекомендации |
|---|---|---|
| `ENVIRONMENT` | Окружение | `development`, `staging` или `production` |
| `DEBUG` | Режим отладки | В Demo, staging и Production — `false` |
| `LOG_LEVEL` | Уровень логирования | Обычно `INFO` в production |
| `DATABASE_URL` | Основное подключение PostgreSQL | Async SQLAlchemy URL, обычно `postgresql+asyncpg://...` |
| `PGVECTOR_DATABASE_URL` | PostgreSQL для vector store | Может указывать на ту же БД при подходящих schema/permissions |
| `REDIS_URL` | Подключение Redis | Используйте доступный защищённый endpoint |
| `SECRET_KEY` | Секрет подписи JWT/приложения | В staging/production обязателен, минимум 32 символа |
| `API_SECRET_KEY` | Устаревший alias секрета | Для совместимости; предпочтителен `SECRET_KEY` |
| `CORS_ORIGINS` | Разрешённые browser origins | Точные доверенные origins; не используйте wildcard с credentials |
| `RATE_LIMIT_PER_MINUTE` | Лимит API | Настраивайте под ёмкость deployment |
| `OTEL_ENABLED` | Переключатель OpenTelemetry | Включайте при настроенном collector/exporter |
| `OTEL_SERVICE_NAME` | Идентификатор сервиса telemetry | Стабильное имя |
| `OTEL_EXPORTER_ENDPOINT` | OTLP collector endpoint | Должен быть доступен из runtime |

В production/staging запуск отклоняет отсутствующий или короче 32 символов signing secret. Если заданы оба ключа, каноническим является `SECRET_KEY`.

Сгенерировать секрет можно локально или в утверждённом secret manager:

```bash
openssl rand -hex 32
```

Не отправляйте секреты в чат, исходный код, issue comments или CI logs.

## 4. Профили Mortarium AI

### Локальный / on-premises профиль

Локальный профиль использует Ollama. В текущем примере для генерации выбрана Qwen3.5 9B, для embeddings — `mxbai-embed-large`. Основные переменные:

- `OLLAMA_BASE_URL`
- `OLLAMA_FAST_MODEL`
- `OLLAMA_MAIN_MODEL`
- `OLLAMA_COMPLEX_MODEL`
- `OLLAMA_EMBEDDING_MODEL`

Для Compose используйте hostname `ollama`; для процесса на host — endpoint хоста.

### Демонстрационный профиль QwenCloud

Текущий demo profile использует **только QwenCloud** с моделью `qwen3.8-flash`. Не настраивайте OpenRouter как fallback.

- `USE_CLOUD_LLM=true`
- `CLOUD_LLM_PROVIDER=qwencloud`
- `QWEN_API_KEY` — секрет
- `QWEN_BASE_URL=https://ap-southeast-1.maas.qwencloudapi.com/compatible-mode/v1`
- `QWEN_MODEL=qwen3.8-flash`
- `QWEN_FAST_MODEL=qwen3.8-flash`
- `QWEN_COMPLEX_MODEL=qwen3.8-flash`
- `QWEN_FREE_QUOTA_ONLY=true`
- `QWEN_TIMEOUT_SECONDS=30`
- `QWEN_MAX_OUTPUT_TOKENS=500`

Для защиты от непреднамеренной платной нагрузки нужны два независимых условия:

1. Application guard: `QWEN_FREE_QUOTA_ONLY=true`.
2. В консоли провайдера включён переключатель **Free quota only** для выбранной модели.

Флаг приложения — fail-closed проверка конфигурации. Сам по себе он не проверяет и не ограничивает биллинг/квоту провайдера. Перед демонстрацией проверьте остаток и срок действия квоты. Бесплатная квота не обязательно безлимитна или автоматически обновляется.

QwenCloud отвечает за генерацию. Embeddings настраиваются отдельно: наличие Qwen API key не означает, что embedding endpoint доступен. До включения cloud RAG проверьте embedding provider, credentials, размерность векторов и ingestion/retrieval tests.

Подробности: [Эксплуатация демо QwenCloud](../ai/QWENCLOUD_DEMO.ru.md).

### Другие провайдеры

В `.env.example` могут присутствовать необязательные credentials Gemini, Groq, OpenAI и Anthropic. Их наличие в шаблоне не означает, что они включены в текущий demo profile. Не добавляйте fallback и не меняйте активного провайдера без отдельного архитектурного изменения и тестов.

## 5. RAG, агенты, MCP и наблюдаемость

Mortarium использует LangGraph для оркестрации pharmacist agent и RAG. В проверенном runtime к активному графу подключены настройки:

- `RAG_TOP_K`
- `RAG_MAX_CONTEXT_DOCS`
- `RAG_MAX_REWRITES`
- `RAG_MAX_QUERY_VARIATIONS`
- `RAG_ENABLE_HYDE`
- `RAG_ENABLE_MULTI_QUERY`

Некоторые переменные объявлены в settings или `.env.example`, но пока не являются эффективными runtime controls:

- `RAG_RERANK_TOP_N` — reranker не внедрён;
- `RAG_RRF_K` — hybrid search использует значение метода по умолчанию;
- `RAG_ENABLE_CONTEXTUAL_COMPRESSION` — compression node всегда включён;
- `RAG_MAX_CHUNK_TOKENS` и `RAG_CHUNK_OVERLAP` — Celery worker использует defaults конфигурации задачи;
- `RAG_DEFAULT_LANGUAGES` — ingestion loaders имеют отдельные defaults.

Перед использованием этих параметров изучите [аудит архитектуры Mortarium/RAG](../rag_architecture_audit.ru.md).

Настройки агента включают лимиты итераций/истории и checkpoint configuration. Наличие HITL/safety settings не доказывает, что полный approval workflow включён. MCP-инструменты фильтруются по ролям и требуют доверенного tenant context. Запись запрещена, пока не настроен trusted approval verifier. Права инструментов должны быть минимальными; память диалога и checkpoints необходимо связывать с тем же patient scope, что и запрос.

Зависимости OpenTelemetry и локальные Compose collector/Jaeger включены. Локальный collector удаляет чувствительные URL, SQL, authorization, user, patient, pharmacy и session attributes перед экспортом в Jaeger. Не предполагайте, что такой collector автоматически существует в FastAPI Cloud: для cloud telemetry нужен доступный OTLP endpoint. Не добавляйте patient data, credentials, access tokens или клинический текст в span attributes.

Ragas находится в изолированной evaluation dependency group для CI/offline evaluation и не является обязательной runtime-переменной production.

## 6. Конфигурация FastAPI Cloud для Demo

FastAPI Cloud используется только для публичной Demo. Production использует тот же технологический стек приложения и развёртывается на аптечном сервере через Ansible. Публичные playbooks определяют автоматизацию; реальные host inventory, per-site credentials, SSH access и approvals остаются под контролем оператора и никогда не коммитятся.

Публичное приложение Demo размещается по адресу https://pharmaviyum-erp.fastapicloud.dev. Переменные приложения задаются в панели FastAPI Cloud Environment Variables, а deploy credentials — в защищённом GitHub Actions environment demo-pharmaviyum-erp.

### Переменные приложения Demo

- ENVIRONMENT=staging — поддерживаемый безопасный runtime-профиль приложения Demo.
- DEBUG=false
- LOG_LEVEL=INFO
- DATABASE_URL — URL изолированной Demo PostgreSQL, обычно postgresql+asyncpg://...
- PGVECTOR_DATABASE_URL — URL vector store Demo.
- REDIS_URL — отдельный managed Redis endpoint для Demo.
- SECRET_KEY — уникальный случайный секрет только для Demo, не короче 32 символов.
- CORS_ORIGINS — точный HTTPS origin Demo.
- USE_CLOUD_LLM=true и CLOUD_LLM_PROVIDER=qwencloud, если включён AI-профиль Demo.
- QwenCloud API, model, timeout и quota variables согласно руководству QwenCloud Demo.

Runtime enum приложения поддерживает development, staging и production. Demo использует staging, чтобы не обозначать публичную демонстрационную среду как Production и при этом сохранять безопасную staging-конфигурацию. PostgreSQL/pgvector и Redis provisioned отдельно; FastAPI Cloud автоматически не создаёт эти сервисы.

### GitHub Actions secrets для Demo

Workflow развёртывания Demo требует:

- FASTAPI_CLOUD_DEMO_TOKEN — deploy token FastAPI Cloud только для Demo.
- FASTAPI_CLOUD_DEMO_APP_ID — ID приложения Demo в FastAPI Cloud.
- DEMO_DATABASE_URL — URL изолированной Demo БД для read-only проверки схемы.
- VITE_CLERK_PUBLISHABLE_KEY — только если он нужен frontend build/sign-in конфигурации.

Workflow не должен читать Production credentials или обращаться к Production инфраструктуре. Он читает только указанные Demo-specific secrets; DEMO_DATABASE_URL передаётся в process variable DATABASE_URL для read-only проверки схемы.

### Контроль релиза Demo

1. Влейте проверенное изменение в main после обязательных CI checks.
2. Вручную запустите Deploy Demo to FastAPI Cloud из main с утверждённым Demo change/ticket reference.
3. Пройдите approval для environment demo-pharmaviyum-erp, если он настроен.
4. Проверьте точный deployed commit, staging runtime identity, версию CPython, /health, /ready, frontend routes, обработку неверной авторизации и защиту POS.

Workflow развёртывания Demo не запускает Alembic migrations. Изменение схемы Demo требует отдельной утверждённой операции и проверенного backup/restore path. Deployment и миграции Production выполняются за пределами этого публичного репозитория. См. [руководство по развёртыванию Demo в FastAPI Cloud](../deployment/FASTAPI_CLOUD.ru.md).
## 7. Pharmacy Edge / on-premises

Cloud demo и аптечные Edge nodes — разные профили deployment:

- Edge/on-premises использует локальный Ollama, если он настроен.
- Для каждого Edge node нужны собственные защищённые database/Redis и site identity/credentials.
- Параметры Central sync (`PHARMAVIYUM_EDGE_NODE_ID`, `PHARMAVIYUM_EDGE_TOKEN`, `PHARMAVIYUM_CENTRAL_SYNC_URL`, batch/lease/timeout) задаются отдельно для каждого узла, где развёрнут sync worker.
- POS transaction path должен оставаться локально работоспособным при сбоях WAN/central services; синхронизация асинхронна и не должна зависеть от LLM.
- Не используйте credentials одной аптеки на другом Edge node.

Начальная цель rollout — 1–10 аптек. Архитектура предусматривает дальнейший рост до 100 аптек, но такую ёмкость нельзя заявлять без load, recovery, backup/restore и synchronization tests.

## 8. Миграции БД и безопасность данных

Каноническое дерево Alembic находится в корне репозитория. Публичный workflow развёртывания Demo не применяет миграции.

Изменения схемы Demo требуют отдельной проверки и утверждения операции над изолированной Demo БД, подтверждённого backup/restore path и post-migration validation. Никогда не используйте Production database URL или migration credentials для Demo.

Миграции Production и их автоматизация управляются за пределами этого публичного репозитория. Не добавляйте Production database endpoints, migration secrets или привилегированные Production operations в публичные workflows.

Новая Demo БД пуста. Успешный deployment не импортирует лекарственный каталог, не создаёт остатки и не восстанавливает бизнес-данные. Импортируйте каталог только отдельной проверенной идемпотентной процедурой и только с синтетическими данными.

## 9. Health checks и проверка релиза Demo

Проверяйте readiness публичной Demo, а не только liveness:

curl --fail https://pharmaviyum-erp.fastapicloud.dev/health
curl --fail https://pharmaviyum-erp.fastapicloud.dev/ready

Ожидаемый ready response должен показывать healthy для PostgreSQL, Redis и AI initialization. Workflow развёртывания Demo также проверяет SPA routes, runtime identity, обработку неверной авторизации и защиту POS.

Зелёный CI не доказывает корректность Demo provider quota, содержимого БД, полноты каталога или всех аптечных процессов. Перед объявлением релиза Demo успешным выполните live smoke checks. Health checks и release evidence Production относятся к отдельно управляемому Production environment.

## 10. Правила безопасности

- Не коммитьте .env-файлы, API keys, tokens, passwords или database connection strings.
- Используйте уникальные credentials для каждого окружения и Edge node.
- Храните Demo secrets в защищённом Demo environment и платформе хостинга Demo. Production secrets управляются за пределами этого публичного репозитория.
- Не используйте общие или default admin credentials.
- При подозрении на утечку ротируйте секрет.
- Ограничьте сетевой доступ к PostgreSQL и Redis доверенными сервисами.
- Не помещайте секреты, patient identifiers, рецепты или клинический текст в logs, traces, fixtures и документацию.
- Изолируйте сбои AI/provider от POS и core ERP transactions.
- Делайте backup перед изменениями схемы и регулярно проверяйте restore.
- Не обходите branch protection, CI, environment approvals и release gates.