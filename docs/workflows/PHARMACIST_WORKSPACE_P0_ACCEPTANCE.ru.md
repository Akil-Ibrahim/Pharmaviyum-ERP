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

## 3. P0.3 — Создать tenant-scoped API истории пациента (базовая реализация есть; приёмка продолжается)

### Подтверждённая реализация
- `GET /api/v1/patient-purchases/{patient_id}/history` — отдельный pharmacist-facing route. Он требует явные `pharmacy_id` и ограниченный purpose code, запрещает platform superuser, требует active `PharmacyMembership`, проверяет принадлежность активного пациента выбранной аптеке и отказывает для null/unassigned patients.
- Ответ содержит только минимальный allowlist: purchase ID, product name, category, quantity и purchase timestamp.
- Allowed и denied decisions записываются как metadata-only `PHIAccessAudit`; clinical payload в audit event не копируется.
- `tests/integration/test_patient_history_tenant_scope.py` покрывает allowed access, cross-pharmacy denial, missing membership, null-owner denial и superuser denial.
- Сопутствующий `GET /api/v1/patients/{patient_id}/ai-profile` использует явные pharmacy/purpose/membership checks и metadata-only audit; его сценарии покрывает `tests/integration/test_ai_patient_profile_access.py`.
- Alembic migration для `PHIAccessAudit` добавляет DB triggers, запрещающие UPDATE, DELETE и TRUNCATE; `tests/integration/test_phi_access_audit_immutability.py` проверяет эти ограничения и сохранность evidence при downgrade.
- Legacy `GET /patient-purchases/` остаётся только для superuser, требует явный pharmacy ID и теперь соединяет/фильтрует по `Patient.pharmacy_id`. Он всё ещё возвращает более широкий административный projection и не записывает новый PHI access audit event.

### Что ещё требуется
- Добавить failure-injection tests: PHI read должен fail closed, если audit persistence/commit завершается ошибкой.
- Решить, сохранять, сужать или заменять legacy administrative listing; если сохранять — определить и реализовать audit и privileged-access policy.
- Управлять оставшимися global superuser reads в общих patient/order routes через отдельную purpose-bound support-access policy; новые pharmacist routes намеренно запрещают superuser.
- Сохранить exact-commit PostgreSQL integration CI artifacts и проверить query plan/index истории пациента на утверждённой схеме.
- Не считать этот read API patient-linked dispensing: POS checkout всё ещё не связан с patient/prescription.

### Критерии приёмки
1. Route-specific integration tests выше должны пройти на точном candidate commit.
2. Фармацевт аптеки A получает только историю пациента, принадлежащего аптеке A; cross-pharmacy и null-owner requests завершаются fail closed.
3. Отсутствующее membership и platform-superuser requests отклоняются и надёжно аудируются.
4. Allowlist полей ответа проверяется тестами.
5. До заявления о полном PHI governance нужно проверить поведение при сбое audit persistence.
6. Для legacy administrative access и остальных global superuser paths определены ответственный владелец и audit policy.

**Текущий статус:** pharmacist patient-history API и route-level audit реализованы в исходниках и имеют PostgreSQL integration tests. P0.3 не считается полностью принятым до exact-commit CI evidence, audit-failure tests и завершения политики оставшегося privileged read. Это не является Production/site acceptance evidence.

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
