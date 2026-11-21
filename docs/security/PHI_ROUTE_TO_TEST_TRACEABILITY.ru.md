# Трассировка PHI: маршруты → тесты → доказательства

**Дата проверки:** 2026-11-21  
**Исходный baseline:** PHI audit для `main`: `c6d35b828c1958f1bcb9077bbd0b6a71ef94613b`  
**Область:** маршруты Patient API и чтение истории покупок пациента. Проверены исходники и существующие тесты; тесты этим документом не запускались. Runtime и данные пациентов не использовались.

## Назначение

Матрица связывает каждый маршрут, работающий с данными пациента, с границей авторизации, возвращаемыми данными, существующими тестами и следующим необходимым доказательством. Это не сертификат безопасности.

## Матрица маршрутов и доказательств

| Маршрут | Текущая авторизация / scope | Поверхность PHI или чувствительных данных | Существующие тесты | Текущий уровень | Следующее необходимое доказательство |
|---|---|---|---|---|---|
| `GET /api/v1/patients/` | Active user; pharmacy scope разрешается. Superuser может не передать pharmacy и получить global scope. | Список: имя, телефон, email, местоположение и loyalty-данные. | В `tests/integration/endpoints/test_patients.py` есть list/search/pagination; в проверенных кейсах нет двухтенантной проверки изоляции. | L1 | Integration tests на двух сохранённых в БД аптеках; проверка отсутствия чужих строк и агрегатов. |
| `GET /api/v1/patients/statistics` | Active user; тот же scope resolver и global-поведение superuser. | Агрегаты по пациентам аптеки. | В проверенном наборе не найден отдельный тест tenant isolation для маршрута. | L1 | Проверить все aggregate queries и добавить cross-tenant проверки количества и агрегатов. |
| `GET /api/v1/patients/phone/{phone}` | Active user; scope разрешается; superuser может работать глобально. | Возвращается широкий `PatientResponse`. | Отдельный негативный tenant-тест поиска по телефону не найден. | L1 | Двухтенантные тесты поиска/совпадения телефона; DTO с полями по назначению. |
| `GET /api/v1/patients/{patient_id}` | Active user; scope разрешается; superuser может работать глобально. | Широкий `PatientResponse`: состояния, заметки о лечении, аллергии, страхование, консультации и покупки. | Есть integration happy-path/not-found; cross-tenant denial в проверенных кейсах не найден. | L1 | Двухтенантные allow/deny tests; тесты allowlist полей DTO. |
| `GET /api/v1/patients/{patient_id}/ai-profile` | Active user; scope разрешается; superuser может работать глобально. | Профиль пациента для AI context. | Отдельный tenant isolation test для маршрута не найден. | L1 | Cross-tenant denial; проверка передачи в AI только минимально необходимых разрешённых полей. |
| `POST /api/v1/patients/` | Только superuser; `pharmacy_id` необязателен. Если scope не передан, пациент может быть создан без pharmacy ownership. | Создание идентификаторов и записи пациента. | Есть integration tests create/duplicate/unauthorized; явный тест запрета отсутствующего pharmacy scope не найден. | L1 | Требовать явный авторизованный tenant либо отдельно утверждённый workflow нераспределённой записи; тестировать отказ для null owner. |
| `PUT /api/v1/patients/{patient_id}` | Только superuser; scope необязателен; при его отсутствии возможен global update. | Изменение демографических данных пациента. | Есть integration update tests; двухтенантный denial test не найден. | L1 | Purpose-bound privileged update policy; двухтенантные deny tests; проверка audit event. |
| `DELETE /api/v1/patients/{patient_id}` | Только superuser; scope необязателен; при его отсутствии возможен global soft delete. | Состояние жизненного цикла пациента. | Есть integration soft-delete test; двухтенантный denial test не найден. | L1 | Управляемое support permission, tenant-scoped delete tests и durable audit. |
| `POST /api/v1/patients/{patient_id}/visit` | Active user; scope разрешается; superuser может работать глобально. | Посещение пациента и связанные коммерческие метаданные. | В проверенном наборе не найден tenant-specific test маршрута. | L1 | Двухтенантные allow/deny tests; минимизация event payload и аудит. |
| `GET /patient-purchases/` | Только superuser; обязателен явный `pharmacy_id`; запрос соединяет Patient и фильтрует по pharmacy. | Покупки пациента, товар, партия, количество, цена и признак prescription-required. | `tests/unit/test_patient_purchases_scope.py` проверяет скомпилированный SQL на mock-объектах, но не две реальные записи в БД. | L1 | Integration test с двумя сохранёнными аптеками; проверка отсутствия чужих покупок и корректной авторизации/аудита. |

## Сквозные наблюдения

1. `resolve_pharmacy_scope` — resolver tenant-контекста, а не полная PHI policy. Он не требует purpose-of-use, отдельного patient permission или надёжного события аудита доступа.
2. Global superuser path намеренно присутствует в исходниках и тестах. Нельзя просто удалить его без анализа операций; его нужно заменить отдельно выдаваемым, ограниченным по времени, reason-coded и аудируемым support-access policy.
3. `Patient.pharmacy_id` допускает NULL. Создание пациента без явного pharmacy scope может создать запись без владельца. Нельзя угадывать tenant при исправлении таких записей.
4. Широкий `PatientResponse` следует разделить на workflow-specific DTO с явными allowlists полей.
5. Unit-тесты генерации SQL полезны для проверки формы запроса, но не доказывают изоляцию на реальной БД, транзакционное поведение или API denial semantics.

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
