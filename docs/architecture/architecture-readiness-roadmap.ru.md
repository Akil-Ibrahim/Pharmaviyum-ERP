# Дорожная карта архитектурной готовности

**Дата проверки:** 2026-11-19  
**Область:** архитектурная и эксплуатационная готовность Pharmaviyum ERP/CRM  
**Решение:** сохранить Modular Monolith; закрыть пробелы в доказательствах до добавления распределённой сложности.

Документ превращает Architecture Vision, реестр ADR, Offline Capability Matrix и аудит Mortarium RAG в проверяемые инженерные этапы. Он не является сертификацией production safety или соответствия нормативным требованиям.

## 1. Целевые архитектурные принципы

1. **Сначала Modular Monolith.** Оставить одно развёртываемое FastAPI-приложение, но обеспечить явные границы доменов. Выделять сервис только при наличии измеримых доказательств необходимости независимого масштабирования, владения, безопасности или релизного цикла.
2. **Tenant isolation — системный инвариант.** Идентичность tenant определяется серверной авторизацией, а не только недоверенным полем запроса. Каждый запрос, cache, memory namespace, checkpoint, event и background job должен сохранять tenant scope.
3. **Контекст пациента — отдельная граница безопасности.** Состояние пациента нельзя повторно использовать для другого пациента, включая явную область без пациента.
4. **PostgreSQL — долговременный источник истины.** Redis ускоряет работу и хранит краткосрочное состояние, но не должен быть единственной записью бизнес-транзакции.
5. **Events — это контракты.** Для Central/Edge synchronization нужны transactional outbox/inbox, версии схем, idempotency keys, правила порядка и replay controls.
6. **AI — подсистема, производящая доказательства.** Provenance retrieval, проверка citations, clinical safety evaluation, изоляция контекста и human escalation входят в контракт продукта.
7. **Эксплуатационная готовность — часть архитектуры.** Возможность не считается завершённой без telemetry, alerting, recovery, migration и rollback процедур.

## 2. Этапы готовности

| Этап | Приоритет | Требуемые доказательства | Критерий завершения |
|---|---|---|---|
| Изоляция пациентов и tenant | P0 | API, Redis и PostgreSQL checkpoint integration tests; cross-tenant rejection; sync/stream parity | Все synthetic сценарии проходят CI; согласован staged verification plan |
| Целостность запасов | P1 | Append-only movement ledger; атомарные sale/return/transfer; idempotency и reconciliation tests | Каждое изменение запаса отражено в durable movement; reconciliation обнаруживает расхождения |
| Pharmacy RBAC и pricing | P1 | Tenant-scoped role matrix, валютная политика, миграция и authorization tests | Нет cross-pharmacy read/write путей; роли и правила цен явные и аудируемые |
| Central/Edge synchronization | P1 | Версионируемые event contracts, transactional outbox/inbox, ordering, retries, deduplication, conflict policy | Replay и повторная доставка безопасны; offline/online переходы проверены integration tests |
| Качество и безопасность RAG | P1 | Версионируемый RU/EN golden set; Ragas и domain metrics; citation и negation tests | Пороги качества явные, воспроизводимые и блокируют safety regressions в CI |
| Production operations | P1 | OTel traces/metrics/logs, PHI redaction, SLOs, alerts, backup restore и rollback drills | Критические пользовательские сценарии имеют измеримые SLO и проверенные recovery procedures |
| Архитектурное управление | P2 | Владельцы ADR, dependency rules, threat model, data classification, change review | У каждого существенного решения есть владелец, альтернативы, последствия и доказательства проверки |

## 3. Последовательность работ

### Этап 0 — Доказать изоляцию пациента и tenant

Patient-scoped HMAC namespaces для API sessions, Agent checkpoints и RAG checkpoints присутствуют в `main` через PR #287. Unit tests проверяют различие namespace. Это необходимо, но недостаточно.

Требуемая integration-последовательность на синтетических записях и disposable services:

- Повторно использовать одну client session для запросов Patient A, Patient B и без пациента.
- Проверить синхронный и streaming API.
- Проверить, что API отклоняет пациента, не принадлежащего аутентифицированной аптеке.
- Сохранять и читать Redis short-term memory, summary и episodic state без cross-scope чтения.
- Сохранять LangGraph checkpoints в PostgreSQL и проверять независимость thread state.
- Проверить fail-closed поведение при отсутствии production/staging `SECRET_KEY`.
- Документировать последствия secret rotation и legacy checkpoint retention до смены ключей или удаления старого состояния.

**Release rule:** нельзя считать patient-isolation проверенной в production, пока нет доказательств CI и контролируемого staged запуска. Для этих тестов нельзя использовать реальные данные пациентов.

### Этап 1 — Сделать целостность запасов структурным свойством

Завершить и довести до эксплуатационной готовности ADR-0006. Append-only movement model, общий transactional service и несколько мигрированных POS/admin write paths уже существуют; остаётся валидация и закрытие остаточных lifecycle paths:

- Append-only movement records для поступлений, продаж, возвратов, корректировок и перемещений.
- Атомарная транзакционная граница между бизнес-командой, stock projection и outbox event.
- Idempotency key, связанный с tenant, типом команды и aggregate.
- Явные правила распределения по lot/batch и срокам годности.
- Reconciliation job, сравнивающий stock projection с историей movements.
- Запрет прямого изменения stock quantity вне inventory domain service.

**Release rule:** мигрировать каждый write path постепенно; для каждого этапа иметь reconciliation report и rollback path.

### Этап 2 — Обеспечить tenant-scoped authorization и pricing

Реализовать ADR-0005 как исполняемую модель авторизации:

- Определить матрицу role × resource × action, включая cashier, pharmacist, manager и tenant administrator.
- Получать pharmacy scope из authenticated membership и проверять его в application services и database queries.
- Определить currency, tax, rounding, price-list и effective-date policies.
- Добавить negative tests для cross-tenant reads, writes, exports, background jobs и AI tools.
- Фиксировать привилегированные изменения в append-only audit trail.

**Release rule:** tenant-scoped функция не считается завершённой только потому, что UI скрывает элемент или проверяет route.

### Этап 3 — Сделать Central/Edge synchronization детерминированной

Завершить ADR-0002 и ADR-0007 с явным протоколом:

- Transactional outbox на Edge и durable inbox на Central.
- Immutable event ID, tenant ID, aggregate ID/version, schema version и occurred-at timestamp.
- Idempotent consumer и обнаружение конфликтов при повторной доставке изменённого payload.
- Ordering per aggregate и gap detection.
- Retry/backoff, poison-message quarantine и operator replay.
- Явная conflict policy для каждой offline-capable команды.
- Version compatibility и staged rollout для Edge nodes.

**Release rule:** offline cash sale, local stock lookup и local transaction persistence должны переживать restart и replay без двойной проводки. Регулируемые и online-only операции остаются заблокированными offline, как указано в capability matrix.

### Этап 4 — Сделать RAG измеримым clinical evidence pipeline

- Поддерживать версионируемый golden dataset на русском и английском с provenance и reviewer approval.
- Измерять retrieval recall@k, MRR/nDCG, context precision/recall, faithfulness и answer relevancy.
- Сохранять domain-specific проверки citation correctness, точности названия/дозировки/формы препарата, negation preservation, clinical hallucination и patient-context isolation.
- Проверять prompt injection в user queries, retrieved documents, memory summaries и tool outputs.
- Настроить reranker, RRF и contextual-compression параметры в runtime либо удалить их из конфигурации; нельзя оставлять настройки, которые выглядят активными, но игнорируются.
- Сохранять точные source IDs на всех этапах retrieval, generation, reviewer revision и API response.
- Оставить Ragas и дорогие evaluators вне production request path; запускать детерминированные safety regression checks в CI.

**Release rule:** нельзя выпускать изменение модели или retrieval только на основании отдельных примеров. Публиковать dataset version, metric deltas и известные классы ошибок.

### Этап 5 — Обеспечить эксплуатационную готовность платформы

- Передавать trace context через FastAPI, SQLAlchemy, Redis, Celery, MCP и LLM calls.
- Редактировать patient identifiers, prompts, retrieved text, tokens и credentials в logs и span attributes.
- Определить SLO для login, POS checkout, inventory mutation, AI response и Edge synchronization.
- Настроить alerting на error budget burn, queue age, outbox/inbox lag, database pool saturation, Redis availability и AI provider failures.
- Проверять восстановление database backup, migration forward/rollback strategy, Redis loss и provider outage.
- Использовать readiness probes, проверяющие зависимости и инициализацию, а не только liveness процесса.
- Оставить production migrations additive и требующими явного approval; не выполнять bootstrap/reset непустой production database.

## 4. Definition of Done для архитектуры

Существенная возможность получает статус **Implemented**, только когда выполнены применимые пункты:

- [ ] Есть Accepted ADR или документированная причина, почему ADR не нужен.
- [ ] Ясны domain ownership и допустимое направление зависимостей.
- [ ] Authentication, tenant scope и patient/data classification проверяются на сервере.
- [ ] Database constraints и transaction boundaries защищают инварианты.
- [ ] Unit, integration и failure-path tests покрывают контракт.
- [ ] CI запускает релевантные тесты и security checks.
- [ ] Metrics, traces и privacy-safe logs позволяют диагностировать сбои.
- [ ] Документированы migration, rollback, retention и recovery.
- [ ] Runbook определяет действия оператора и критерии escalation.
- [ ] Production activation имеет отдельные доказательства, не равные code merge.

Статусы ADR должны оставаться строгими: **Proposed** — не принято; **Accepted** — направление одобрено; **Implemented** — есть код, тесты и operational evidence; **Superseded** — историческое решение сохранено, но заменено.

## 5. Явные non-goals

- Не разделять Modular Monolith на микросервисы без измеримой необходимости.
- Не использовать Redis как system of record для продаж, запасов или клинических записей.
- Не включать offline banking authorization, fiscalization, e-prescriptions или регулируемые процессы без jurisdiction-specific approval и проверенной интеграции.
- Не заявлять HIPAA/GDPR или иное regulatory compliance только на основании архитектурной документации.
- Не ротировать HMAC secrets и не удалять legacy checkpoints без retention, migration и rollback плана.

## 6. Границы имеющихся доказательств

На дату проверки:

- Patient-aware API, Agent и RAG namespace derivation присутствует в `main` через PR #287.
- Существуют unit-level namespace tests.
- В репозитории есть integration fixtures для PostgreSQL и Redis.
- Новая synthetic API/Redis/PostgreSQL isolation integration suite предложена отдельным PR; её CI результат и staged выполнение необходимо проверить до признания этапа завершённым.
- ADR-0005, ADR-0006, ADR-0002 и ADR-0007 остаются архитектурной работой, а не завершёнными production-возможностями.
- Production readiness, clinical safety и regulatory compliance не выводятся из успешного code merge.

**Периодичность проверки:** пересматривать roadmap после каждого этапа, обновлять evidence links и owners и не повышать maturity labels без доказательств тестирования и эксплуатации.
