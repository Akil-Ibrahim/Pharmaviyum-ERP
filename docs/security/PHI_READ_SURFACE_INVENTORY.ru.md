# Инвентаризация PHI read-поверхностей — дополнительная проверка исходного кода

**Дата проверки:** 2026-11-21  
**База:** текущая default branch `main`  
**Область:** выборочная read-only проверка patient API, patient service/repository, response schemas, MCP patient-history tool, order API и in-process event bus. База данных, runtime, production data и secrets не использовались.

## Краткий итог

Проверка расширяет первоначальный PHI governance audit. Найдены дополнительные риски на уровне исходного кода, которые нужно закрыть до заявления о полной tenant isolation и PHI access governance.

**Эта проверка не доказывает эксплуатацию уязвимости или утечку в production.** Некоторые выводы относятся к потенциально опасным repository-методам, call sites которых ещё не полностью прослежены. Это цели обязательной проверки, а не утверждения о подтверждённой внешней эксплуатируемости.

## Находки

### F-01 — Repository-методы принимают pharmacy scope, но не применяют его

Файл: `src/pharmaviyum/repositories/patient.py`

- `get_recent_patients(limit, pharmacy_id)` принимает `pharmacy_id`, но не добавляет его в запрос.
- `get_top_customers(limit, pharmacy_id)` принимает `pharmacy_id`, но не добавляет его в запрос.
- Оба метода возвращают ORM-объекты Patient, а не агрегированную проекцию.
- Все call sites в рамках этой проверки не перечислены.

**Риск:** вызывающий код может полагаться на контракт параметра и считать запрос tenant-scoped, хотя фактически получает строки из разных аптек. Это дефект изоляции на repository-уровне, если методы используются в tenant-scoped workflow.

**Необходимые действия:** найти все call sites; добавить pharmacy predicates; написать negative tests на двух аптеках, доказывающие, что tenant-scoped вызов не возвращает пациентов другого tenant. Если существует глобальный административный сценарий, выделить для него отдельно названный и явно авторизованный метод, а не использовать необязательный scope.

### F-02 — Patient response schema возвращает широкий набор клинических и коммерческих связей

Файлы: `src/pharmaviyum/schemas/patient.py`, `src/pharmaviyum/api/v1/endpoints/patients.py`, `src/pharmaviyum/repositories/patient.py`

- `PatientResponse` включает conditions (в том числе treatment notes/current medications/notes), allergies, insurance, consultations и purchase history.
- `get_patient` и `get_patient_by_phone` возвращают эту широкую response model.
- Repository заранее загружает allergies, conditions, insurances, consultations и purchases для patient detail path.
- Та же response model используется в ответах create/update/visit.

**Риск:** одно разрешение на чтение пациента открывает широкий payload из нескольких классов данных. Это усложняет принцип minimum necessary и увеличивает вероятность случайного раскрытия информации.

**Необходимые действия:** определить purpose-specific DTO (например, краткая демография, контекст безопасности отпуска лекарства, страховой workflow) с явными allowlists полей. Не возвращать consultation notes, insurance identifiers или purchase history без необходимости конкретного workflow. Добавить schema contract tests, проверяющие отсутствие запрещённых полей в каждом endpoint response.

### F-03 — Patient lifecycle events содержат прямые идентификаторы

Файл: `src/pharmaviyum/services/patient.py`

- `create_patient` отправляет в `patient.created` поля `patient_id`, `full_name`, `phone`, `country` и `created_by`.
- `update_patient` отправляет patient ID и список изменённых полей.
- Event bus — process-local и best-effort (`src/pharmaviyum/services/event_bus.py`); текущий общий лог emit записывает тип события и количество handlers, а не payload.
- Полный граф subscribers и возможная внешняя пересылка/логирование не были исчерпывающе прослежены.

**Риск:** прямые идентификаторы попадают в общий application event channel. Будущие subscribers, telemetry exporters или интеграции могут передать их в системы без PHI controls.

**Необходимые действия:** заменить прямые идентификаторы в общих событиях на opaque references и минимальные метаданные; для обоснованных клинических workflow использовать отдельный permissioned clinical event contract. Добавить тесты, что event payload не содержит имя, телефон, email, DOB, clinical notes или prescription data. Проверить всех subscribers до включения внешней доставки.

### F-04 — Tenant-scoped mutation helpers сначала выполняют unscoped lookup

Файл: `src/pharmaviyum/repositories/patient.py`

- `soft_delete(id, pharmacy_id)` и `record_visit(id, pharmacy_id)` сначала загружают пациента по ID без pharmacy predicate, затем сравнивают pharmacy ID, если scope передан.
- Сейчас методы возвращают false/None при несовпадении tenant до применения мутации, но первоначальное чтение из БД уже было unscoped.
- Другие helpers, например `restore`, `update_loyalty`, `add_allergy`, `add_condition`, не принимают pharmacy scope в сигнатуре; авторизация их callers полностью не прослежена.

**Риск:** defense-in-depth и auditability слабее, чем при едином scoped query. Внутренний caller может случайно обойти предполагаемый tenant contract.

**Необходимые действия:** использовать scoped SELECT/UPDATE predicates непосредственно в SQL; требовать явный trusted tenant context для patient mutations; перечислить call sites и проверить cross-tenant denial на repository и API уровнях.

### F-05 — Patient и order APIs сохраняют глобальную область superuser без pharmacy ID

Файлы: `src/pharmaviyum/modules/auth/tenant.py`, `src/pharmaviyum/api/v1/endpoints/patients.py`, `src/pharmaviyum/api/v1/orders.py`

- `resolve_pharmacy_scope` возвращает переданный pharmacy ID для superuser и `None`, если superuser его не указал.
- Patient list/detail/search/statistics передают результат в service/repository; в проверенных repository methods `None` означает отсутствие pharmacy predicate.
- Order read и mutation handlers также позволяют superuser оставаться в глобальной области без pharmacy ID.

**Риск:** привилегированный доступ в этих handlers не ограничен purpose, временем или отдельным аудитом чтения. Это дизайн глобального привилегированного доступа, а не доказательство tenant escape обычного пользователя.

**Необходимые действия:** внедрить отдельное решение platform-support authorization (grant, reason, expiry, разрешённое действие, patient/tenant scope) и обязательный аудит привилегированного доступа к данным пациента. Не отключать superuser workflow без анализа операционных сценариев.

## Наблюдавшиеся положительные контроли

- Для обычных пользователей `resolve_pharmacy_scope` проверяет active `PharmacyMembership`; при нескольких membership требуется явный pharmacy ID.
- MCP patient-history tool получает pharmacy ID из trusted MCP context и включает его в patient, prescription-count и order-count queries.
- AI API проверяет переданный patient ID относительно авторизованной аптеки до вызова harness.
- Эти контроли не заменяют отдельный PHI access audit и не компенсируют repository methods, игнорирующие переданный pharmacy parameter.

## Следующая последовательность реализации

1. Проследить все call sites F-01 и F-04, а также каждый путь сериализации Patient ORM.
2. Добавить tenant predicates в repository methods и scoped mutation statements; добавить negative integration tests с двумя synthetic pharmacies.
3. Разделить широкую PatientResponse на purpose-specific DTO с allowlists и contract tests.
4. Минимизировать generic patient event payload и проверить каждого subscriber/forwarder.
5. Реализовать отдельный PHI access audit event и privileged-support policy из основного governance audit.
6. Проверить API, dashboard, reports, exports, background jobs, MCP и Edge paths до закрытия инвентаризации.

## Критерии приёмки

- [ ] Каждый repository method с pharmacy parameter действительно применяет его либо явно обозначен как global и защищён отдельной авторизацией.
- [ ] Тесты двух tenant доказывают изоляцию patient query и mutation.
- [ ] Patient response schemas возвращают только поля, необходимые конкретному workflow.
- [ ] Generic events и telemetry не содержат прямых идентификаторов пациентов и клинических payload.
- [ ] Доступ superuser к данным пациента ограничен purpose и аудируется.
- [ ] Для каждой patient read-поверхности определены владелец, authorization policy, классификация ответа и поведение аудита.

## Ограничения

Это целевая проверка исходного кода, а не полный security assessment. Полнота call graph, runtime behavior, число строк в БД, production configuration и поведение внешних subscribers не проверены. Документ не устанавливает соответствие HIPAA, GDPR или национальному законодательству.
