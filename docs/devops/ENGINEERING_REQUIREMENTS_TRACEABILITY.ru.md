# Трассировка инженерных требований — Pharmaviyum

[English](./ENGINEERING_REQUIREMENTS_TRACEABILITY.md) · **Русский**

**Статус:** начальная матрица трассировки по документации репозитория  
**Базовый commit:** `1cf4c6afbc738df95986480d99340db0a76e9e8c` (`main`, 2026-11-21)  
**Основные требования:** [Engineering Benchmark Requirements](./ENGINEERING_BENCHMARK_REQUIREMENTS.ru.md)  
**Связанные доказательства процессов:** [Трассировка аптечных процессов](../workflows/PHARMACY_WORKFLOW_TRACEABILITY.ru.md)  
**Проверка runtime / Production:** этим документом не выполнялась.

## 1. Назначение и контракт доказательств

Документ связывает инженерные требования с архитектурными решениями, реализацией, автоматизированными тестами и доказательствами CI/эксплуатации. Это индекс трассировки и реестр пробелов, а не сертификация реализации или Production readiness.

Требование считается **закрытым** только при наличии актуальных подтверждений по всей применимой цепочке:

`Требование → Архитектурное решение / контроль → Реализация → Автотест → Артефакт CI → Проверка среды`

## 1.1 Единая модель доказательной работоспособности

Для каждого требования и сквозного процесса Pharmaviyum использует одну шкалу зрелости доказательств. В матрице указывается ровно **один наивысший уровень, подтверждённый на данный момент**. Уровень отражает силу доказательств, а не процент готовности, важность требования или разрешение на релиз.

| Уровень | Название | Минимальные критерии принятия |
|---|---|---|
| **L0** | Документировано | Описаны требование, ожидаемое поведение, владелец и объективный критерий выхода. Наличие реализации не подразумевается. |
| **L1** | Реализовано | Реализация найдена в исходном коде на указанном commit; конфигурация и ownership прослеживаются. Само наличие кода не доказывает его выполнение. |
| **L2** | Проверено unit-тестами | Соответствующие unit-тесты прошли на точном commit; зафиксированы команда, запуск, результат и артефакт. |
| **L3** | Проверено интеграционными тестами | Совместно проверены зависимости и границы persistence (например API + БД + Redis); положительные, отрицательные и failure-path проверки прошли на точном commit. |
| **L4** | Проверен сквозной процесс (E2E) | Репрезентативный пользовательский сценарий выполнен от точки входа до устойчивого бизнес-результата. Проверяются обязательные side effects, авторизация, аудит, идемпотентность и поведение при сбоях, а не только HTTP success. |
| **L5** | Проверено в эксплуатации | Процесс проверен в контролируемой staging/pre-production среде; представлены применимые доказательства observability, security, load, recovery, backup/restore и rollback. Контроли должны быть реально проверены, а не только описаны. |
| **L6** | Проверено в Production | Точный релиз проверен в идентифицированной production-среде по утверждённой безопасной процедуре; зафиксированы deployment identity, smoke/workflow результаты, telemetry и готовность rollback. Реальные данные пациентов нельзя использовать для тестирования. |

### Правила присвоения уровня

- Уровень назначается **отдельно для каждого требования и критического workflow**, а не всему приложению одной общей отметкой. У приложения нет единого уровня зрелости.
- Уровень workflow ограничен самым низким уровнем любого обязательного шага или контроля. Необязательные шаги не снижают уровень, если требование не делает их обязательными.
- Более высокий уровень наследует все доказательства предыдущих уровней; его нельзя присвоить по одному успешному тесту или скриншоту.
- Для L1 нужны доказательства по исходному коду. Для L2 — unit-тесты на точном commit. Для L3 — integration evidence. Для L4 — доказательство полного сценария и проверенных устойчивых результатов. Для L5/L6 — доказательства, привязанные к конкретной среде.
- CI — механизм доставки доказательств, а не отдельный уровень зрелости. Успешный pipeline сам по себе не означает L2, L3 или L4: должны быть указаны область тестирования и соответствующие артефакты.
- Тест на mocks не доказывает реальную интеграцию. Backend API test не доказывает работоспособность браузерного процесса. Успешный вызов инструмента не доказывает завершение аптечной задачи.
- Production verification не является разрешением на небезопасные клинические действия. Используйте синтетические test tenants и утверждённые неклинические транзакции; production-проверки должны быть read-only либо отдельно одобрены и контролироваться.
- Если доказательство устарело, относится к другому commit/окружению или не воспроизводится, оно не учитывается для текущего уровня. Фиксируется пробел, а уровень остаётся на последнем обоснованном значении.
- **NOT TESTED**, **NOT AVAILABLE** и **BLOCKED** — это пометки о пробелах/ограничениях, а не уровни зрелости. Они не заменяют единственное значение L0–L6.

Для каждого уровня сохраняется provenance доказательств: точный commit SHA, тест/check и команда, run ID, среда и release/deployment ID (если применимо), timestamp, неизменяемый артефакт/log/trace, reviewer/owner, ограничения и следующий критерий выхода. Нельзя повышать уровень на основании исторического запуска, другого SHA или другой среды.



## 2. Матрица трассировки по направлениям

| ID | Область требований | Архитектура / решение | Известные свидетельства реализации и тестов | Уровень доказательств | Пробел / критерий выхода |
|---|---|---|---|---|---|
| AR-01 | Architecture Vision, System Context, bounded contexts и ownership | [Архитектурное видение](../architecture/pharmaviyum-architecture.ru.md), [System Context](../architecture/system-context.ru.md), индекс ADR | Документы архитектуры и ADR-0001…0008 существуют. Эта матрица не проверяла независимо все runtime-зависимости и границы владения. | L0 — Документировано | Проверить C4 Container/Component views, матрицу ownership, dependency rules и автоматические архитектурные тесты. Связать каждый bounded context с модулем, схемой и владельцем миграций. |
| AR-02 | Архитектурные решения и их жизненный цикл | [Индекс ADR](../adr/README.ru.md) | ADR-0001…0008 имеют явные статусы Proposed/Accepted и частичной реализации. | L0 — Документировано | Для каждого существенного решения зафиксировать альтернативы, последствия, миграцию/rollback, влияние на безопасность, владельца и доказательства проверки. Accepted не означает Implemented. |
| IF-01 | Изоляция Production/Demo и границы данных | Baseline Production/Demo, подготовленный в PR #388 (пока не влит в эту ветку) | Baseline требует отдельных DB credentials/branches, Redis endpoints, secrets и только синтетических данных в Demo. Для Production ранее подтверждены метаданные Neon с PostgreSQL 18; provisioning Demo и фактическое разделение endpoints здесь не доказаны. | L0 — Документировано | Проверить реальные ID ресурсов, endpoints, credentials, network policy, secrets и synthetic-data controls, не раскрывая значения секретов. Добавить негативные тесты против повторного использования credentials/данных между средами. |
| IF-02 | Совместимость PostgreSQL, pgvector и Redis | [Engineering Benchmark](./ENGINEERING_BENCHMARK_REQUIREMENTS.ru.md), [Technology Stack](../technology-stack.ru.md) | Целевые версии описаны. Версия managed Redis и hosted pgvector требуют runtime-проверки. Legacy Compose явно запрещён для Production/Demo и сохраняет PostgreSQL 16 / Redis 7. | L0 — Документировано | Зафиксировать `SHOW server_version`, версию pgvector из `pg_extension`, Redis `INFO server` или эквивалент провайдера, версии клиентов, TLS/auth. Не менять major версии с persistent volume без отрепетированной миграции. |
| IF-03 | Backup, restore, миграции и disaster recovery | [Production Operations Runbook](../operations/PRODUCTION_OPERATIONS_RUNBOOK.ru.md), [Release Runbook](../operations/RELEASE_RUNBOOK.ru.md) | Процедуры описаны в операционной документации; актуального артефакта restore drill и измеренных RPO/RTO эта матрица не содержит. | L0 — Документировано | Провести backup/restore и migration rollback в изолированной среде. Зафиксировать целостность данных, длительность, RPO/RTO, обработку ошибок и артефакты. Для Production нужны утверждённые цели и успешная репетиция. |
| SE-01 | RBAC, tenant isolation и авторизация | [PHI Governance Audit](../architecture/PHI_ACCESS_GOVERNANCE_AUDIT.ru.md), [PHI Read Surface Inventory](../security/PHI_READ_SURFACE_INVENTORY.ru.md), [PHI Route-to-Test Map](../security/PHI_ROUTE_TO_TEST_TRACEABILITY.ru.md), ADR-0005 | Source audit описывает pharmacy-scope controls и regression tests, но также отмечает глобальные superuser paths и неполное API/database-backed негативное покрытие. | L1 — Реализовано (обнаружено в исходном коде) | Инвентаризировать все read/write paths, обеспечить tenant predicates на уровне запросов, определить privileged support policy и запустить двухтенантные API integration tests для allow/deny сценариев. |
| SE-02 | PHI access audit, минимизация данных и приватность telemetry | PHI governance audit и PHI read-surface inventory | Требования governance описаны. Реализация отдельного append-only PHI audit, purpose-bound privileged access и полной минимизации response fields указанными аудитами не подтверждена. | L0 — Документировано | Реализовать надёжные allowed/denied access events, append-only DB controls, purpose/reason/expiry, DTO allowlists и redaction tests для logs, traces, metrics, MCP и background jobs. |
| AI-01 | LangGraph RAG retrieval и качество ответов | [AI system design](../ai/AI_LLM_SYSTEM_DESIGN.ru.md), [RAG architecture audit](../rag_architecture_audit.ru.md), [Ragas evaluation](../ai/ragas-pharmaceutical-evaluation.ru.md), ADR-0004 | Benchmark задаёт Recall@K, Precision@K, MRR, nDCG, поддерживаемые Ragas answer/context metrics и собственные citation/clinical metrics. В требованиях указан существующий retrieval evaluator. | L1 — Реализовано (обнаружено в исходном коде) | Проверить закреплённую версию/API Ragas, versioned golden dataset, экспертные labels, воспроизводимый baseline, confidence intervals и CI regression thresholds. Оценки Ragas не являются клинической истиной. |
| AI-02 | Аптечная клиническая безопасность | Разделы 4–5 Engineering Benchmark; AI safety/red-team документы | Метрики включают точность лекарства/ингредиента/дозировки/формы/пути введения, negation, interactions, contraindications, unsupported claims и escalation. Наличие экспертной разметки и покрытия датасета одной документацией не доказано. | L0 — Документировано | Создать проверенный фармацевтами synthetic golden set; определить знаменатели и классификацию критических ошибок; проверить adversarial, EN/RU multilingual, negation и citation support. Клинические пороги утверждают квалифицированные эксперты. |
| AI-03 | Agent Harness, LangGraph, безопасность MCP и patient context | ADR-0003; [Mortarium operations](../ai/mortarium-pharmacy-operations.ru.md); [Patient session isolation](../ai/patient-session-isolation.ru.md) | Workflow audit указывает пять read-only MCP tools и влитый patient-scoped state code; staged проверка PostgreSQL checkpoints + Redis session-switch остаётся открытой. | L1 — Реализовано (обнаружено в исходном коде) | Проверить unauthorized tool calls, аргументы, переключение pharmacy/patient, повторное использование старых checkpoints, retries/loops, итоговое состояние бизнес-операции и staged persistence. Успешный tool call не равен успешной задаче. |
| QE-01 | Backend/API, БД и contract quality | [Testing Guide](../guides/TESTING.ru.md), benchmark requirements | Workflow audit ссылается на POS checkout, inventory ledger и orders tests. Эта матрица не запускала их независимо. | L1 — Реализовано (обнаружено в исходном коде) | Связать каждый критический route/domain transition с unit, integration, contract и migration tests. Зафиксировать актуальные CI artifacts и добавить недостающие failure/rollback/concurrency tests. |
| QE-02 | Frontend и сквозные аптечные процессы | [Трассировка аптечных процессов](../workflows/PHARMACY_WORKFLOW_TRACEABILITY.ru.md) | Workflow audit указывает, что ряд операционных routes возвращают `null`: POS, patients, prescriptions, inventory, batches, suppliers, orders, transfers и procurement. POS backend tests не доказывают наличие рабочего checkout UI. | L1 — Реализовано (обнаружено в исходном коде) | Восстановить P0 POS и интерфейсы фармацевта, связать пациента/рецепт только после security controls и покрыть полные browser journeys через Playwright, включая stock/payment state. |
| QE-03 | Производительность, нагрузка и capacity | [Engineering Benchmark](./ENGINEERING_BENCHMARK_REQUIREMENTS.ru.md); [модель capacity](../performance/CAPACITY_WORKLOAD_MODEL.ru.md); [DevOps roadmap](./README.ru.md) | Канонический масштаб: 100 аптек, 5 сотрудников на аптеку (500 всего), 3 POS-кассы на аптеку (300 всего), 200 посещений на аптеку в день (20 000 всего в день). k6 entry point и стресс-профили описаны; репрезентативный staging capacity result не установлен. | L0 — Документировано | Утвердить arrival/peak distribution, распределение ролей, пересечение смен, конверсию посещения в продажу, состав корзины/workflow, загрузку касс, AI-спрос и лимиты инфраструктуры. Затем выполнить staged-тесты 1→10→25→50→100 tenants, по 3 параллельных cashier journeys на аптеку и отдельно обозначенный upper-bound профиль на 300 касс. Сохранить отчёты точного SHA и saturation evidence; не выводить RPS/VUs из суточного числа посещений. |
| OP-01 | OpenTelemetry, SLI/SLO, alerts и incident response | [OpenTelemetry Guide](../observability/opentelemetry.ru.md), [Operations Runbook](../operations/PRODUCTION_OPERATIONS_RUNBOOK.ru.md) | Instrumentation и целевой стек описаны; end-to-end trace coverage, доставка alerts и MTTD/MTTR drills этой матрицей не доказаны. | L0 — Документировано | Проследить FastAPI→DB/Redis→Celery→LangGraph/RAG/MCP/model; проверить propagation, redaction, collector delivery, alerts и incident exercises. SLO определять по репрезентативным baseline. |
| OP-02 | Deployment, rollback и release control | [FastAPI Cloud Runbook](../deployment/FASTAPI_CLOUD.ru.md), [Release Runbook](../operations/RELEASE_RUNBOOK.ru.md) | CI workflows и ручной hosted deployment описаны. Green CI на docs branch не является доказательством production deployment. | L0 — Документировано | Проверить protected branch rules, required checks, artifact provenance, deployment approval, post-deploy smoke tests и rollback rehearsal на текущем release path. |
| BV-01 | Бизнес-KPI и ограничения NDA | [Business Value and KPI](../workflows/PHARMACY_BUSINESS_VALUE_AND_KPIS.ru.md) | KPI framework разделяет результаты Pharmacist, Pharmacy и Company; benchmark требует измеримых доказательств. | L0 — Документировано | Привязать каждый KPI к event definition, источнику, знаменателю, когорте и окну измерения. Не публиковать финансовые метрики под NDA и не заявлять эффект без воспроизводимых измерений. |


## 2.1 Прицельная проверка PHI исходников — 2026-11-21

Проведена read-only проверка текущего исходного кода `main` в дополнение к аудитам PHI governance и read surfaces (указанный в аудите baseline: `c6d35b828c1958f1bcb9077bbd0b6a71ef94613b`). Это доказательства уровня исходного кода; база данных, Production runtime и данные пациентов не использовались.

Подтверждённая реализация и ограничения доказательств:

- Маршруты списка, поиска по телефону и чтения `GET /api/v1/patients/{patient_id}` разрешают pharmacy scope для обычных пользователей. `resolve_pharmacy_scope` позволяет superuser не указывать `pharmacy_id`, что намеренно даёт глобальную область доступа. Unit-тест `tests/unit/modules/auth/test_tenant.py::test_superuser_can_use_global_scope` явно закрепляет это поведение.
- Маршруты создания/изменения/удаления пациента доступны только superuser. В create-маршруте `pharmacy_id` необязателен; если superuser его не передаёт, сервис может создать пациента с nullable `Patient.pharmacy_id`. Это путь создания записи без владельца, обнаруженный в коде, а не доказательство наличия таких записей в Production.
- `PatientResponse` включает состояния и заметки о лечении, аллергии, номер страхового полиса, консультации и историю покупок. Маршруты чтения по ID и телефону возвращают этот широкий DTO. Минимизация полей по назначению для этих путей не доказана.
- `GET /patient-purchases/` требует superuser и явный `pharmacy_id`, соединяет `Patient` и фильтрует по `Patient.pharmacy_id`. Текущие regression tests компилируют SQL с mock-объектами; они не доказывают двухтенантную изоляцию на сохранённых в БД записях.
- `AuditLog` — общая модель, ориентированная на аудит изменений. Проверенные patient read handlers не создают отдельное событие разрешённого/запрещённого доступа к PHI. Append-only enforcement на уровне БД этой проверкой исходников не подтверждён.

Связанные исходники и тесты: `src/pharmaviyum/api/v1/endpoints/patients.py`, `src/pharmaviyum/modules/auth/tenant.py`, `src/pharmaviyum/services/patient.py`, `src/pharmaviyum/models/patients/patient.py`, `src/pharmaviyum/schemas/patient.py`, `src/pharmaviyum/models/audit_log.py`, `src/pharmaviyum/api/v1/patient_purchases.py`, `tests/unit/modules/auth/test_tenant.py`, `tests/unit/test_patient_purchases_scope.py`.

**Уровни доказательств:** SE-01 остаётся **L1** (в коде есть tenant-aware controls, но глобальный привилегированный scope и двухтенантное негативное доказательство на уровне БД остаются открытыми). SE-02 остаётся **L0** для требования отдельного PHI access audit и минимизации: общая audit-модель существует, но необходимый PHI access contract и его enforcement не подтверждены. Не повышать уровни только на основании этой проверки исходников.

Следующие критерии выхода: требовать явный управляемый pharmacy context при создании пациента; внедрить DTO с полями по назначению; определить ограниченную по времени и обязательную к указанию причины privileged-support policy; реализовать надёжный аудит разрешённых/запрещённых обращений к PHI с append-only enforcement; выполнить двухтенантные integration tests на синтетических данных, включая отказ для записей без владельца и поведение при сбое аудита.

## 3. Приоритетные release blockers

Это не косметические правки документации: для соответствующих процессов необходимы реализация и доказательства до объявления их production-ready.

1. **P0 — Patient/PHI access governance:** завершить инвентаризацию read surfaces, tenant isolation на уровне запросов, purpose-bound privileged access, надёжный PHI access audit, минимизацию полей и негативные двухтенантные тесты.
2. **P0 — Рабочий интерфейс фармацевта:** POS и основные процессы должны быть доступны и работоспособны в браузере; backend endpoints и placeholders навигации недостаточны.
3. **P0 — Dispensing с пациентом и рецептом:** определить авторизацию, валидацию, проверку фармацевтом, аудит и транзакционную связь до включения клинического отпуска.
4. **P0 — Patient-scoped AI state:** завершить staged validation persistence и переключения сессий между PostgreSQL checkpoints и Redis-backed memory.
5. **P1 — Доказательство восстановления:** провести backup/restore, migration rollback и recovery objectives в изолированном staging.
6. **P1 — Доказательство AI evaluation:** versioned expert-reviewed dataset, citation correctness, medication entity/negation checks и regression gates.
7. **P1 — Эксплуатационные доказательства:** telemetry privacy, end-to-end trace coverage, alert delivery, SLO и rollback exercises.
8. **P1 — Capacity evidence:** репрезентативная synthetic staging нагрузка с измеренными ограничениями; плановые допущения нельзя выдавать за capacity results.

## 4. Обязательная запись доказательств

Для каждого требования ведите запись со следующими полями:

| Поле | Обязательное значение |
|---|---|
| Requirement ID | Стабильный ID из этой матрицы |
| Owner | Ответственная инженерная роль/команда |
| ADR / control | ID ADR или ссылка на политику |
| Implementation | Файл/модуль/API/schema и commit |
| Test | Файл теста, case ID и точная команда |
| CI | Workflow, run ID, conclusion и проверенный SHA |
| Runtime | Среда, deployment/release ID и timestamp |
| Artifact | Неизменяемая ссылка на отчёт/log/trace |
| Уровень зрелости | Одно значение: L0–L6 со ссылками на доказательства |
| Limitations | Mocks, synthetic data, отсутствующая служба или непроверенный путь |
| Exit condition | Объективное условие закрытия строки |

## 5. Правила governance

- Benchmark requirements остаётся каноническим контрактом измерений; эта матрица связывает его с архитектурой и доказательствами реализации.
- Матрица аптечных процессов остаётся каноническим аудитом операционных процессов; не дублируйте здесь её подробные описания.
- Статус ADR не равен статусу реализации.
- CI привязан к commit. Успех на предыдущем SHA нельзя переносить на новый.
- Production verification требует явных доказательств из конкретной среды; source review и Codespaces недостаточны.
- Неизмеренное значение — NOT TESTED или UNAVAILABLE, никогда не ноль и не PASS.
- Не используйте реальные данные пациентов в benchmark, Demo или evaluation datasets.
- Финансовые результаты под NDA не включать в публичную документацию и CV.

## 6. Ближайшие действия

1. Повторно проверить текущий main по PHI read-surface inventory и закрыть либо обновить каждую находку доказательством на уровне кода.
2. Составить route-to-test map для P0 patient, prescription и POS workflows.
3. Проверить фактические runtime-версии и разделение Production/Demo через read-only inspection провайдера/БД.
4. Запустить benchmark suite в изолированном staging и опубликовать versioned report.
5. Добавить release evidence checklist со ссылками на точные CI и runtime artifacts для каждого блокирующего требования.

**Текущий вывод:** у Pharmaviyum есть существенная документированная инженерная основа и ряд подтверждённых аудитом исходного кода backend-контролей. Но инфраструктура, PHI governance, интерфейс фармацевта, staged AI isolation, recovery, observability и capacity остаются открытыми до появления актуальных воспроизводимых артефактов. Это не заявление о Production readiness.
