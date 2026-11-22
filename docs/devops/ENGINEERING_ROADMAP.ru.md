# Инженерная дорожная карта и этапы поставки

**Принцип:** продвижение определяется доказательствами и критериями выхода, а не календарными названиями этапов или амбициями по инфраструктуре.

## Текущая базовая модель поставки

Репозиторий представляет собой модульный FastAPI monolith с frontend на React/TypeScript, состоянием на PostgreSQL, Redis-совместимым cache/memory, инфраструктурой Celery tasks и Mortarium LangGraph AI/RAG. FastAPI Cloud размещает и развёртывает только публичную Demo через вручную запускаемый workflow. Production использует тот же технологический стек приложения и развёртывается на аптечном сервере через проверенные Ansible playbooks; реальные host inventory, per-site credentials и approvals остаются под контролем оператора.

Текущая цель Production deployment — аптечный сервер в рамках профиля Pharmacy Edge. Central + Edge fleet synchronization — поэтапная целевая архитектура; это не утверждение, что Central service или сеть из 100 аптек уже развёрнуты. Значение 100 аптек — проектная цель, а не доказательство текущей production capacity. См. [ADR-0002](../adr/ADR-0002-offline-first-central-edge.ru.md).

## Этап 0 — Инженерная основа

**Цель:** воспроизводимая разработка и безопасная поставка.

Работы: поддерживать pyproject.toml + uv.lock, frontend lockfile, lint/format/type/test/security CI, документированную совместимость runtime и проверяемые PR gates.

**Критерии выхода:** чистая настройка по документации, воспроизводимые lockfiles, обязательные checks проходят на точном PR SHA, обычная PR-проверка не запускает неявный production deployment.

## Этап 1 — Корректность аптечных процессов

**Цель:** доказать корректность критических бизнес-транзакций до масштабирования.

Работы: описать роли, авторизацию, переходы состояний и audit effects; проверить приёмку товара, партии/сроки годности, складские движения, FEFO, POS, оплату, возвраты и перемещения; тестировать idempotency, concurrency, cancellation и reconciliation.

**Критерии выхода:** синтетические end-to-end сценарии, инварианты ledger/inventory после успеха и отказа, tenant/role tests; никаких заявлений о завершённости только на основании list/read endpoints.

## Этап 2 — Базовый уровень capacity и производительности

**Цель:** измерить репрезентативную нагрузку.

Работы: выполнить [Stage 1 load testing](./STAGE_1_LOAD_TESTING.md); отдельно моделировать browsing, search, authenticated reads/writes и AI; фиксировать RPS, concurrency, p50/p95/p99, ошибки, насыщение БД, Redis latency, backlog workers и задержки провайдера.

**Критерии выхода:** воспроизводимая нагрузка и baseline report, допущения отделены от измерений, bottlenecks документированы, thresholds пересмотрены.

## Этап 3 — Observability и операционная надёжность

**Цель:** диагностировать сбои API, data services, workers и AI.

Работы: проверить W3C trace propagation, bounded spans, dashboards и alerts; определить timeouts, ограниченные retries, backpressure и graceful shutdown; проверить readiness и incident response.

**Критерии выхода:** traces для согласованных workflow, проверена доставка alerts, runbooks связывают alerts с действиями восстановления, privacy review telemetry пройден.

## Этап 4 — Защита данных и восстановление

**Цель:** продемонстрировать возможность восстановления.

Работы: определить RPO/RTO, настроить PostgreSQL backup/PITR там, где поддерживается, определить retention Redis/checkpoints, проводить изолированные restore drills, проверить ротацию секретов и контроль доступа.

**Критерии выхода:** измеренное время восстановления и проверки целостности, назначены владельцы retention, процедуры восстановления протестированы, жизненный цикл данных пациентов проверен.

## Этап 5 — Качество и безопасность Mortarium AI

**Цель:** сделать качество AI измеримым и изолировать контекст пациента.

Работы: связывать аутентифицированный tenant/patient context через API, memory, cache и checkpoints; оценивать retrieval на английском и русском; измерять citation entailment, medication entity accuracy, negation и hallucination; запускать offline Ragas и детерминированные regression checks; тестировать prompt injection и небезопасные tools.

**Критерии выхода:** ноль утечек между пациентами в определённом наборе тестов, утверждённые датасет и reviewer process, пороги утверждены квалифицированными специалистами, доказательства версионированы, границы обязательной проверки человеком явно определены.

## Этап 6 — Пилот Pharmacy Edge

**Цель:** доказать локальную работу и синхронизацию в небольшом контролируемом масштабе.

Работы: проверить Ansible на лабораторном оборудовании; протестировать локальный POS при WAN outage; проверить durable outbox/inbox, duplicate delivery, ordering и poison events; проверить offline capability, backup/restore и staged upgrades.

**Критерии выхода:** приёмка лаборатории/пилота, отсутствие повторных бизнес-эффектов при replay, видимость sync backlog/stale state, проверенные restore и rollback, rollout limit не превышает утверждённый scope.

## Этап 7 — Контролируемое расширение на несколько площадок

**Цель:** расширяться только при наличии подтверждающих данных пилота.

Работы: canary и wave rollout, нагрузочные тесты Central ingestion/reporting, изоляция отказов площадок, тесты отказа Central, процедуры поддержки и установки обновлений.

**Критерии выхода:** capacity evidence для каждого расширения, нет нерешённых критических security/data-integrity findings, recovery objectives соблюдены, получено явное разрешение увеличить rollout limit.

## Gates поставки

Этап считается завершённым только если код/configuration проверены, автоматические checks прошли на целевом commit, операционные доказательства сохранены, security/privacy проверены, документация актуальна, а остаточные риски имеют ответственного.

## Связанные планы и доказательства

- [Индекс DevOps](./README.ru.md)
- [Инженерные benchmark requirements](./ENGINEERING_BENCHMARK_REQUIREMENTS.ru.md)
- [Stage 1 load testing — английский оригинал](./STAGE_1_LOAD_TESTING.md)
- [Stage 2 observability — английский оригинал](./STAGE_2_OBSERVABILITY.md)
- [Pharmacy Edge rollout — английский оригинал](./PHARMACY_EDGE_ANSIBLE_ROLLOUT.md)
- [Offline capability matrix](./PHARMACY_OFFLINE_CAPABILITY_MATRIX.ru.md)
- [Production operations runbook](../operations/PRODUCTION_OPERATIONS_RUNBOOK.ru.md)
