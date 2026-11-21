# Инвентаризация PHI read-поверхностей — дополнительная проверка исходного кода

**Дата проверки:** 2026-11-21  
**База:** текущая default branch `main`  
**Область:** выборочная read-only проверка patient API, patient service/repository, response schemas, MCP patient-history tool, order API и in-process event bus. База данных, runtime, production data и secrets не использовались.

## Краткий итог

Проверка расширяет первоначальный PHI governance audit. Найдены дополнительные риски на уровне исходного кода, которые нужно закрыть до заявления о полной tenant isolation и PHI access governance.

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

### F-02 — Patient response schema возвращает широкий набор клинических и коммерческих связей

Файлы: `src/pharmaviyum/schemas/patient.py`, `src/pharmaviyum/api/v1/endpoints/patients.py`, `src/pharmaviyum/repositories/patient.py`

- `PatientResponse` включает conditions (в том числе treatment notes/current medications/notes), allergies, insurance, consultations и purchase history.
- `get_patient` и `get_patient_by_phone` возвращают эту широкую response model.
- Repository заранее загружает allergies, conditions, insurances, consultations и purchases для patient detail path.
- Та же response model используется в ответах create/update/visit.

**Риск:** одно разрешение на чтение пациента открывает широкий payload из нескольких классов данных. Это усложняет принцип minimum necessary и увеличивает вероятность случайного раскрытия информации.

**Необходимые действия:** определить purpose-specific DTO (например, краткая демография, контекст безопасности отпуска лекарства, страховой workflow) с явными allowlists полей. Не возвращать consultation notes, insurance identifiers или purchase history без необходимости конкретного workflow. Добавить schema contract tests, проверяющие отсутствие запрещённых полей в каждом endpoint response.

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

### F-05 — Patient и order APIs сохраняют глобальную область superuser без pharmacy ID

Файлы: `src/pharmaviyum/modules/auth/tenant.py`, `src/pharmaviyum/api/v1/endpoints/patients.py`, `src/pharmaviyum/api/v1/orders.py`

- `resolve_pharmacy_scope` возвращает переданный pharmacy ID для superuser и `None`, если superuser его не указал.
- Patient list/detail/search/statistics передают результат в service/repository; в проверенных repository methods `None` означает отсутствие pharmacy predicate.
- Order read и mutation handlers также позволяют superuser оставаться в глобальной области без pharmacy ID.

**Риск:** привилегированный доступ в этих handlers не ограничен purpose, временем или отдельным аудитом чтения. Это дизайн глобального привилегированного доступа, а не доказательство tenant escape обычного пользователя.

**Необходимые действия:** внедрить отдельное решение platform-support authorization (grant, reason, expiry, разрешённое действие, patient/tenant scope) и обязательный аудит привилегированного доступа к данным пациента. Не отключать superuser workflow без анализа операционных сценариев.

### F-06 — Order и purchase lookups проверяют tenant ownership после чтения строк

Файл: `src/pharmaviyum/api/v1/orders.py`

- В create path пациент первоначально загружался только по ID, после чего `patient.pharmacy_id` сравнивался в Python.
- В order detail и status-update paths выполнялся JOIN с Patient, но фильтр был только по `Order.id`; tenant ownership проверялся уже после загрузки результата Order/Patient.
- При завершении заказа Patient повторно загружался по ID без pharmacy predicate.
- Поиск дублирующего receipt фильтровался только по receipt number, без JOIN с tenant-владельцем Patient.
- Эти post-fetch проверки отклоняли несовпадающий непустой scope до защищённой записи, но не обеспечивали tenant isolation на границе SQL-запроса.

**Риск:** строки другого tenant могли попасть в память приложения до отказа в авторизации. Проверка receipt также полагалась на глобальную уникальность формата receipt, а не на явный tenant predicate. Эта проверка не доказывает production disclosure или cross-tenant mutation.

**Исправление в работе:** общие query builders добавляют `Patient.pharmacy_id == scope` в patient, order и purchase lookups, если tenant scope определён. Существующее глобальное поведение superuser при scope `None` сохраняется. SQL compilation regression tests проверяют наличие predicates; database-backed integration coverage на двух tenant всё ещё необходима.

## Наблюдавшиеся положительные контроли

- Для обычных пользователей `resolve_pharmacy_scope` проверяет active `PharmacyMembership`; при нескольких membership требуется явный pharmacy ID.
- MCP patient-history tool получает pharmacy ID из trusted MCP context и включает его в patient, prescription-count и order-count queries.
- AI API проверяет переданный patient ID относительно авторизованной аптеки до вызова harness.
- Эти контроли не заменяют отдельный PHI access audit и не доказывают end-to-end tenant isolation без integration tests.

## Следующая последовательность реализации

1. Проследить все call sites helpers без явного scope из F-01 и F-04, а также каждый путь сериализации Patient ORM.
2. Добавить two-pharmacy integration tests для уже scoped query/mutation methods и tenant predicates в оставшиеся mutation paths, где они необходимы.
3. Разделить широкую PatientResponse на purpose-specific DTO с allowlists и contract tests.
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
