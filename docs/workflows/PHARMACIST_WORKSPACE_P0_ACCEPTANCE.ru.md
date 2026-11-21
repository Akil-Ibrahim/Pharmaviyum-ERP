# P0 Pharmacist Workspace — реализация и критерии приёмки

[English](./PHARMACIST_WORKSPACE_P0_ACCEPTANCE.md) · [Русский](./PHARMACIST_WORKSPACE_P0_ACCEPTANCE.ru.md)

**Статус:** backlog реализации и контракт приёмки  
**Область:** P0-процессы фармацевта и безопасность данных пациентов  
**Базовая версия:** `main`, commit `c6d35b828c1958f1bcb9077bbd0b6a71ef94613b`  
**Изменение application code этим документом:** нет

Документ превращает результаты аудита исходного кода в проверяемые P0-критерии поставки. Он не утверждает, что перечисленные ниже задачи уже реализованы.

## 1. P0.1 — Восстановить пользовательский интерфейс POS

### Подтверждённое состояние
- Транзакционный backend: `POST /api/v1/pos/checkout`, поиск товаров, просмотр серий, payment webhook и отдельная приёмка товара.
- Интеграционные тесты: `tests/integration/test_pos_checkout.py`.
- Активный frontend route: `frontend/shadcn-admin/src/routes/_authenticated/pos.tsx`.
- Текущая реализация feature: `frontend/shadcn-admin/src/features/pos/index.tsx`, возвращает `null`.

### Требования к реализации
- Заменить пустой feature полноценным рабочим процессом кассира на основе типизированных API-контрактов; бизнес-правила не дублировать в браузере.
- Поиск должен показывать идентичность препарата, дозировку/силу, форму выпуска, barcode/SKU и доступный остаток авторизованной аптеки.
- Выбор серии должен показывать срок годности и доступное количество; FEFO и допустимость остатка окончательно определяет backend.
- Содержимое корзины и итоговые суммы должны повторно проверяться сервером при checkout; суммы клиента — только отображение.
- Показывать состояние оплаты, идентификатор чека, pending/failed и понятный сценарий восстановления без дублирования продажи.
- Повторную отправку блокировать на время запроса, но корректность обеспечивать серверной idempotency.
- Не включать ввод пациента/рецепта до реализации P0.2. Не создавать впечатление, что обычная продажа уже является отпуском с проверенным рецептом.

### Критерии приёмки
1. Playwright journey: поиск → выбор товара → просмотр серий → оплата наличными → отображение чека → остаток отражает проведённое движение.
2. Playwright journey: безналичный checkout → pending payment → подтверждение подписанным webhook → завершённая продажа и чек.
3. Повтор с тем же idempotency key создаёт одну продажу, один идентификатор чека и не дублирует inventory movement.
4. При конкуренции за последнюю единицу два кассира не могут продать больше остатка; persisted stock и sale state согласованы.
5. Просроченные/недопустимые серии нельзя продать; FEFO проверяется по сохранённым данным, а не только по порядку UI.
6. Авторизация и pharmacy scope проверяются для каждого чтения и изменения.
7. Состояния empty/loading/timeout/validation/payment failure/server error пригодны для работы и доступны.
8. В UI fixtures и screenshots не используются реальные данные пациентов.

**Критерий завершения:** POS — рабочий browser workflow с реальным API и автоматизированными browser + API/integration тестами. Страница или mock-only flow недостаточны.

## 2. P0.2 — Безопасно связать пациента, рецепт и отпуск

### Подтверждённое состояние
- Доменные записи пациента, рецепта и POS-продажи существуют независимо.
- Checkout сейчас не устанавливает связь с пациентом/рецептом.
- Frontend route рецептов возвращает `null`.
- В базовой версии не найден сквозной тест prescription-to-checkout.

### Обязательное проектирование до реализации
- Определить каноническую связь sale, patient, prescription, prescription lines и dispensed sale lines. Нельзя использовать одну агрегированную запись истории покупок как единственный клинический след.
- Проверять принадлежность пациента и аптеки на сервере. Переданный клиентом patient ID — selector, а не доказательство доступа.
- Проверять статус рецепта, совпадение пациента, pharmacy scope, препарат, дозировку, форму, количество, повторы/refills, срок действия и применимые локальные правила.
- Проверка/override фармацевта должна быть явным, permission-checked, reason-coded и аудируемым решением. AI не может разрешать отпуск.
- Сохранять, кто проверил, что отпущено, какая строка рецепта исполнена, какая серия выделена, когда и с каким результатом.
- До включения процесса определить partial dispensing, cancellation, correction и reversal semantics.
- Не выводить юридические правила рецептурного отпуска из ответа AI; правила конкретной юрисдикции должны быть проверенной детерминированной policy.

### Критерии приёмки
1. Подмена рецепта другого пациента отклоняется.
2. Доступ к пациенту/рецепту другой аптеки отклоняется.
3. Просроченные, отменённые, исчерпанные или недействительные рецепты отклоняются согласно настроенной policy.
4. Несовпадение препарата, дозировки или формы отклоняется либо требует определённого pharmacist exception flow.
5. Отпущенное количество не превышает разрешённый остаток.
6. Partial dispensing и повтор запроса идемпотентны и сохраняют корректный остаток.
7. Sale, prescription fulfilment, lot movement и audit event фиксируются атомарно либо через явно протестированный saga/compensation contract.
8. Override фармацевта требует permission, причины и неизменяемого audit evidence.
9. Тесты покрывают race conditions, duplicate requests, rollback и tenant isolation.

**Критерий завершения:** воспроизводимая и протестированная цепочка patient → prescription → pharmacist verification → FEFO allocation → payment/receipt → patient history. AI остаётся decision support.

## 3. P0.3 — Создать API истории пациента с tenant scope

### Подтверждённое состояние
- `GET /api/v1/patient-purchases/` требует `CurrentSuperuser`.
- Текущий запрос напрямую выбирает `PatientPurchase`, не присоединяет `Patient`, не ограничивает выборку по `Patient.pharmacy_id` и не принимает идентификатор конкретного пациента.
- Поле `Patient.pharmacy_id` допускает `NULL`.
- Это глобальный административный список, а не API истории пациента для фармацевта.

### Требования к реализации
- Не открывать текущий глобальный административный endpoint обычным ролям фармацевта без явного пересмотра его назначения и авторизации.
- Создать отдельный patient-scoped API, требующий аутентифицированное членство в аптеке и selector пациента.
- Определять принадлежность пациента на сервере и ограничивать каждую запись истории авторизованной аптекой.
- Определить обработку legacy-записей с null/unassigned pharmacy ownership; до сверки таких записей обычный фармацевт не должен получать к ним доступ.
- Возвращать только поля, необходимые рабочему процессу фармацевта; не раскрывать лишние идентификаторы и финансовые данные.
- Создавать audit event при доступе к истории: actor, pharmacy, patient reference, purpose/context и timestamp. Не копировать клиническое содержимое в логи.
- Реализовать pagination, детерминированную сортировку, ограниченные date filters и response limits.

### Критерии приёмки
1. Фармацевт аптеки A получает историю только пациента, доступного в аптеке A.
2. Аптека A не может перечислить или получить покупки пациентов аптеки B, меняя ID, фильтры или pagination.
3. Пациенты с null/unassigned pharmacy не доступны обычным фармацевтам.
4. Неаутентифицированные пользователи и роли без разрешения отклоняются согласно RBAC policy.
5. Административный superuser-доступ проверяется и аудируется отдельно.
6. План запроса использует подходящие индексы patient/pharmacy для окончательной формы запроса.
7. Negative cross-tenant tests выполняются на PostgreSQL, а не только на mock repositories.

**Критерий завершения:** отдельные и явные admin и pharmacist contracts; cross-tenant denial подтверждён интеграционными тестами.

## 4. P0.4 — Завершить staged-проверку Mortarium patient-session isolation

### Подтверждённое состояние
- Patient-scoped API session HMAC v3 и Agent/RAG checkpoint namespaces объединены через PR #287.
- Regression tests существуют.
- Архитектурная документация сохраняет staged-проверку PostgreSQL checkpoint + Redis memory в качестве release gate.

### Обязательная проверка
В изолированном staging с синтетическими пациентами и выделенными PostgreSQL/Redis:
1. Повторно использовать одну client session для Patient A → Patient B → no patient.
2. Повторить сценарий в synchronous и streaming API.
3. Проверить, что Redis dialogue memory, summaries и derived facts не пересекают patient scopes.
4. Проверить, что Agent и RAG checkpoint threads различаются и не содержат raw patient/user/pharmacy identifiers.
5. Проверить, что cache entries не пересекают patient scopes.
6. Проверить, что два application instances создают одинаковые scopes при одинаковом secret.
7. Проверить, что отсутствие/ротация secret обрабатываются fail-closed и согласно политике ротации.
8. Проверить отсутствие raw patient identifiers и clinical payloads в logs, traces и evaluation artifacts.

**Критерий завершения:** воспроизводимые staged evidence приложены к release record. Merge и unit tests сами по себе этот gate не закрывают.

## 5. Порядок поставки и зависимости

| Порядок | Работа | Зависимость | Release gate |
|---:|---|---|---|
| 1 | P0.3 Авторизация API истории пациента | Patient/pharmacy ownership и политика legacy-записей | Cross-tenant integration tests |
| 2 | P0.2 Контракт patient/prescription/dispense | Клиническая policy и audit model | Prescription-to-sale invariants |
| 3 | P0.1 Browser workflow POS | Существующий POS API; P0.2 до включения prescription dispensing | Playwright + transactional tests |
| 4 | P0.4 Staged validation Mortarium | Стабильные staging PostgreSQL, Redis и secret configuration | Patient-switch isolation evidence |

Параллелить можно только работу, которая не ослабляет security boundary. Не включать patient history или prescription dispensing в UI до прохождения соответствующих gates.

## 6. Evidence и отчётность релиза

Для каждого gate фиксировать:
- commit SHA и environment;
- test command / workflow run URL;
- synthetic fixture design;
- ожидаемый и фактический результат;
- ошибки и remediation;
- reviewer и дату.

Использовать точные статусы доказательности: **Designed**, **Implemented**, **Tested**, **Staged-validated**, **Production-validated**. Нельзя повышать статус только на основании route, model, успешного unit test или объединённого PR.

Этот документ не разрешает production deployment, доступ к реальным данным пациентов или изменение application code.

## Повторный аудит исходного кода — main 481a86aa

В актуальном `main` есть PHI governance и pharmacy-scope predicates в Patient Repository с регрессионными тестами. См. [аудит доступа к PHI](../architecture/PHI_ACCESS_GOVERNANCE_AUDIT.md), [инвентаризацию чтения PHI](../security/PHI_READ_SURFACE_INVENTORY.md) и `tests/unit/test_patient_repository_tenant_scope.py`. Эти изменения не заменяют P0.3: отдельному API истории для фармацевта всё ещё нужны server-resolved pharmacy membership, fail-closed обработка legacy-пациентов, минимальные поля, аудит чтений, пагинация и PostgreSQL negative tests для межаптечного доступа. Глобальный endpoint, доступный только superuser, повторно использовать нельзя. Только source audit; не production validation.
