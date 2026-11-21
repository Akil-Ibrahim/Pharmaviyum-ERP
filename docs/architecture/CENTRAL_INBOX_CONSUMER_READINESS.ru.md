# Central Inbox Consumer — аудит готовности

**Дата проверки:** 2026-11-19  
**Решение:** только надёжный приём событий; применение к доменным данным отключено.  
**Область:** проверка текущего исходного кода `main`. Это gate реализации, а не подтверждение production readiness.

## 1. Подтверждённое текущее поведение

Текущий Central ingress в `src/pharmaviyum/api/v1/sync.py` аутентифицирует зарегистрированный Edge-узел, получает `pharmacy_id` из его регистрации, отклоняет несовпадающую идентичность узла, валидирует и сохраняет событие в `CentralInboxEvent`, а затем возвращает `accepted` только после commit транзакции Inbox. Идентичный дубликат event ID получает подтверждение durable receipt; повторное использование event ID с другим содержимым отклоняется.

Текущая модель Inbox (`src/pharmaviyum/models/sync.py`) хранит идентификаторы события, pharmacy/node scope, event/schema/aggregate identity, timestamps, payload, `processing_status` и `processing_error`. В ней пока нет worker lease/fencing fields, ограниченного retry scheduling, счётчиков попыток или aggregate checkpoint model.

В проверенной реализации нет Central domain consumer. `accepted` означает только надёжное получение события, а не применение его к остаткам, продажам или платежам.

## 2. Покрытие текущего event contract

Строгая v1-схема в `src/pharmaviyum/schemas/sync.py` сейчас разрешает только:

- `pos.sale.created` — версия sale aggregate 1;
- `pos.sale.cancelled` — версия sale aggregate 2;
- `pos.payment.succeeded` — версия sale aggregate 2;
- `pos.payment.failed` — версия sale aggregate 2.

v1 валидирует денежные значения в decimal-string формате, итоги продажи, количества товаров, суммы lot allocations, состояние платежа, inventory effect, запрет дополнительных полей и лимит payload 256 KiB.

Это контракт жизненного цикла POS sale, а не полный контракт складской синхронизации. Отдельные события для goods receipts, adjustments, write-offs, expiry disposal, transfer dispatch/receipt и opening balances сейчас не описаны. Нельзя создавать универсальный stock consumer, самостоятельно додумывая семантику этих операций.

Результат версии 2 для одной продажи взаимоисключающий: cancellation либо payment settlement/failure. Central должен отклонять или помещать в quarantine конфликтующие event ID одной aggregate version. Нельзя выбирать победителя по времени поступления.

## 3. Существующие доменные модели и ограничения сопоставления

### Аптечные остатки и партии

`Inventory` — текущая запись остатка/партии в scope конкретной аптеки. Естественная уникальность: `(product_id, pharmacy_id, lot_number)`; также есть составная идентичность `(id, pharmacy_id, product_id)`.

`InventoryMovement` — append-only журнал движений. Он содержит idempotency key в scope аптеки, составной foreign key, связывающий inventory/pharmacy/product, остатки и резервы до/после операции, ограничения типов движений и дельт, идентичность исполнителя и необязательные business reference/correlation.

Central должен сохранять эти инварианты и создавать факты движения, а не перезаписывать реплицированное количество.

### POS projection

Модели `Sale`, `SaleItem`, `SaleItemAllocation` и `Payment` хранят продажу, строки, распределение по партиям и платежи. Idempotency constraints продажи и платежа привязаны к соответствующему scope.

Edge payload содержит `product_sku`, `lot_number` и количество распределения, но не Edge `product_id` и не `inventory_id`. Следовательно, Central необходимы явный pharmacy-scoped SKU crosswalk и правило разрешения партии до безопасного сопоставления строки с Central product и inventory lot.

Нельзя считать SKU глобально уникальным. Нельзя искать партию только по `lot_number`. Сопоставление должно находить ровно один активный Central product для авторизованной аптеки и ровно одну совместимую партию в scope этого product/pharmacy. Отсутствующее или неоднозначное соответствие отправляется в quarantine; событие продажи не должно автоматически создавать product или lot.

Событие не содержит Central identity кассира Edge. Нельзя копировать локальный integer ID в `cashier_user_id`. До создания Central sale нужно определить аудируемое сопоставление исполнителя или отдельную модель source-originated sale projection.

### Legacy и patient-oriented модели

`ProductBatch` не имеет pharmacy scope и не является авторитетной моделью для FEFO или stock mapping в Central. Consumer не должен использовать её.

Legacy `Order` / `PatientPurchase` ориентированы на пациента и не заменяют POS sale/payment/lot-модель. Не объединять эти агрегаты и не добавлять patient identifiers в общую POS-синхронизацию.

## 4. Требования к Central consumer

До реализации утвердить контракт event handlers, затем реализовать:

1. **Claim:** короткая транзакция с `FOR UPDATE SKIP LOCKED`, проверкой статуса и времени следующего retry.
2. **Lease:** уникальный lease token, expiry, attempt number и fencing-проверка при каждом завершении/ошибке. Устаревший worker не должен фиксировать результат после takeover.
3. **Ordering:** durable checkpoint по ключу `(pharmacy_id, aggregate_type, aggregate_id)`. Применять только следующую ожидаемую версию. Будущие версии сохранять как pending; не перескакивать через gap.
4. **Idempotency:** event ID и aggregate version остаются уникальными. Идентичный повтор — no-op; одинаковая identity с разным содержимым — protocol conflict.
5. **Atomic application:** в одной DB-транзакции блокировать Inbox row/checkpoint, проверять mapping и доменные инварианты, записывать sale/payment projection и inventory movement facts, обновлять projection остатка, продвигать checkpoint и помечать событие processed.
6. **Failure handling:** временные DB/worker ошибки повторять с bounded exponential backoff и jitter. Постоянные mapping/domain conflicts отправлять в quarantine с reason codes и durable operator audit. Replay сохраняет исходные event ID и payload.
7. **Reconciliation:** сравнивать Edge-originated sale/payment и movement references с Central projections; выявлять missing, duplicate, unmapped и mismatched records без скрытого изменения остатков.
8. **Observability:** измерять возраст старейших accepted/pending событий, backlog, attempts, lease expirations, gap age, quarantine count, replay outcomes и per-pharmacy acknowledgement lag. Не логировать raw payload и patient data.

## 5. Release gates до любых доменных side effects

- [ ] Pharmacy-scoped product/SKU crosswalk с правилами уникальности и жизненного цикла.
- [ ] Детерминированное разрешение lot и политика конфликтов expiry/lot.
- [ ] Явная provenance кассира Edge; никаких выдуманных Central user IDs.
- [ ] Утверждённые Central sale/payment projection и семантика финансового ledger.
- [ ] Полный event contract для складских операций вне POS allocations.
- [ ] Atomic transaction и concurrency tests для последней единицы товара и duplicate events.
- [ ] Gap recovery, stale-lease fencing, worker crash, retry/quarantine tests.
- [ ] Replay audit и reconciliation tests.
- [ ] Synthetic multi-pharmacy integration tests на disposable PostgreSQL.
- [ ] Runbooks для backup/restore и staged rollout/rollback.

## 6. Решение

**GO:** продолжать read-only проектирование контракта и mapping, создавать fixtures/tests, реализовать worker infrastructure под отключённым feature flag после утверждения доменных контрактов.

**NO-GO:** пока не применять принятые Inbox events к production sales, payments, inventory balances или patient records. Не заполнять отсутствующие product/lot/actor mappings догадками. Не включать consumer только потому, что Inbox row надёжно сохранена.

Этот gate сохраняет границу durable receipt и не позволяет превращать транспортное подтверждение в непроверенную финансовую или складскую проводку.
