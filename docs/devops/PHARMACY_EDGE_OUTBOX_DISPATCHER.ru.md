# Dispatcher Outbox для Pharmacy Edge

## Назначение

Dispatcher доставляет зафиксированные локальные записи `outbox_events` в Central Inbox. PostgreSQL является durable source of truth. Redis/Celery используется только для расписания и выполнения задач; потеря или очистка Redis не должна удалять бизнес-события.

## Конфигурация каждого Edge-узла

| Переменная | Назначение |
|---|---|
| `PHARMAVIYUM_EDGE_NODE_ID` | UUID, полученный при регистрации Edge-инсталляции в Central |
| `PHARMAVIYUM_EDGE_TOKEN` | Bearer credential, выданный конкретному Edge-узлу один раз |
| `PHARMAVIYUM_CENTRAL_SYNC_URL` | HTTPS base URL Central API |
| `PHARMAVIYUM_SYNC_BATCH_SIZE` | Максимум строк за один проход (по умолчанию 50, жёсткий предел 500) |
| `PHARMAVIYUM_SYNC_LEASE_SECONDS` | Длительность lease (по умолчанию 30 секунд; минимум 15) |
| `PHARMAVIYUM_SYNC_HTTP_TIMEOUT_SECONDS` | Timeout запроса к Central (по умолчанию 10 секунд) |

Храните token в Ansible Vault или secret store платформы. Не коммитьте его в Git, не встраивайте в image, URL или frontend. Node ID и token должны использоваться только на соответствующей аптечной Edge-инсталляции. API должен быть доступен по HTTPS/TLS. mTLS и автоматическая ротация credentials остаются обязательным hardening до широкого fleet rollout.

Если отсутствует любая из трёх обязательных переменных Edge identity, dispatcher безопасно не выполняет доставку. Central-only installation не должна получать Edge credentials.

Ansible app-backend role развёртывает API, Celery worker и один Beat scheduler вместе. Secret-bearing `.env` создаётся с mode 0600, вывод задачи подавляется. Deploy validation требует передавать три Edge identity values совместно и использовать HTTPS Central URL.

## Протокол доставки

1. POS-транзакция фиксирует бизнес-строки и outbox event в одной транзакции PostgreSQL.
2. Celery Beat ставит bounded dispatcher pass в очередь каждые пять секунд. На одной Edge-инсталляции должен работать один Beat scheduler.
3. Dispatcher захватывает подходящие строки в короткой транзакции через `FOR UPDATE SKIP LOCKED`.
4. Каждому claim назначается уникальный lease fencing token и срок действия. Счётчик попыток увеличивается до сетевого вызова.
5. HTTP-запрос выполняется вне транзакции БД и содержит immutable `event_id`, `edge_node_id`, aggregate identity/version и payload. Central определяет authoritative pharmacy scope по аутентифицированной Edge registration; Edge не передаёт доверенный `pharmacy_id`.
   - POS product references используют общий product SKU и lot number; локальные integer primary keys продуктов/остатков не передаются, поскольку они не переносимы между независимыми Edge DB.
   - Central должен разрешить SKU в каноническом каталоге аптеки и помещать неизвестные или неоднозначные mappings в quarantine.
   - Sale aggregate ID — неизменяемый receipt number, а не локальный auto-increment sale ID. Локальные numeric IDs кассира и payment rows не передаются.
6. Только совпадающий Central acknowledgement со статусом `accepted` позволяет dispatcher установить `published_at`.
7. Timeout или ошибка освобождает принадлежащий worker lease и планирует exponential backoff с jitter. Событие остаётся durable и не удаляется молча.

**Важно:** Central acknowledgement означает durable receipt в inbox, а не применение inventory или других domain effects.

## Порядок и конкурентность

Dispatcher не захватывает более позднюю неопубликованную версию, пока более ранняя версия того же `(pharmacy_id, aggregate_type, aggregate_id)` остаётся неопубликованной. Разные aggregates могут обрабатываться параллельно. `SKIP LOCKED` позволяет нескольким worker processes захватывать непересекающиеся строки.

Lease token служит fencing token: worker, чей lease заменён, не может отметить событие опубликованным или изменить lease нового worker. Если Central сохранил событие, но HTTP acknowledgement потерялся, тот же `event_id` отправляется повторно; Central Inbox дедуплицирует повторную доставку.

Более раннее событие, которое отклонено или постоянно не доставляется, намеренно блокирует более поздние версии этого aggregate. Оператор должен устранить причину. Нельзя пропускать версии или переписывать payload уже созданного события.

## Валидация payload

Текущая схема v1 использует строгие вложенные Pydantic-модели: неизвестные поля запрещены; количество — strict integer и положительное; денежные значения — строки с двумя десятичными знаками; проверяются арифметика строки/чека, равенство сумм распределения по партиям количеству товара и согласованность payment/inventory state. Есть unit tests на ошибочные типы, значения, неизвестные поля и арифметические расхождения. Эти проверки подтверждают форму события, но не заменяют доменную валидацию Central Consumer.

## Ограничения текущей реализации и критерии rollout

- Dispatcher транспортирует только POS event types, которые создаёт текущий producer. Central ordered consumer и применение inventory, payment, dispensing, returns или purchasing effects пока не реализованы.
- Отдельный management UI пока отсутствует. Superuser-only API endpoints показывают метаданные dead-letter без раскрытия event payload и поддерживают audited replay после устранения причины.
- Transport failures, HTTP 408/425/429 и 5xx повторяются с backoff. Остальные 4xx, redirects и malformed acknowledgements помещаются в durable quarantine; они не создают бесконечный retry loop.
- Quarantined events остаются immutable и блокируют более поздние aggregate versions. Replay сохраняет исходные event ID, payload и aggregate version; каждый replay создаёт durable audit record.
- mTLS, автоматическая ротация credentials и per-pharmacy monitoring dashboards остаются незавершёнными.
- Worker и Beat containers должны использовать ту же локальную PostgreSQL DB, что и POS API, и получать ту же Edge identity configuration.
- До пилота необходимо протестировать Central unavailability, lost acknowledgements, worker termination after claim, lease expiry, duplicate deliveries, aggregate ordering и full-disk conditions.
- Не включайте production migrations или fleet dispatch, пока stacked PRs не прошли CI, Central consumer и inventory conflict policy не реализованы, а controlled pilot не прошёл failure-injection tests.

## Статус гарантии

Текущий протокол обеспечивает durable outbox, повторную доставку и дедупликацию при durable Central Inbox receipt. Он **не обеспечивает** exactly-once network delivery, применение доменных изменений в Central, conflict-free inventory replication или production-grade disaster recovery.
