# Управление доступом к PHI — архитектурный аудит исходного кода

**Дата проверки:** 2026-11-21  
**Базовая версия:** `main`, commit `c6d35b828c1958f1bcb9077bbd0b6a71ef94613b`  
**Область:** read-only проверка patient, purchase, tenant, audit-log и synchronization файлов. Production DB и runtime не использовались.

## Итоговое решение

**NO-GO для заявления о завершённом governance доступа к данным пациентов.** В репозитории есть общая модель `AuditLog` и явные pharmacy memberships, но проверенный endpoint чтения покупок пациентов имеет глобальную область для superuser, общая audit-модель не содержит измерений, необходимых для расследования доступа к PHI, а `Patient.pharmacy_id` допускает NULL.

Это вывод по исходному коду, а не доказательство эксплуатации уязвимости или подтверждённой утечки в production. Endpoint требует активного superuser. Проблема в том, что привилегированный доступ шире аптечного workflow, а в проверенном обработчике не обнаружены patient-level authorization и аудит чтения.

## 1. Подтверждённые факты реализации

### 1.1 API чтения покупок пациентов

Файл: `src/pharmaviyum/api/v1/patient_purchases.py`

- `GET /patient-purchases/` требует `CurrentSuperuser`.
- Запрос выбирает `PatientPurchase` без join к `Patient` и без фильтра по `Patient.pharmacy_id`.
- Ответ содержит patient ID, сведения о продукте, партии, номер чека, количество, цены, prescription-required и время покупки.
- Пагинация ограничена (`limit <= 200`), но пагинация не обеспечивает tenant isolation.
- В проверенном handler не создаётся audit event чтения.

**Интерпретация:** это привилегированная глобальная read-поверхность. Проверка роли superuser — это authorization check, но не purpose-bound аптечная политика доступа. Не следует называть это доказанным обходом tenant isolation для обычного пользователя.

### 1.2 Владение пациентом в tenant-модели

Файл: `src/pharmaviyum/models/patients/patient.py`

- `Patient.pharmacy_id` допускает NULL.
- Модель содержит прямые идентификаторы и чувствительные поля: имя, дата рождения, телефон, email, адрес, национальные/страховые идентификаторы, аллергии и заметки о хронических состояниях.
- В проверенном ORM-объявлении обязательное pharmacy ownership не обеспечено.

**Интерпретация:** владение legacy-записями нельзя считать установленным автоматически. Перед обязательным pharmacy scope нужно инвентаризировать строки с NULL и определить явную проверяемую процедуру установления владельца. Нельзя угадывать аптеку по телефону, сессии пользователя, покупке или текущему Inventory.

### 1.3 Существующая общая audit-модель

Файл: `src/pharmaviyum/models/audit_log.py`

Существующий `AuditLog` хранит actor ID/type, action, entity/entity ID, необязательный JSON changes, IP, user agent и timestamp.

В нём явно не представлены:
- pharmacy/tenant scope;
- ссылка на пациента как субъект доступа, отдельно от целевого ресурса;
- события read/view/search/export/print;
- результат authorization (allowed/denied);
- purpose-of-use или reason code;
- request/trace/correlation ID;
- source channel и authentication context;
- состояние break-glass и approval/review;
- версия policy/permission.

Само наличие модели не доказывает, что чтение чувствительных данных аудируется. Проверенный patient-purchase handler её не использует.

### 1.4 Membership и обход через superuser

Файлы: `src/pharmaviyum/models/pharmacy_membership.py`, `src/pharmaviyum/modules/auth/tenant.py`

- `PharmacyMembership` связывает пользователя с аптекой и содержит active flag.
- `require_pharmacy_tenant` проверяет активное членство обычного пользователя.
- Helper намеренно разрешает superuser любую запрошенную аптеку без membership.
- `resolve_pharmacy_scope` позволяет superuser оставаться в глобальной области, если pharmacy не указана.

**Интерпретация:** helper полезен для tenant-scoped operational API, но сам по себе не является PHI policy. Для чувствительных данных пациента нужны явный pharmacy context, проверка владения пациентом, purpose/permission checks и audit event. Глобальный доступ superuser должен быть отдельной управляемой административной возможностью.

### 1.5 Граница Central Inbox

Файлы: `src/pharmaviyum/models/sync.py`, `src/pharmaviyum/api/v1/sync.py`, `docs/adr/ADR-0007-central-inbox-consumer.md`

- Edge ingress получает pharmacy scope из аутентифицированной регистрации Edge node, а не из недоверенного поля запроса.
- Central Inbox сохраняет durable receipt и возвращает `accepted` после commit.
- Central domain consumer пока отсутствует. `accepted` не означает, что продажа, платёж или Inventory были применены.
- ADR явно блокирует бизнес-эффекты до выполнения требований к product/lot/actor mapping, полноте event contract, idempotency, ordering и atomicity.

**Требование безопасности:** обычная POS-синхронизация не должна превращаться в транспорт пациентских записей или клинического контекста. Не добавлять PHI в POS event contract без отдельного одобренного clinical synchronization design. Не записывать raw Inbox payload в логи.

### 1.6 Другие patient-facing поверхности, выборочно проверенные

Целевой поиск по исходному коду выявил дополнительные поверхности; проверка была выборочной, а не исчерпывающей:

- `src/pharmaviyum/api/v1/endpoints/patients.py`: handlers списка, карточки, поиска по телефону, статистики и AI-профиля вызывают `resolve_pharmacy_scope` и передают полученную область в patient service. Для обычных пользователей helper требует активное membership или единственное однозначное membership. Для superuser отсутствие `pharmacy_id` намеренно сохраняет глобальную область. Следовательно, patient API учитывает tenant для обычных пользователей, но глобальное чтение superuser остаётся возможным и требует отдельной управляемой support policy.
- `src/pharmaviyum/ai/mcp/tools/patient_history.py`: запрос пациента и подсчёты prescriptions/orders явно фильтруются по `pharmacy_id` из доверенного MCP context; один только tool input не выбирает tenant. Это положительный контроль в проверенном пути, но он не заменяет аудит доступа.
- `src/pharmaviyum/api/v1/orders.py`: чтение заказа разрешает pharmacy scope и сравнивает аптеку связанного пациента. Superuser может оставаться в глобальной области, если scope не передан. Создание и изменение статуса заказа доступны только superuser и должны входить в review привилегированного доступа.
- `src/pharmaviyum/api/v1/ai.py`: AI-запросы требуют авторизованный pharmacy context и проверяют optional patient ID относительно этой аптеки до вызова harness; session IDs HMAC-scoped по pharmacy, user и patient. Это положительный authorization/session-isolation контроль, но исходный код не демонстрирует отдельный PHI read audit event.

В репозитории также есть patient repositories и dashboard aggregates. Полный call graph, query filters, response fields и role policy остаются частью обязательной исчерпывающей инвентаризации. Результаты поиска сами по себе не доказывают безопасность каждого caller.

## 2. Целевая политика

### 2.1 Решение об авторизации

Каждая операция с данными пациента должна проверять на сервере:

1. аутентифицированного активного principal;
2. активное pharmacy membership и роль/permission в рамках аптеки;
3. принадлежность пациента этой аптеке (либо отдельно одобренную cross-pharmacy care relationship);
4. разрешение на конкретное действие (read, update, dispense, export, delete и т. д.);
5. purpose-of-use / reason code там, где это требуется политикой;
6. явный отказ, если ownership или scope отсутствует либо неоднозначен.

Глобальный флаг `is_superuser` не должен незаметно превращать каждый patient endpoint в неограниченный доступ к клиническим данным. Доступ platform support должен выдаваться отдельно, быть ограниченным по времени, иметь reason code, журналироваться и подлежать review.

### 2.2 Контракт PHI access audit event

Нужен отдельный append-only контракт аудита доступа к PHI; общих логов изменений сущностей недостаточно. Минимальные поля:

- immutable event ID и UTC timestamp;
- actor ID и actor type (human, service, Edge/system);
- tenant/pharmacy ID;
- subject type и стабильная ссылка на пациента (без копирования идентификаторов пациента);
- action: read, search, create, update, dispense, export, print, disclose, break-glass;
- resource type и resource reference;
- decision: allowed или denied, с ограниченным reason code;
- purpose-of-use / workflow context;
- request ID и trace ID;
- source channel (API, UI, MCP/tool, background job, Edge);
- authentication/session context, достаточный для расследования, без credentials;
- break-glass approval/reviewer fields, если применимо.

Не хранить в audit metadata клинические payload, полные request/response body, prescriptions, notes, tokens, secrets и ненужные прямые идентификаторы. Использовать контролируемые reason-code словари и ограниченные строки.

### 2.3 Целостность и эксплуатация аудита

- Надёжно сохранять решение доступа и audit record; определить поведение при сбое audit persistence. Для PHI reads — fail closed, если политика требует durable audit и безопасного fallback нет.
- Запретить application DB role UPDATE/DELETE audit records; использовать DB privileges и/или append-only triggers и покрыть тестами.
- Отделить retention security audit от обычных application logs; определить сроки хранения, legal hold, экспорт и access-review с учётом применимого законодательства.
- Ограничить просмотр audit log отдельным permission; аудитировать и доступ к самому журналу.
- По умолчанию исключить PHI из logs и traces. Использовать opaque IDs, redaction, low-cardinality metrics и явные allowlists.
- Создать alerts для необычных массовых чтений, повторных отказов, cross-pharmacy access attempts, exports и break-glass.

## 3. Безопасная последовательность реализации

1. **Инвентаризировать все patient read surfaces.** API routes, dashboard queries, search, reports, exports, AI/MCP tools, background jobs и Edge contracts. Классифицировать поля и назначение.
2. **Определить ownership semantics.** Разобрать строки `Patient.pharmacy_id IS NULL` через проверяемый migration plan. Явно определить cross-pharmacy sharing; не выводить его автоматически.
3. **Определить pharmacy-scoped роли и permissions.** Membership — граница tenant, но не роль. Добавить явные permissions для patient data и policy platform support.
4. **Реализовать authorization service.** Загружать patient row и проверять pharmacy ownership в том же query/transaction, что и чтение; fail closed при отсутствующем или неоднозначном ownership.
5. **Реализовать PHI access audit event.** Тесты allowed/denied reads, сбоя audit persistence, break-glass, export и доступа к audit log.
6. **Сузить глобальный patient-purchase endpoint.** Предпочтителен явный pharmacy-scoped route и server-side patient ownership. Platform-wide support workflow должен быть отдельным, ограниченным по времени и аудируемым. Не менять существующий API без проверки consumers и совместимости.
7. **Добавить negative integration tests.** User A не читает пациента B из другой аптеки; superuser требует designated support policy; пациент без owner scope получает fail closed; denied attempts аудируются; application role не может изменять audit records.
8. **Проверить на staging с synthetic data.** Миграции, query plans, audit throughput, retention и alert delivery. Production rollout запрещён до репетиции backup/restore и rollback.

## 4. Acceptance gates

- [ ] Для каждого patient-data read surface документированы owner, scope и permission.
- [ ] Ни одно чтение данных пациента не опирается только на глобальную роль.
- [ ] NULL/неоднозначное patient ownership приводит к fail closed.
- [ ] Разрешённый и запрещённый доступ аудируется без записи PHI payload.
- [ ] Audit records append-only для application DB role.
- [ ] Break-glass явный, ограниченный по времени, с reason code и review.
- [ ] Cross-pharmacy, export, MCP и background-job tests проходят на synthetic fixtures.
- [ ] Redaction в logging/tracing проверена тестами.
- [ ] Production access review и retention policy одобрены.

## 5. Не входит в этот аудит и ограничения безопасности

- Аудит не меняет application code, DB schema, production data, secrets, permissions или deployment.
- Он не устанавливает соответствие HIPAA, GDPR или национальному законодательству о медицинских данных. Применимость и требования нуждаются в отдельной юридической проверке по юрисдикции.
- Он не разрешает unrestricted superuser access или автоматическое переназначение legacy patients.
- Он не включает patient data в Central POS Inbox events.

**Исторический статус на source baseline от 2026-11-21:** реализация ещё не была начата. Ниже приведён follow-up от 2026-11-22 с текущей частичной remediation. PHI access governance остаётся release blocker до выполнения всех gates для соответствующих patient-level маршрутов.

## 6. Статус последующей реализации — 2026-11-22

Read-only проверка `main` на `2616b4209fc037b1e4f1899b876478bf72258641` подтверждает частичную реализацию после исторического аудита:

- Стандартные patient list/detail/phone routes теперь используют `PatientSummaryResponse` вместо широкого legacy `PatientResponse`.
- `GET /api/v1/patients/{patient_id}/ai-profile` требует явные pharmacy и purpose, active membership и принадлежность пациента аптеке; запрещает platform superuser и записывает metadata-only allowed/denied `PHIAccessAudit` decisions.
- `GET /api/v1/patient-purchases/{patient_id}/history` — отдельный pharmacist-facing route с такими же explicit pharmacy/purpose/membership/ownership controls. Он запрещает superuser и пациентов с null owner, возвращает минимальный projection и записывает allowed/denied audit decisions.
- Legacy `GET /patient-purchases/` остаётся только для superuser и требует явный pharmacy ID; его query теперь соединяет `Patient` и фильтрует по `Patient.pharmacy_id`. Он всё ещё возвращает более широкий administrative projection и не создаёт новый PHI audit event.
- Таблица `PHIAccessAudit` защищена DB triggers, запрещающими UPDATE, DELETE и TRUNCATE; integration tests проверяют эти controls и downgrade guard для сохранённых evidence.

Оставшиеся gaps: общие patient/order routes всё ещё допускают global superuser scope; создание пациента по-прежнему может не указывать nullable pharmacy ownership; legacy administrative purchase listing не использует новый read audit; не завершены support-access governance, audit-persistence failure tests, полное покрытие маршрутов и telemetry redaction evidence. MCP `get_patient_history` получает trusted user/pharmacy/role context, но не выбранный patient или purpose; он может запросить другого active patient в той же аптеке и не записывает `PHIAccessAudit`. Кроме того, Ansible Compose повторно использует PostgreSQL bootstrap `POSTGRES_USER` для application runtime connections; отдельная non-superuser runtime role в репозитории не создаётся, поэтому trigger-only append-only enforcement не доказана против application credential. Наличие route-specific integration tests — это evidence в исходниках, а не утверждение об успешном exact-commit CI или Production acceptance.

Этот follow-up не устанавливает legal/regulatory compliance и не сертифицирует live Production deployment.
