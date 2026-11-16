# ADR-0007: Central Inbox Consumer и упорядоченное применение доменных событий

**Статус:** Proposed — архитектура определена; реализация заблокирована доменными prerequisites  
**Дата:** 2026-11-16  
**Ответственные:** инженерная команда Pharmaviyum

## Контекст

Pharmacy Edge записывает POS-события в transactional outbox. Edge dispatcher доставляет их в Central API с гарантией at-least-once. Central аутентифицирует зарегистрированный Edge identity, проверяет контракт событий v1 и сохраняет durable receipt `CentralInboxEvent` со статусом `processing_status=accepted`.

В текущей реализации Central domain-event consumer отсутствует. Celery-задача `dispatch_outbox_batch` является Edge-side outbox publisher, а не Central Inbox Consumer. Поэтому подтверждение `accepted` означает только надёжный приём события, но не применение продажи, платежа или складского эффекта.

Текущая схема Inbox обеспечивает дедупликацию событий и уникальность версии агрегата, но пока не содержит lease-механизма consumer-а, планирования повторов, истории попыток, quarantine-семантики и checkpoint применённой версии.

## Решение

Реализовать Central Consumer как отдельный application service и worker. HTTP ingress оставить ограниченным аутентификацией, валидацией схемы, durable receipt и подтверждением приёма. PostgreSQL остаётся источником истины; Celery/Redis может пробуждать или планировать worker, но не должен владеть долговечностью событий или состоянием их обработки.

Протокол обеспечивает **at-least-once delivery и идемпотентные бизнес-эффекты**. Гарантия exactly-once доставки по сети не заявляется.

### 1. Durable state machine обработки

Использовать следующие постоянные состояния:

| Состояние | Значение |
|---|---|
| `accepted` | Receipt зафиксирован; событие ожидает обработки |
| `processing` | Worker захватил событие с fenced lease |
| `retry_wait` | Произошла временная ошибка; назначено время повтора |
| `processed` | Все доменные эффекты и aggregate checkpoint атомарно зафиксированы |
| `quarantined` | Постоянный конфликт контракта/доменных данных требует вмешательства оператора |

Разрешённые переходы:

- `accepted -> processing`
- `retry_wait -> processing`, когда `next_attempt_at <= now()`
- `processing -> processed` только в той же транзакции, что и все доменные эффекты и обновление checkpoint
- `processing -> retry_wait` при временной ошибке
- `processing -> quarantined` при постоянном доменном/контрактном нарушении или исчерпании политики повторов
- просроченный lease состояния `processing` может быть перехвачен другим worker; старый lease token больше не должен разрешать изменение состояния

Нельзя помечать событие как processed до commit доменных эффектов. Нельзя удалять poison events или незаметно пропускать их.

### 2. Durable claim и контроль конкуренции

Аддитивно расширить `central_inbox_events` операционными полями:

- `attempt_count` — неотрицательное целое число;
- `next_attempt_at` — UTC timestamp;
- `locked_until` — UTC timestamp, nullable;
- `lease_token` — случайный UUID/string, nullable;
- `last_attempt_at` и `processed_at` — nullable UTC timestamps;
- `processor_version` — nullable string для аудита и диагностики.

Добавить partial/compound index для поиска готовых к обработке событий `accepted`/`retry_wait` и событий `processing` с истёкшим lease. Поле `processing_error` должно быть ограниченным и очищенным от чувствительных данных. Не сохранять в тексте ошибки полный payload, credentials, patient identifiers или секреты провайдеров.

Захватывать ограниченную batch-выборку в короткой транзакции с PostgreSQL `FOR UPDATE SKIP LOCKED`. Назначать новый lease token и срок его действия, увеличивать счётчик попыток. Перед обработкой и изменением статуса worker обязан повторно проверить актуальный lease token после блокировки Inbox row. Устаревший worker не может подтверждать событие или менять расписание повтора для более нового claim.

### 3. Порядок агрегатов и восстановление пропусков

Создать durable aggregate checkpoint с ключом:

`(pharmacy_id, aggregate_type, aggregate_id)`

Checkpoint хранит последнюю успешно применённую `aggregate_version` и последний применённый `event_id`.

- Новый агрегат начинается с версии 0; первая применимая версия — 1.
- Событие допускается к обработке, только если его версия равна `last_applied_version + 1`.
- Более поздняя версия при отсутствии predecessor остаётся ожидающей/retryable; применять её вне очереди запрещено.
- Конфликтующее событие с уже занятой версией агрегата является protocol conflict и должно быть отклонено на ingress или помещено в quarantine.
- Не вводить глобальный порядок между аптеками или независимыми агрегатами.
- Обновлять checkpoint в той же транзакции, что и доменные эффекты и переход Inbox в `processed`.

Существующее unique constraint на `(pharmacy_id, aggregate_type, aggregate_id, aggregate_version)` остаётся последней защитой от дублирования версии.

### 4. Атомарное применение доменных эффектов

Каждое событие обрабатывается в одной транзакции PostgreSQL:

1. Заблокировать Inbox event и проверить актуальный lease token.
2. Заблокировать/создать aggregate checkpoint и проверить ожидаемую следующую версию.
3. Повторно проверить событие на domain boundary: ingress validation сама по себе не даёт права менять бизнес-данные.
4. Найти каждый продукт по canonical SKU, а каждую партию — по аутентифицированной аптеке, продукту и lot number. Не доверять локальным числовым Edge ID.
5. Проверить идентичность продукта/партии, expiry metadata и pharmacy scope. Неизвестные или неоднозначные соответствия помещать в quarantine; не создавать продукт или партию автоматически из события продажи.
6. Применить каждую дельту остатка/резерва через общий `apply_inventory_movement`.
7. Формировать детерминированный ограниченный idempotency key движения из `event_id` и стабильных позиций item/allocation. Использовать event ID как correlation reference.
8. Сохранить Central sale/payment projection и обновить aggregate checkpoint.
9. Установить Inbox status `processed` и выполнить commit.

Все движения по allocations одного события, sale/payment projection, checkpoint и завершение Inbox должны фиксироваться или откатываться вместе. Сбой до commit не оставляет частичного бизнес-эффекта. Повтор после commit видит `processed` и не создаёт второе движение.

Использовать `actor_type=system` для Central integration actor, если Central user identity отсутствует; исходный Edge node и event reference сохранять в correlation/reference metadata. Не выдумывать и не переиспользовать Central cashier user для кассира Edge.

### 5. Обязательные доменные prerequisites перед включением POS Consumer

Текущего контракта v1 недостаточно для безопасной складской проекции:

- Сейчас передаются события создания/отмены продажи и платежей, но ещё не определён полный поток приёмок, корректировок, списаний, возвратов, перемещений и утверждённая исходная база opening balance/snapshot.
- Нельзя применять списание продажи к Central lot, исходное количество которого неизвестно или не подтверждено.
- SKU и lot number являются переносимыми идентификаторами, но Central обязан иметь явную политику сопоставления каталога/партий и выявлять неоднозначность или конфликт expiry metadata.
- Локальная модель `Sale` требует локальный `cashier_user_id`; Edge contract намеренно не передаёт локальные числовые ID пользователей. Для Central reporting нужна отдельная source-aware sale projection либо отдельно утверждённое стабильное сопоставление actor identity. Нельзя создавать фиктивного локального кассира.
- Payment events необходимо сверять с Central sale/payment projection по receipt number, pharmacy scope и неизменяемой event identity. Нельзя считать клиентский статус платежа достаточным доказательством settlement от провайдера.

До реализации и сверки этих prerequisites Central Inbox должен оставаться в режиме durable-receipt-only. Не включать складские или финансовые side effects.

### 6. Классификация ошибок и quarantine

Повторять временные инфраструктурные ошибки (недоступность БД, deadlock, временный сбой зависимости) с ограниченным exponential backoff и jitter.

Постоянные ошибки помещать в quarantine: неподдерживаемая schema/event type, невозможный переход состояния, неизвестное/неоднозначное соответствие продукта или партии, pharmacy-scope mismatch, невозможный переход баланса и несовместимая версия агрегата. Отсутствующий predecessor — это version gap, а не poison event: событие остаётся ожидающим, при превышении операционного порога возраста gap создаётся alert.

Операторский replay обязан сохранять исходные неизменяемые `event_id` и payload. Исправления требуют compensating/new event или аудируемого изменения mapping; запрещено переписывать полученный payload события.

### 7. Эксплуатационные требования

Добавить метрики и alerts с низкой кардинальностью:

- количество событий в Inbox backlog и возраст самого старого accepted/retry;
- количество попыток, повторов, quarantine и постоянных ошибок;
- aggregate version gaps и возраст gap;
- processing latency и ошибки транзакций;
- конфликты movement idempotency и неизвестные catalog/lot mappings;
- задержка accepted-to-processed по каждой аптеке.

Предусмотреть операторский workflow для просмотра, исправления и replay quarantined events с RBAC и audit trail. Не выводить raw payload в обычные application logs или metrics.

## Рассмотренные альтернативы

- **Применять доменные эффекты в ingress request:** отклонено из-за зависимости API latency от доменных транзакций, сетевых повторов и риска частичных ошибок.
- **Использовать Redis/Celery как durable queue:** отклонено, поскольку PostgreSQL Inbox — durable receipt, а потеря Redis не должна приводить к потере событий.
- **Помечать событие processed до применения эффектов:** отклонено, поскольку crash приведёт к безвозвратной потере бизнес-эффекта.
- **Last-write-wins или пропуск aggregate versions:** отклонено, поскольку складские и платёжные факты должны быть аудируемыми.
- **Создавать отсутствующие продукты/партии из POS payload:** отклонено, поскольку событие продажи не является authoritative catalog или stock-receipt командой.

## Этапы реализации и критерии приёмки

1. Утвердить полный перечень Edge-to-Central событий, включая opening balance/snapshot и все операции, меняющие склад.
2. Определить Central product/lot mapping и source-aware sale/payment projection models.
3. Добавить processing metadata Inbox и aggregate checkpoint через additive migrations; перед этим проверить все Alembic heads.
4. Реализовать fenced ordered consumer и детерминированную event-to-movement idempotency mapping.
5. Добавить integration tests: duplicate delivery, concurrent workers, lease expiry/stale worker, out-of-order versions, recovery missing predecessor, unknown SKU/lot, cross-pharmacy mismatch, atomicity нескольких allocations, injected rollback и replay после commit.
6. Сверить Central inventory projections с Edge ledgers для контролируемой тестовой аптеки.
7. Завершить security, observability, backup/restore и failure-injection validation до pilot.

**Production status:** Не реализовано; Central Inbox остаётся receipt-only. Запрещено включать Central POS inventory/payment consumer до прохождения всех перечисленных gates.
