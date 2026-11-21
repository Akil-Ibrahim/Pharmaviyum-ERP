# DevOps и Production Engineering — Pharmaviyum ERP/CRM

[English](./README.md) · **Русский**

## Назначение

Этот раздел описывает инженерный roadmap и операционную модель развития Pharmaviyum ERP/CRM. Плановый сценарий — 100 аптек, 200 посетителей в день на аптеку (20 000 всего), пять сотрудников на аптеку (500 всего) и три POS-терминала на аптеку (300 всего). Объём AI-запросов и пиковая конкурентность не определены и должны измеряться отдельно. Число посетителей нельзя трактовать как число AI-запросов или одновременных сессий.

Документация развивает существующую модель deployment, а не предлагает инфраструктуру ради самой инфраструктуры.

## Текущая модель поставки

Текущая цепочка:

1. Pull request в main.
2. GitHub Actions: CI, тесты, security и RAG evaluation.
3. Merge после прохождения обязательных checks.
4. Ручной запуск Demo-only deployment workflow для FastAPI Cloud.
5. Проверка статуса deployment, логов и smoke tests.

FastAPI Cloud размещает только публичную Demo. Demo БД, cache и worker services должны быть подготовлены и эксплуатироваться согласно Demo deployment runbook. Production использует тот же технологический стек приложения на аптечном сервере; Ansible отвечает за конфигурацию инфраструктуры и выпуск приложения. Реальные Production inventory, per-site credentials и approvals остаются вне Git. Ansible rollout нельзя считать подтверждённым для Production до получения lab/pilot и site acceptance evidence.

В репозитории также есть opt-in Compose stack мониторинга для контролируемых развёртываний. Nginx/edge, OpenTelemetry Collector, managed data services и multi-node orchestration — целевые возможности, а не утверждение, что они входят в текущую базовую конфигурацию.

GitHub Actions — CI quality gate. Отдельный FastAPI Cloud workflow — текущий путь deployment публичной Demo и не должен обращаться к Production. Docker image build jobs могут поддерживать container workflows, но не являются целевой платформой hosted deployment.

## Принципы production

1. **Сначала измерять, затем масштабировать.** Capacity решения основаны на нагрузочных тестах и production metrics.
2. **Сервисы должны заменяться.** По возможности контейнеры stateless; persistent state хранится в managed или явно резервируемых системах.
3. **Автоматизировать восстановление.** Backup, rollback и restore должны быть исполнимыми и протестированными.
4. **Наблюдать весь путь запроса.** API, БД, Redis, workers и AI/RAG требуют коррелированной telemetry.
5. **Безопасная деградация.** Timeouts, ограниченные retries, circuit breakers, rate limits и graceful degradation предотвращают каскадные сбои.
6. **Защищать цепочку поставки.** Immutable images, SBOM, provenance, dependency scanning и least privilege — требования к релизу.
7. **Не усложнять платформу без причины.** Kubernetes — возможный поздний этап, а не обязательное условие production readiness.

## Этапы roadmap

### Этап 1 — Capacity и нагрузочное тестирование

Используйте tests/load/k6/stage1_baseline.js как воспроизводимую точку входа. Начинайте с актуального /health и аутентифицированной нагрузки /api/v1/ai/query; не тестируйте устаревшие endpoints. Постепенно добавляйте подтверждённые CRM reads/writes, поиск и RAG с синтетическими tenant-данными.

Измеряйте RPS, concurrency, p50/p95/p99, ошибки и насыщение; соединения PostgreSQL, query latency и pgvector; Redis latency и глубину Celery queue; AI concurrency, model latency и timeouts. Фиксируйте baseline и повторяйте тесты после существенных изменений инфраструктуры.

Текущие k6 thresholds — начальные инженерные gates, не финальные SLO. Перекалибруйте их после репрезентативных измерений.

**Критерий выхода:** воспроизводимый набор нагрузочных тестов и документированная capacity baseline. Бизнес-допущения и контракт доказательств benchmark описаны в [Engineering Benchmark Requirements](./ENGINEERING_BENCHMARK_REQUIREMENTS.ru.md). Ступени конкурентности — стресс-профили, не прогноз трафика.

### Этап 2 — Observability

Целевая схема: FastAPI/Celery/AI → OpenTelemetry SDK → OpenTelemetry Collector → metrics/traces/logs → Prometheus/Tempo/Loki → Grafana.

Минимально отслеживайте API request/error rate, p50/p95/p99, задержки запросов и пула БД, Redis health/latency, Celery queue depth и duration, RAG retrieval/generation latency, LLM latency/errors/concurrency и насыщение CPU/памяти/диска/сети.

SLI/SLO определяются после измерений этапа 1, а не назначаются произвольно. Проверяйте trace coverage, context propagation, сбои exporter/collector, потерю telemetry, доставку alerts и корреляцию логов с traces. Наличие instrumentation само по себе не доказывает end-to-end observability.

**Критерий выхода:** dashboards, alert rules, correlated traces и документированные SLO.

### Benchmark и quality gates

Канонический контракт метрик для API, PostgreSQL/pgvector, Redis, RAG, аптечного AI, agents/MCP, security, OpenTelemetry, frontend E2E и scalability находится в [Engineering Benchmark Requirements](./ENGINEERING_BENCHMARK_REQUIREMENTS.ru.md).

Сохраняйте независимые gates для backend performance, data services, retrieval, качества ответов/citations, клинической безопасности, agent/tool correctness, tenant isolation, observability, frontend workflows и recovery. Не объединяйте их в единый средний балл. Подтверждённая утечка между tenant, несанкционированный protected tool execution, раскрытие чувствительной telemetry или критическая клиническая ошибка блокируют релиз.

Ragas применяется только для метрик, поддерживаемых закреплённой версией. Retrieval ranking и специализированные клинические метрики требуют project evaluators и/или экспертной разметки; не называйте их встроенными метриками Ragas без проверки API.

Каждый benchmark фиксирует commit, environment, workload, dataset, sample size, команду и артефакт. Различайте MEASURED, HISTORICAL, ESTIMATED, NOT TESTED и UNAVAILABLE. Результаты Codespaces не доказывают production capacity.

### Этап 3 — Надёжность приложения

Настройте явные connect/read/write/request timeouts; ограниченные retries с exponential backoff и jitter; circuit breakers; graceful shutdown и startup/readiness; лимиты пулов БД и Redis; API rate limiting и request-size limits; idempotency для повторяемых write operations; Celery task limits/retry policies; backpressure для дорогих AI-операций.

Не используйте бесконечные retries и не повторяйте бездумно неидемпотентные операции.

**Критерий выхода:** сбои зависимостей и всплески трафика приводят к предсказуемой деградации, а не к каскадному отказу.

### Этап 4 — Надёжность PostgreSQL и Redis

PostgreSQL одновременно является транзакционной БД и хранилищем pgvector, поэтому критичен для capacity и availability.

PostgreSQL: connection pooling/PgBouncer при подтверждённой нагрузке на соединения; автоматические backups; point-in-time recovery; проверка restore; replication/managed PostgreSQL при необходимости; pg_stat_statements и slow-query monitoring; review индексов/autovacuum; мониторинг pgvector indexes и query plans.

Redis: определите, какие данные являются cache, queue state или durable application state; настройте persistence и HA по требованиям; контролируйте память/eviction, здоровье Celery broker и queue depth; используйте managed Redis, когда требования превышают возможности single-node deployment.

**Критерий выхода:** протестированный backup/restore и документированные режимы отказа PostgreSQL и Redis.

### Этап 5 — Надёжность AI/LLM

AI — отдельный capacity domain; он не должен насыщать основной CRM API. Целевые controls: Agent Harness/AI Gateway, model routing, concurrency limits, per-tenant quotas, timeouts, bounded retries, circuit breaker, response/cache policy и fallback/degraded mode.

Мониторьте AI request rate, queue depth, model/retrieval latency, generation failures, token usage/cost, per-tenant concurrency и регрессии RAG quality/safety.

**Критерий выхода:** насыщение AI не выводит из строя обычный CRM-трафик, а degraded behaviour наблюдаем.

### Этап 6 — Безопасность и software supply chain

Расширяйте CI security baseline: container scanning (Trivy или аналог), dependency scanning, генерация/хранение SBOM, image provenance и signing/verification, production secret store, least-privilege runtime, network segmentation, WAF/edge rate limiting при необходимости, контролируемые dependency updates и регулярное обновление base images.

Не помещайте credentials в repository files, Docker images или build logs.

**Критерий выхода:** для каждого production image есть проверяемое происхождение, SBOM и воспроизводимый security verification.

### Этап 7 — CI/CD и release engineering

Сохраняйте GitHub Actions в роли CI gate, а FastAPI Cloud — в роли hosting/deployment Demo. Хостинг и развёртывание Production управляются за пределами публичного репозитория. Ansible остаётся отдельной возможностью on-premises deployment.

Требуются immutable image с commit SHA/digest, CI gates до публикации image, проверка миграций БД, deployment health checks, процедура rollback, release metadata/audit trail, разделение окружений, контролируемое production approval и smoke tests. Не обходите обязательные checks через continue-on-error.

Canary/blue-green оценивайте только при обосновании трафиком и топологией.

**Критерий выхода:** неудачный релиз быстро обнаруживается и откатывается по документированной процедуре.

### Этап 8 — Disaster Recovery и production validation

Production readiness не завершена, пока восстановление не проверено. Определите RPO/RTO с бизнесом; документируйте восстановление БД и Redis; проверьте restore из реального backup; опишите redeployment приложения из immutable image; тестируйте сбои зависимостей, worker failure и queue recovery; повторяйте load tests после изменений; проводите контролируемые failure/chaos tests; пересматривайте SLO и incident response.

**Критерий выхода:** команда демонстрирует восстановление на практике, а не только описывает его.

## Политика Kubernetes

Kubernetes намеренно не входит в обязательные первые восемь этапов. Вводите его только при подтверждённой потребности в возможностях, которые Docker Compose + Ansible не обеспечивают эффективно: multi-node scheduling, частые независимые deployment, автоматическое горизонтальное масштабирование или существенно больший парк сервисов.

Цель — надёжность production, а не количество технологий.

## Production checklist

### Надёжность
- [ ] Установлена load baseline.
- [ ] SLO определены по измеренной нагрузке.
- [ ] Настроены timeouts и ограниченные retries.
- [ ] Включён rate limiting.
- [ ] Проверен graceful shutdown.
- [ ] Проверен database pooling.
- [ ] Настроены Celery backpressure и task limits.

### Observability
- [ ] OpenTelemetry instrumentation включена там, где требуется.
- [ ] Развёрнут Collector.
- [ ] Доступны metrics dashboards и distributed tracing.
- [ ] Доступны централизованные логи.
- [ ] Проверены alert rules.

### Данные
- [ ] Автоматические PostgreSQL backups.
- [ ] PITR доступен, если требуется.
- [ ] Выполнен restore test.
- [ ] Мониторится pgvector.
- [ ] Документировано восстановление Redis.

### Безопасность
- [ ] Включён container и dependency scanning.
- [ ] SBOM сохраняется.
- [ ] Image provenance проверяется.
- [ ] Production secrets хранятся вне Git.
- [ ] Проверен runtime least privilege.
- [ ] Проверены Edge/WAF controls.

### Поставка и восстановление
- [ ] Immutable image releases.
- [ ] CI gates enforced.
- [ ] Проверен процесс миграций.
- [ ] После deployment запускаются smoke tests.
- [ ] Проверен rollback.
- [ ] Документированы RPO/RTO.
- [ ] Продемонстрированы DB restore и redeployment приложения.
- [ ] Проверены сбои зависимостей.
- [ ] Поддерживается incident runbook.

## Связанные документы

- [Инженерные benchmarks и требования к качеству](./ENGINEERING_BENCHMARK_REQUIREMENTS.ru.md) — канонический контракт метрик.
- [Инженерная дорожная карта](./ENGINEERING_ROADMAP.ru.md) · [English](./ENGINEERING_ROADMAP.md) — этапы, владельцы, доказательства и критерии выхода; русский перевод ещё не опубликован.
- [Stage 1 Load Testing](./STAGE_1_LOAD_TESTING.md) — процедура нагрузочного тестирования; пока только английская версия.
- [Руководство Ansible для Pharmacy Edge](./ANSIBLE_PHARMACY_EDGE_GUIDE.ru.md) · [Ansible Pharmacy Edge Guide](./ANSIBLE_PHARMACY_EDGE_GUIDE.md) — подготовка хостов, безопасность и deployment.
- [План внедрения Pharmacy Edge](./PHARMACY_EDGE_ANSIBLE_ROLLOUT.ru.md) · [English](./PHARMACY_EDGE_ANSIBLE_ROLLOUT.md) — границы rollout, fleet capacity, release, backup/recovery и критерии приёмки.
- [FastAPI Cloud runbook](../deployment/FASTAPI_CLOUD.ru.md) — размещение и deployment публичной Demo.
- [Руководство по тестированию](../guides/TESTING.ru.md) — тесты и CI.


## Трассировка инженерных требований

Используйте [матрицу трассировки инженерных требований](./ENGINEERING_REQUIREMENTS_TRACEABILITY.ru.md) как междоменный индекс, связывающий benchmark requirements с ADR, реализацией, тестами, доказательствами CI и runtime-проверками. Матрица фиксирует открытые release blockers и не заявляет Production readiness. См. [английскую версию](./ENGINEERING_REQUIREMENTS_TRACEABILITY.md).
