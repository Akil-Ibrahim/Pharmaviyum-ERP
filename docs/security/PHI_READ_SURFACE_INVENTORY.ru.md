# Инвентаризация PHI read-поверхностей — дополнительная проверка исходного кода

**Дата проверки:** 2026-11-22  
**База:** `main` на `2616b4209fc037b1e4f1899b876478bf72258641`  
**Область:** выборочная read-only проверка patient API, patient service/repository, response schemas, MCP patient-history tool, order API и in-process event bus. База данных, runtime, production data и secrets не использовались.

## Краткий итог

Проверка расширяет первоначальный PHI governance audit. Найдены дополнительные риски на уровне исходного кода, которые нужно закрыть до заявления о полной tenant isolation и PHI access governance.

**Дополнительные критические findings:** MCP patient-history tool не связан с выбранным patient/purpose, а Ansible Compose использует PostgreSQL bootstrap user как runtime credential приложения. Эти gaps ограничивают защитную ценность route-level PHI audit.

**Эта проверка не доказывает эксплуатацию уязвимости или утечку в production.** Некоторые выводы относятся к потенциально опасным repository-методам, call sites которых ещё не полностью прослежены. Это цели обязательной проверки, а не утверждения о подтверждённой внешней эксплуатируемости.

## Находки

### F-01 — Repository query scope реализован; доказательство изоляции на уровне БД ещё требуется

Файл: `src/pharmaviyum/repositories/patient.py`

- В текущем `main` методы `get_recent_patients` и `get_top_customers` добавляют `Patient.pharmacy_id == pharmacy_id`, если scope передан.
- `tests/unit/test_patient_repository_tenant_scope.py` компилирует оба запроса и проверяет pharmacy predicate.
- Оба метода возвращают ORM-объекты Patient, а не агрегированную проекцию.
- Текущие тесты доказывают корректное построение SQL, но не end-to-end изоляцию между двумя сохранёнными pharmacy; все call sites ещё нужно сопоставить.

**Статус:** ранее описанный дефект отсутствия predicate не воспроизводится в проверенной ревизии `main`. Не следует считать его открытым дефектом исходного кода.

**Оставшиеся действия:** добавить integration tests на двух pharmacy, доказывающие, что tenant-scoped вызов не возвращает пациентов другого tenant, и сопоставить все call sites. Если есть глобальный административный сценарий, выделить для него отдельно названный и явно авторизованный метод вместо необязательного scope.

### F-02 — Исторический finding: широкая PatientResponse раскрывала лишнюю PHI; стандартные patient routes теперь используют PatientSummaryResponse

Файлы: `src/pharmaviyum/schemas/patient.py`, `src/pharmaviyum/api/v1/endpoints/patients.py`, `src/pharmaviyum/repositories/patient.py`

- Legacy schema `PatientResponse` содержит conditions (включая treatment notes/current medications/notes), allergies, insurance, consultations и purchase history.
- До исправления стандартные patient endpoints использовали широкую Patient response model либо возвращали широкий связанный объект.
- Repository detail query по умолчанию загружает clinical/insurance/consultation relations и purchase lines.
- Dedicated AI profile schema и результат repository не соответствовали друг другу: schema требовала `patient_id` и `phone`, тогда как repository возвращал `id` и посторонние demographic/purchase aggregates. Это могло приводить к response validation failure.

**Риск:** один общий patient-read contract раскрывал несколько не связанных с конкретным workflow классов данных, нарушая minimum-necessary design и увеличивая вероятность случайной выдачи PHI.

**Исправление в PR:** ввести `PatientSummaryResponse` как стандартный контракт для list/create/update/get/get-by-phone/visit. Стандартные patient endpoints больше не сериализуют clinical, insurance, consultation или purchase relations. Create/update/summary repository reads явно отключают eager loading связей. AI profile сужен до purpose-bound clinical safety context: только patient_id, allergies и conditions; repository query не загружает insurance, consultation и purchase relations. Regression tests проверяют response allowlist и соответствие AI-profile schema.

**Исправление в последующем PR:** `GET /patients/{patient_id}/ai-profile` теперь требует явные purpose code и pharmacy ID, запрещает platform superuser, требует активное `PharmacyMembership`, проверяет активное владение пациентом на уровне SQL и записывает metadata-only решения `PHIAccessAudit` для разрешённого и запрещённого доступа. Request ID ограничен 128 символами. Integration tests покрывают разрешённый доступ, отсутствие membership, cross-pharmacy отказ и отказ superuser. Широкая `PatientResponse` остаётся только legacy-моделью и не должна использоваться в route contracts. Это закрывает только риск AI-profile endpoint, но не все patient PHI read surfaces.

### F-03 — Patient lifecycle events содержат связываемые идентификаторы

Файл: `src/pharmaviyum/services/patient.py`

- PR #385 удаляет `patient_id`, `full_name`, `phone` и `country` из generic payload события `patient.created`; остаётся только `pharmacy_id`.
- `patient.updated`, `patient.deleted` и `patient.visit_recorded` по-прежнему содержат стабильный patient ID в generic event payload; их минимизация остаётся открытой задачей.
- Поиск по исходному коду не обнаружил in-repository subscribers через `event_bus.on(...)`. Это не доказывает отсутствие динамически зарегистрированных или внешних consumers.
- Лог создания пациента больше не содержит patient ID.
- Event bus — process-local и best-effort (`src/pharmaviyum/services/event_bus.py`); общий лог emit записывает тип события и количество handlers, а не payload.

**Риск:** стабильный patient ID — связываемые персональные данные. Их присутствие в generic lifecycle events позволит будущим subscribers или telemetry integrations сопоставлять события с пациентскими записями вне purpose-bound workflow.

**Исправление:** удалить patient identifiers из generic `patient.created`; оставить только tenant-level routing metadata. Остальные lifecycle events требуют такой же проверки. Если workflow необходим patient reference, нужно определить отдельный permissioned event contract и явную authorization path для lookup, а не повторно использовать generic event bus.

### F-04 — Два patient mutation helpers применяют scope; другим mutation helpers не хватает явного tenant scope

Файл: `src/pharmaviyum/repositories/patient.py`

- Текущий `main` применяет `Patient.pharmacy_id == pharmacy_id` непосредственно в начальных SELECT-запросах методов `soft_delete` и `record_visit`.
- SQL regression tests проверяют наличие predicates и отсутствие мутации, когда scoped lookup не возвращает строку.
- Другие helpers, например `restore`, `update_loyalty`, `add_allergy`, `add_condition`, не принимают pharmacy scope в сигнатуре; авторизация их callers ещё не прослежена полностью.

**Статус:** ранее описанная проблема unscoped initial lookup не присутствует в проверенной ревизии `main`.

**Оставшиеся действия:** сопоставить всех callers helpers без scope; добавить явный trusted tenant context и scoped database predicates там, где это требуется. Добавить cross-tenant integration tests на repository и API уровнях.

### F-05 — Patient и order APIs сохраняют глобальный scope superuser; новый pharmacist history route имеет более узкие контроли

Файлы: `src/pharmaviyum/modules/auth/tenant.py`, `src/pharmaviyum/api/v1/endpoints/patients.py`, `src/pharmaviyum/api/v1/orders.py`, `src/pharmaviyum/api/v1/patient_purchases.py`

- `resolve_pharmacy_scope` возвращает переданный pharmacy ID для superuser и `None`, если superuser его не указал.
- Patient list/detail/search/statistics routes и order read/mutation handlers передают этот результат в service/repository; `None` означает отсутствие pharmacy predicate в проверенных query paths.
- Новый `GET /patient-purchases/{patient_id}/history` устроен иначе: требует pharmacy ID и один из трёх purpose codes, запрещает superuser principals, проверяет active `PharmacyMembership`, принадлежность пациента аптеке и записывает metadata-only allowed/denied audit records.
- Legacy `GET /patient-purchases/` остаётся доступен только superuser и требует pharmacy ID, но в проверенной реализации не использует новый PHI audit record.

**Риск:** специализированный purchase-history route имеет purpose и membership gate, однако общие patient endpoints и order handlers всё ещё допускают глобальный superuser scope без purpose-bound grant и read audit. Это дизайн глобального привилегированного доступа, а не доказательство tenant escape обычного пользователя.

**Необходимые действия:** внедрить отдельное решение platform-support authorization (grant, reason, expiry, разрешённое действие, patient/tenant scope) и обязательный аудит привилегированного доступа ко всем PHI read surfaces. Расширить новый audit contract на обычные patient reads и другие PHI-bearing paths. Не отключать superuser workflow без анализа операционных сценариев.

### F-06 — Order и purchase tenant predicates проверяются непосредственно в SQL

Файл: `src/pharmaviyum/api/v1/orders.py`

- В create path пациент первоначально загружался только по ID, после чего `patient.pharmacy_id` сравнивался в Python.
- В order detail и status-update paths выполнялся JOIN с Patient, но фильтр был только по `Order.id`; tenant ownership проверялся уже после загрузки результата Order/Patient.
- При завершении заказа Patient повторно загружался по ID без pharmacy predicate.
- Поиск дублирующего receipt фильтровался только по receipt number, без JOIN с tenant-владельцем Patient.
- Эти post-fetch проверки отклоняли несовпадающий непустой scope до защищённой записи, но не обеспечивали tenant isolation на границе SQL-запроса.

**Риск:** строки другого tenant могли попасть в память приложения до отказа в авторизации. Проверка receipt также полагалась на глобальную уникальность формата receipt, а не на явный tenant predicate. Эта проверка не доказывает production disclosure или cross-tenant mutation.

**Исправление в PR #387:** общие query builders добавляют `Patient.pharmacy_id == scope` в patient, order и purchase lookups, если tenant scope определён. Существующее глобальное поведение superuser при scope `None` сохраняется. PostgreSQL SQL-compilation regression tests и полный CI прошли. Database-backed integration coverage на двух tenant всё ещё необходима.

### F-07 — MCP patient-history tool ограничен аптекой, но не patient-context/purpose-bound и не записывает PHI audit

Файлы: `src/pharmaviyum/ai/mcp/context.py`, `src/pharmaviyum/api/v1/ai.py`, `src/pharmaviyum/ai/mcp/schemas.py`, `src/pharmaviyum/ai/mcp/tools/patient_history.py`

- `MCPAuthorizationContext` содержит только `user_id`, `pharmacy_id` и `user_role`. AI API передаёт эти поля; выбранный `patient_id`, используемый для HMAC session namespace, не включён в MCP authorization context.
- `PatientHistoryRequest` принимает `patient_id`, переданный моделью, и не содержит purpose-of-use.
- Запрос инструмента проверяет `Patient.id`, доверенный `pharmacy_id` и active status. Это блокирует cross-pharmacy lookup, но не доказывает, что запрошенный пациент совпадает с пациентом, выбранным для текущей AI-сессии.
- Инструмент возвращает full name, age, gender, blood type, allergies, conditions, active-prescription count, recent-order count, loyalty tier и preferred language.
- Инструмент не записывает `PHIAccessAudit`. Текущий log содержит только counts и latency, не записывая patient ID или clinical payload.

**Риск:** AI session, привязанная к Patient A, потенциально может запросить Patient B в той же аптеке, потому что trusted MCP context не содержит/не проверяет выбранного пациента и purpose. Это authorization gap в исходном коде, а не доказательство раскрытия данных в Production.

**Требуемые действия:** связать MCP context с выбранным patient и purpose; требовать совпадение patient ID инструмента с этим context либо отдельный authorization для смены пациента; записывать allowed/denied `PHIAccessAudit`; сузить output schema; добавить mismatch, missing-purpose, denied-access и audit-failure integration tests.

### F-08 — Runtime database credential является PostgreSQL bootstrap superuser; audit triggers не обеспечивают полную неизменяемость

Файлы: `ansible/roles/app-backend/files/docker-compose-backend.yml`, `ansible/group_vars/all.yml`, `ansible/roles/postgresql/tasks/main.yml`, `alembic/versions/2026_11_21_000001_phi_access_audit.py`

- Pharmacy-server Compose profile инициализирует PostgreSQL через `POSTGRES_USER` (по умолчанию `app_user`) и передаёт тот же username/password в `DATABASE_URL` для backend, Celery worker и Celery beat.
- При первоначальном создании data volume стандартный PostgreSQL container entrypoint создаёт `POSTGRES_USER` как bootstrap superuser. В репозитории не обнаружено последующего разделения ролей, runtime role с `NOSUPERUSER` или grants, запрещающих application credential менять audit schema objects.
- Текущая Ansible role `postgresql` создаёт/проверяет data directory и сообщает состояние container; она не создаёт отдельные runtime, owner, migration и audit roles и не проверяет DB privileges.
- PHI audit migration добавляет triggers против UPDATE/DELETE/TRUNCATE, но database superuser или table owner может отключить/удалить triggers или изменить таблицу. Runtime application credential не должен иметь такие privileges.
- Production Alembic guard требует `MIGRATION_DATABASE_URL`, но public Ansible migration environment его не передаёт; отдельный migration credential и least-privilege path ещё не подключены.

**Риск:** append-only trigger полезен как defense in depth, но текущая конфигурация репозитория не доказывает, что приложение не может его обойти. Это риск конфигурации/code path, а не доказательство злоупотребления live Production role.

**Требуемые действия:** создать bootstrap-only superuser, ограниченную runtime role, контролируемую migration role и при необходимости отдельную audit writer/owner role. Убедиться, что runtime role не superuser и не может ALTER/DROP/TRUNCATE audit storage или отключать triggers. Добавить PostgreSQL tests для `pg_roles.rolsuper`, `has_table_privilege`, trigger protection и попыток изменения schema/triggers. Не передавать migration credentials в application runtime environment.

## Наблюдавшиеся положительные контроли

- Для обычных пользователей `resolve_pharmacy_scope` проверяет active `PharmacyMembership`; при нескольких membership требуется явный pharmacy ID.
- MCP patient-history tool получает pharmacy ID из trusted MCP context и включает его в patient, prescription-count и order-count queries.
- AI API проверяет переданный patient ID относительно авторизованной аптеки до вызова harness.
- Эти контроли не заменяют отдельный PHI access audit и не доказывают end-to-end tenant isolation без integration tests.

## Следующая последовательность реализации

1. Проследить все call sites helpers без явного scope из F-01 и F-04, а также каждый путь сериализации Patient ORM.
2. Добавить two-pharmacy integration tests для уже scoped query/mutation methods и tenant predicates в оставшиеся mutation paths, где они необходимы.
3. Завершить rollout purpose-specific patient DTO; добавлять отдельные clinical/insurance/purchase endpoints только при наличии workflow и проверить аудит AI-profile access.
4. Минимизировать generic patient event payload и проверить каждого subscriber/forwarder.
5. Реализовать отдельный PHI access audit event и privileged-support policy из основного governance audit.
6. Проверить API, dashboard, reports, exports, background jobs, MCP и Edge paths до закрытия инвентаризации.

## Критерии приёмки

- [ ] Каждый repository method с pharmacy parameter действительно применяет его либо явно обозначен как global и защищён отдельной авторизацией.
- [ ] Тесты двух tenant доказывают изоляцию patient query и mutation.
- [ ] Patient response schemas возвращают только поля, необходимые конкретному workflow.
- [ ] Generic events и telemetry не содержат прямых идентификаторов пациентов и клинических payload; стабильные patient ID рассматриваются как связываемые данные.
- [ ] Доступ superuser к данным пациента ограничен purpose и аудируется.
- [ ] Для каждой patient read-поверхности определены владелец, authorization policy, классификация ответа и поведение аудита.

## Ограничения

Это целевая проверка исходного кода, а не полный security assessment. Полнота call graph, runtime behavior, число строк в БД, production configuration и поведение внешних subscribers не проверены. Документ не устанавливает соответствие HIPAA, GDPR или национальному законодательству.
