# Трассировка PHI: маршруты → тесты → доказательства

**Дата проверки:** 2026-11-22  
**Исходный baseline:** `main` на `2616b4209fc037b1e4f1899b876478bf72258641`; исторические findings сохранены там, где явно обозначены.  
**Область:** маршруты Patient API и чтение истории покупок пациента. Проверены исходники и существующие тесты; тесты этим документом не запускались. Runtime и данные пациентов не использовались.

## Назначение

Матрица связывает каждый маршрут, работающий с данными пациента, с границей авторизации, возвращаемыми данными, существующими тестами и следующим необходимым доказательством. Это не сертификат безопасности.

## Матрица маршрутов и доказательств

| Маршрут | Текущая авторизация / scope | Поверхность PHI или чувствительных данных | Существующие тесты | Текущий уровень | Следующее необходимое доказательство |
|---|---|---|---|---|---|
| `GET /api/v1/patients/` | Active user; pharmacy scope разрешается. Superuser может не передать pharmacy и получить global scope. | `PatientSummaryResponse`: demographic/contact и loyalty summary; без clinical, insurance, consultation и purchase relations. | В `tests/integration/endpoints/test_patients.py` есть list/search/pagination; legacy fixture ориентирован на superuser и не доказывает двухтенантную изоляцию обычных пользователей. | L1 | Добавить persisted two-tenant tests с ordinary members; проверить, что строки и counts не пересекают pharmacies. |
| `GET /api/v1/patients/statistics` | Active user; тот же scope resolver и global-поведение superuser. | Агрегаты по пациентам аптеки. | В проверенном наборе не найден отдельный тест tenant isolation для маршрута. | L1 | Проверить все aggregate queries и добавить cross-tenant проверки количества и агрегатов. |
| `GET /api/v1/patients/phone/{phone}` | Active user; scope разрешается; superuser может работать глобально. | `PatientSummaryResponse`; без clinical/insurance/consultation/purchase relations. | Отдельный негативный tenant-тест поиска по телефону не найден. | L1 | Двухтенантные phone collision/lookup tests и assertions авторизации ordinary users. |
| `GET /api/v1/patients/{patient_id}` | Active user; scope разрешается; superuser может работать глобально. | `PatientSummaryResponse`; широкий legacy `PatientResponse` больше не является стандартным контрактом этого маршрута. | Есть integration happy-path/not-found; покрытие cross-tenant denial для ordinary users остаётся неполным. | L1 | Двухтенантные allow/deny tests; проверка allowlist полей ответа. |
| `GET /api/v1/patients/{patient_id}/ai-profile` | Non-superuser; явные `pharmacy_id` и purpose; обязательны active membership и принадлежность активного пациента аптеке. Superuser запрещён. | Минимальный AI context: `patient_id`, allergies и conditions. Allowed/denied metadata записывается в `PHIAccessAudit`. | `tests/integration/test_ai_patient_profile_access.py` покрывает allowed, missing membership, cross-pharmacy denial и superuser denial. | L1 | Добавить audit-persistence failure injection и включить маршрут в более широкие exact-commit tenant tests. |
| `POST /api/v1/patients/` | Только superuser; `pharmacy_id` необязателен. Если scope не передан, пациент может быть создан без pharmacy ownership. | Создание идентификаторов и записи пациента. | Есть integration tests create/duplicate/unauthorized; явный тест запрета отсутствующего pharmacy scope не найден. | L1 | Требовать явный авторизованный tenant либо отдельно утверждённый workflow нераспределённой записи; тестировать отказ для null owner. |
| `PUT /api/v1/patients/{patient_id}` | Только superuser; scope необязателен; при его отсутствии возможен global update. | Изменение демографических данных пациента. | Есть integration update tests; двухтенантный denial test не найден. | L1 | Purpose-bound privileged update policy; двухтенантные deny tests; проверка audit event. |
| `DELETE /api/v1/patients/{patient_id}` | Только superuser; scope необязателен; при его отсутствии возможен global soft delete. | Состояние жизненного цикла пациента. | Есть integration soft-delete test; двухтенантный denial test не найден. | L1 | Управляемое support permission, tenant-scoped delete tests и durable audit. |
| `POST /api/v1/patients/{patient_id}/visit` | Active user; scope разрешается; superuser может работать глобально. | Посещение пациента и связанные коммерческие метаданные. | В проверенном наборе не найден tenant-specific test маршрута. | L1 | Двухтенантные allow/deny tests; минимизация event payload и аудит. |
| `GET /patient-purchases/` | Только superuser; обязателен явный `pharmacy_id`; запрос соединяет `Patient` и фильтрует по `Patient.pharmacy_id`. | Более широкий административный purchase projection: product, lot, receipt, quantity и price; этот handler не создаёт новый PHI read-audit event. | `tests/unit/test_patient_purchases_scope.py` проверяет query construction на mocks, а не persisted two-tenant behavior. | L1 | Управлять и аудировать этот privileged route; добавить database-backed authorization/audit tests либо заменить его более узким admin contract. |
| `GET /api/v1/patient-purchases/{patient_id}/history` | Non-superuser pharmacist; явные `pharmacy_id` и purpose; обязательны active membership и принадлежность активного пациента аптеке. Superuser запрещён. | Только минимальные поля: purchase ID, product name, category, quantity и timestamp. Allowed/denied metadata записывается в `PHIAccessAudit`. | `tests/integration/test_patient_history_tenant_scope.py` покрывает allowed, cross-pharmacy denial, missing membership, null-owner denial и superuser denial. | L1 | Добавить audit-persistence failure injection и сохранить exact-commit CI evidence. |
| MCP `get_patient_history` | Trusted context содержит только user, pharmacy и role; выбранного patient и purpose нет. Переданный моделью `patient_id` выбирает любого active patient в этой аптеке. | Возвращает name, age, gender, blood type, allergies, conditions, prescription/order counts, loyalty tier и language; `PHIAccessAudit` event не создаётся. | Есть общие MCP RBAC tests; patient-context mismatch, purpose и PHI-audit tests не обнаружены. | L1 | Связать patient/purpose с trusted context, ограничить patient ID инструмента, записывать allowed/denied audit events и тестировать mismatch/audit failure. |

## Сквозные наблюдения

1. `resolve_pharmacy_scope` остаётся tenant resolver, а не полной PHI policy. Общие patient/order routes по-прежнему допускают global superuser scope и не требуют purpose-of-use или durable read audit повсеместно.
2. Global superuser path намеренно присутствует в исходниках и тестах. Новые pharmacist AI-profile/history routes явно запрещают superuser; для общих patient/order и legacy admin paths по-прежнему нужна отдельно выдаваемая, ограниченная по времени, reason-coded и аудируемая support-access policy.
3. `Patient.pharmacy_id` допускает NULL. Superuser patient creation всё ещё может выполняться без pharmacy scope и создавать запись без владельца. Новый pharmacist history route отказывает в доступе к таким записям; не угадывайте ownership при remediation.
4. Стандартные patient routes теперь используют `PatientSummaryResponse`, а AI-profile/history routes — более узкие projections. Не возвращайте legacy `PatientResponse` в route contracts; продолжайте проверять все response DTO.
5. Unit tests, проверяющие generated SQL, полезны как query-shape evidence, но не доказывают database-backed isolation, transaction behavior или API denial semantics. Новые route-specific PostgreSQL integration tests дают более сильные доказательства только для двух scoped HTTP routes; они не покрывают все patient/order/admin/MCP reads.
6. Pharmacy-server Compose использует initial `POSTGRES_USER` credential повторно для backend/worker/beat runtime connections. В репозитории не создаётся отдельная non-superuser runtime role и grants. Поэтому PHI audit triggers не доказывают append-only protection против application credential; проверьте `rolsuper`, table privileges и попытки изменения triggers/schema под фактической runtime role.

## Повторная проверка исходников — 2026-11-22

`PHIAccessAudit` — append-only metadata-only table; Alembic triggers запрещают UPDATE, DELETE и TRUNCATE. `tests/integration/test_phi_access_audit_immutability.py` проверяет эти операции и отказ migration при удалении сохранённых audit records. Это evidence реализации, но не утверждение, что каждый PHI access path записывает audit. Legacy admin purchase listing и общие patient/order reads не имеют полного purpose-bound audit coverage.

## Правила зрелости доказательств

- Наличие исходника и файла теста само по себе не поднимает уровень выше L1, пока релевантный тест не пройден на точном commit и не сохранён его артефакт.
- L2 требует актуального exact-commit результата unit tests.
- L3 требует database-backed/API integration tests с двумя tenant, positive/negative assertions, поведением null-owner и отказом аудита.
- L4 требует полного browser/API workflow с проверкой durable outcome и audit.
- На основании этой проверки исходников ни один маршрут не имеет уровня L5 или L6.

## P0 критерии приёмки

- [ ] Для всех маршрутов определены tenant и permission policy, включая superuser/support.
- [ ] Отсутствующее или неоднозначное владение пациентом приводит к fail-closed в аптечных процессах.
- [ ] Создание пациента не может молча создавать PHI-запись с null tenant ownership.
- [ ] Purpose-specific DTO исключают не относящиеся к процессу клинические/коммерческие поля.
- [ ] Разрешённый и запрещённый доступ к PHI надёжно аудируется без payload с PHI.
- [ ] Audit storage append-only для application role; сценарий отказа проверен.
- [ ] Двухтенантные integration tests покрывают все маршруты, включая AI profile и patient purchases.
- [ ] Только synthetic fixtures; реальные данные пациентов не используются в тестах и Demo.

**Вывод:** в текущем коде есть существенные tenant-aware controls, но полная изоляция и governance набора patient-facing маршрутов ещё не доказаны. До появления database-backed двухтенантных integration evidence соответствующий PHI workflow должен оставаться ниже L3.
