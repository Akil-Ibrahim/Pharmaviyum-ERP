# Развёртывание Pharmaviyum в FastAPI Cloud

Runbook описывает текущий workflow ручного deployment: `.github/workflows/deploy-fastapi-cloud.yml`. Это канонический источник сведений о hosted release. Не выводите поведение deployment из устаревших описаний workflow.

## 1. Политика релизов

Production deployment выполняется намеренно вручную. Push или merge в `main` не запускает автоматический deployment и не должен побочно выполнять миграции БД.

```text
Pull request
  -> обязательные CI, security, frontend, backend, integration и RAG checks
  -> merge в main
  -> ручной запуск Deploy to FastAPI Cloud из main
  -> approval production environment (если настроен)
  -> deploy и smoke checks
  -> проверка логов и live-приложения
```

Workflow использует выбранный commit из `main`, проверяет успешный CI именно для этого SHA и сериализует production deployments через concurrency group.

## 2. GitHub Actions secrets

Добавьте следующие значения как repository Actions secrets или secrets защищённого GitHub Actions environment `production`:

- `FASTAPI_CLOUD_TOKEN` — deploy token FastAPI Cloud.
- `FASTAPI_CLOUD_APP_ID` — ID целевого приложения FastAPI Cloud.
- `DATABASE_URL` — sync или async PostgreSQL URL той же production БД, что использует приложение. Workflow использует его для read-only catalog exclusion checks и очистки временного smoke-test пользователя. Cleanup нормализует `postgresql+asyncpg://` / `postgres+asyncpg://` в URL, совместимый с psycopg.
- `VITE_CLERK_PUBLISHABLE_KEY` — необязательный build-time public frontend key, если он нужен текущей конфигурации входа.

Не помещайте значения секретов в репозиторий, workflow inputs, issue comments или чат. Не выводите credentials в CI logs.

**Секреты с username/password для smoke test не нужны.** Workflow создаёт уникальную временную учётную запись pharmacist со случайным паролем на каждый запуск через существующий registration endpoint, проверяет login/profile/catalog и пытается удалить только эту non-superuser запись. Не задавайте статические `PHARMAVIYUM_SMOKE_USERNAME` / `PHARMAVIYUM_SMOKE_PASSWORD`. Не используйте `admin/admin`.

## 3. Переменные окружения FastAPI Cloud

В панели Environment Variables приложения настройте:

| Переменная | Требование |
|---|---|
| `ENVIRONMENT` | `production` |
| `DEBUG` | `false` |
| `LOG_LEVEL` | `INFO` |
| `DATABASE_URL` | Production PostgreSQL async URL, обычно `postgresql+asyncpg://...` |
| `PGVECTOR_DATABASE_URL` | Доступный PostgreSQL/pgvector URL |
| `REDIS_URL` | Доступный Redis-compatible URL |
| `SECRET_KEY` | Уникальный случайный секрет, минимум 32 символа |
| `CORS_ORIGINS` | Точный доверенный HTTPS origin; без wildcard при credentials |
| `USE_CLOUD_LLM` | `true` для demo AI profile |
| `CLOUD_LLM_PROVIDER` | `qwencloud` |
| `QWEN_API_KEY` | Секретный API key QwenCloud |
| `QWEN_BASE_URL` | `https://ap-southeast-1.maas.qwencloudapi.com/compatible-mode/v1` |
| `QWEN_MODEL` | `qwen3.8-flash` |
| `QWEN_FAST_MODEL` | `qwen3.8-flash` |
| `QWEN_COMPLEX_MODEL` | `qwen3.8-flash` |
| `QWEN_FREE_QUOTA_ONLY` | `true`, fail-closed guard приложения |
| `QWEN_TIMEOUT_SECONDS` | `30` |
| `QWEN_MAX_OUTPUT_TOKENS` | `500` |

Значения QwenCloud описывают текущий demo profile, а не безлимитный бесплатный production SLA. В консоли провайдера включите **Free quota only** для выбранной модели и проверьте остаток/срок действия квоты до включения запросов. Одного application flag недостаточно для enforcement биллинга. Генерация QwenCloud и embeddings — отдельные возможности: embedding provider нужно настроить и проверить независимо до включения cloud RAG.

Используйте одну и ту же production БД для FastAPI Cloud `DATABASE_URL` и GitHub Actions `DATABASE_URL`. Ограничьте сетевой доступ к PostgreSQL и Redis необходимыми источниками.

## 4. Ручная процедура deployment

1. Убедитесь, что изменение влито в `main`.
2. Проверьте обязательные checks для точного commit SHA из `main`.
3. Откройте [Deploy to FastAPI Cloud workflow](https://github.com/Akil-Ibrahim/Pharmaviyum-ERP/actions/workflows/deploy-fastapi-cloud.yml).
4. Нажмите **Run workflow**, выберите ветку `main` и укажите утверждённую ссылку на change/ticket в `change_reference`.
5. Запустите workflow и пройдите approval для environment `production`, если он требуется.
6. Следите за выполнением. Не объявляйте deployment успешным, пока deploy и все обязательные verification steps не завершились успешно.

Workflow выполняет следующие действия:

- checkout выбранного commit;
- установку Bun (с fallback на package manager) и сборку `frontend/shadcn-admin`;
- проверку успешного CI для точного commit SHA;
- проверку change reference и обязательных deployment secrets;
- запуск `uv run fastapi cloud deploy .`;
- read-only production catalog exclusion check;
- проверку `/health` и `/ready`;
- проверку, что `/version` сообщает `production` для API/core, application и authentication settings, debug выключен и runtime — CPython `3.15.2`;
- проверку, что `/settings/appearance` и `/system-status` возвращают SPA HTML;
- проверку HTTP 401 для неверных credentials и неавторизованного POS search;
- создание временной учётной записи pharmacist, проверку auth/profile и непустого поиска Omeprazole в catalog/product endpoints, затем попытку удалить именно эту учётную запись.

Smoke test с временной учётной записью — это production write, а не read-only проверка. Очистка выполняется при обычном завершении и перехватываемых сигналах `INT` / `TERM`, в том числе при неоднозначном результате регистрации. Принудительное завершение runner или потеря host могут помешать cleanup. Smoke checks не должны создавать продажи, приёмки товара или изменять остатки. Если cleanup завершился ошибкой, workflow сообщает о failure. Перед повтором проверьте run и удаляйте только конкретную временную запись, созданную этим запуском, по утверждённой процедуре.

## 5. Миграции БД выполняются отдельно

**Текущий deployment workflow не запускает Alembic migrations.** Не описывайте его как migration workflow.

Изменения схемы требуют отдельной явно утверждённой операции:

1. Проверьте migration script, совместимость и последствия rollback.
2. Убедитесь в наличии свежего backup и проверенного restore path.
3. Получите production approval на изменение схемы.
4. Один раз выполните `uv run alembic upgrade head` из доверенного окружения с безопасно переданным URL целевой production БД.
5. Проверьте версию схемы и readiness приложения до продолжения release.

Не запускайте миграции при старте приложения или параллельно из нескольких replicas. Доступ workflow к БД для catalog checks/smoke cleanup не является разрешением выполнять schema changes.

## 6. Проверка после deployment

Минимальные проверки:

```bash
curl --fail https://pharmaviyum-erp-crm.fastapicloud.dev/health
curl --fail https://pharmaviyum-erp-crm.fastapicloud.dev/ready
```

Ожидаемые поля readiness:

- `status`: `ready`
- `checks.database.status`: `healthy`
- `checks.redis.status`: `healthy`

Endpoint `/ready` проверяет только PostgreSQL и Redis. AI initialization — критическая зависимость startup в production lifespan, но отдельным полем `/ready` не возвращается. Workflow отдельно проверяет `/version` и результат startup приложения.

Также проверьте:

- `/version` сообщает production environment и ожидаемую версию Python;
- `/settings/appearance` и `/system-status` отдают собранный frontend (HTTP 200);
- login и `/api/v1/auth/me` работают для разрешённой непривилегированной тестовой учётной записи;
- POS endpoints отклоняют неавторизованные запросы;
- Omeprazole возвращает непустые результаты в drug-catalog и product search;
- исключённые записи каталога не активны;
- неожиданные продажи, движения товара и изменения остатков отсутствуют.

Зелёный GitHub Actions workflow необходим, но не доказывает готовность всех аптечных процессов, provider quota, OCR, background workers или Edge/offline.

## 7. Ограничения runtime и эксплуатационные заметки

- Native deployment FastAPI Cloud использует Python project configuration; workflow отдельно собирает React frontend.
- Приложение фиксирует `requires-python = "==3.15.2"` в `pyproject.toml` и `3.15.2` в корневом `.python-version`. CI, Docker и deployment workflow требуют точную версию CPython 3.15.2; deployment gate отклоняет любой другой runtime, указанный в `/version`. Последняя известная проверка hosted `/version` от 2026-11-15 показывала CPython 3.15.0, а предыдущая попытка strict build на 3.15.2 завершилась ошибкой: в managed interpreter catalog FastAPI Cloud не было этой версии. Поэтому нельзя считать production работающим на 3.15.2, пока новая deployment-попытка и live `/version` независимо это не подтвердят; если у провайдера всё ещё нет CPython 3.15.2, deployment заблокирован. Успешная CI compatibility job подтверждает установку зависимостей и critical imports в CI, но не доступность managed runtime у провайдера. Production считается обновлённым только после подтверждения CPython 3.15.2 через `/version` и успешных startup, `/health`, `/ready`, authentication и POS smoke checks. Major version Neon PostgreSQL этим обновлением приложения не меняется.
- Dockerfile устанавливает Tesseract и OCR language packs; native FastAPI Cloud автоматически эти системные пакеты не устанавливает. Для OCR требуется отдельно проверенный runtime или внешний OCR service.
- PostgreSQL/pgvector и Redis provisioned отдельно; deployment приложения их не создаёт.
- Celery worker/Beat не запускаются web deployment workflow. При необходимости развёртывайте и мониторьте worker отдельно.
- Cloud OpenTelemetry export требует доступного OTLP collector endpoint; локальный Compose Jaeger/collector автоматически в FastAPI Cloud не появляется.
- Сбои AI provider и исчерпание квоты не должны влиять на POS и core ERP transactions.
- Первая цель rollout — 1–10 аптек. Ёмкость до 100 аптек — архитектурная цель, а не подтверждённая production capacity до проведения испытаний.

## 8. Диагностика

| Симптом | Первые проверки |
|---|---|
| Workflow отклоняет deployment inputs | Проверьте наличие `FASTAPI_CLOUD_TOKEN`, `FASTAPI_CLOUD_APP_ID`, `DATABASE_URL` и change reference в правильном Actions/production scope |
| Проверка CI для exact commit не проходит | Убедитесь, что CI успешно завершился для того же SHA `main`, который выбран workflow |
| `/ready` не готов | Проверьте FastAPI Cloud logs, PostgreSQL, Redis и настройки/доступность AI provider |
| `/settings/appearance` возвращает JSON 404 | Проверьте frontend build/staging и упаковку static files в artifact |
| Smoke catalog search пустой | Это проблема готовности каталога/данных; проверьте импорт и индексацию отдельно. Не создавайте фиктивные записи и не отмечайте smoke test успешным |
| Не удалась очистка временного smoke account | Проверьте конкретные run ID/attempt и cleanup logs; удаляйте только сгенерированную запись после подтверждения, что она не superuser |
| AI calls не работают или квота исчерпана | Проверьте QwenCloud credentials, доступ к модели, Free quota only, срок квоты и embeddings; не переключайтесь молча на платный fallback |

## 9. Безопасность и контроль изменений

- Сохраняйте ручной deployment, защищённый GitHub Actions environment `production`.
- Не обходите CI, branch protection, approvals и concurrency controls.
- Не используйте `admin/admin` или статические smoke credentials.
- Не раскрывайте secrets или patient data в workflow logs, traces, screenshots и issue comments.
- Не меняйте production data, schema или реальные аптечные hosts в рамках обычного deployment без отдельного утверждённого изменения.
