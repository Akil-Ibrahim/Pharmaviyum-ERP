# Контракт событий синхронизации аптек v1

**Статус:** частично реализовано; Production-приёмка не подтверждена.  
**Область:** доставка событий от Pharmacy Edge к Central.

В репозитории уже реализованы transactional POS outbox, Celery dispatcher, регистрация/отзыв Edge-узлов и durable receipt в Central Inbox. При этом **ещё не реализованы** Central domain-event consumer, применение складских/финансовых эффектов, восстановление пропущенных версий, операционные quarantine/DLQ-процессы и end-to-end reconciliation. Ниже текущее состояние отделено от целевого протокола.

## 1. Гарантии доставки

Протокол использует **at-least-once transport** и **effectively-once business effects**:

- Edge фиксирует бизнес-транзакцию и событие outbox в одной локальной транзакции PostgreSQL.
- Dispatcher может отправить событие повторно после timeout, перезапуска процесса или потери подтверждения.
- Central сохраняет событие в durable inbox с unique constraint на event_id.
- Сейчас Central подтверждает получение после commit inbox-записи. Статус `accepted` означает durable receipt, а не применение события domain handler.
- Повторная доставка возвращает исходное durable acknowledgement и не применяет бизнес-эффекты повторно.
- Redis/Valkey и очередь в памяти не являются источником истины.

Exactly-once доставка по сети не гарантируется.

## 2. Обязательная оболочка события (event envelope)

Таблица описывает **целевую** неизменяемую оболочку события. Текущая валидация payload v1 отклоняет неизвестные ключи, проверяет вложенную структуру объектов/списков и размер payload. При этом она **пока не проверяет** все примитивные типы, числовые диапазоны, формат денежных значений и доменные enum-значения. До внедрения Central consumer необходимо добавить строгие typed payload models и negative tests.

Текущий wire envelope v1 содержит: `event_id`, `edge_node_id`, `event_type`, `schema_version`, `aggregate_type`, `aggregate_id`, `aggregate_version`, `occurred_at` и `payload`. Central получает `pharmacy_id` из аутентифицированной регистрации Edge. Поля `recorded_at`, `correlation_id`, `causation_id` и `idempotency_key` сейчас не передаются.

Целевые поля оболочки:

| Поле | Тип | Контракт |
|---|---|---|
| event_id | UUID | Глобально уникален и неизменен при retry. |
| event_type | string | Пространство имён доменного события, например pos.sale.created. |
| schema_version | positive integer | Версия контракта payload. |
| pharmacy_id | stable ID | Область аптеки, назначенная Central; нельзя доверять непроверенному утверждению клиента. |
| edge_node_id | stable ID | Идентификатор зарегистрированной Edge-инсталляции, не hostname/IP. |
| aggregate_type | string | Тип доменного потока, например sale или inventory_item. |
| aggregate_id | string | Стабильный ID внутри области аптеки. |
| aggregate_version | positive integer | Строго возрастающая версия внутри aggregate stream. |
| occurred_at | UTC timestamp | Время бизнес-события со стороны Edge; информационное, не глобальный порядок. |
| recorded_at | UTC timestamp | Время сохранения в БД Edge. |
| correlation_id | UUID/string | Группирует события одного workflow. |
| causation_id | UUID/string или null | Событие/команда, непосредственно вызвавшие это событие. |
| idempotency_key | string | Стабильный ключ команды, если операция поддерживает защиту от повторов. |
| payload | object | Версионируемые факты конкретного события с минимизацией данных. |

Текущее состояние: outbox сохраняет event identity, pharmacy scope, event type/schema, aggregate identity/version, payload и timestamps. Dispatcher добавляет зарегистрированный `edge_node_id` в wire envelope. Correlation/causation metadata и command-level idempotency key пока не сохраняются. Целевые поля таблицы нельзя считать частью текущего v1 payload.

## 3. Идентификация и аутентификация

- Central отвечает за регистрацию аптек/сайтов и подключение Edge-узлов.
- Каждая Edge-инсталляция получает уникальную идентичность и собственный отзывной credential или сертификат.
- Сейчас каждый узел получает случайный высокоэнтропийный bearer credential; в БД сохраняется только его SHA-256 digest, credential можно отозвать. Dispatcher требует HTTPS и передаёт токен в заголовке `X-Edge-Token`.
- Пока не реализованы: mTLS, автоматическая ротация credentials/период перекрытия и управление жизненным циклом сертификатов.
- Разрешённую аптеку определяйте по аутентифицированной регистрации узла. Отклоняйте событие, если заявленный pharmacy_id не совпадает с регистрацией.
- Не помещайте общий статический секрет для всего парка в image, Ansible defaults или source control.
- Отозванный узел не может отправлять новые события. Ротация credentials и контроль периода перекрытия остаются требованиями Production hardening.
- Ansible безопасно устанавливает identity material; приложение проверяет его и авторизует события.

## 4. Порядок и обработка inbox

Dispatcher уже блокирует отправку более поздней неопубликованной версии, пока не подтверждена предыдущая версия того же aggregate. Central отклоняет повторную aggregate version, но пока не проверяет следующую ожидаемую версию и не запускает domain consumer. Следующие пункты описывают **целевую** обработку inbox, а не текущее поведение:

1. Central проверяет envelope, идентичность узла, pharmacy scope и поддерживаемую schema version.
2. Central вставляет исходное событие в durable inbox с уникальным event_id.
3. Если ID уже существует, Central возвращает сохранённое подтверждение без повторного применения.
4. Consumer проверяет следующую ожидаемую aggregate_version.
5. Если будущая версия пришла раньше предшественника, она сохраняется как pending и не применяется вне порядка.
6. Повторная версия с другим event ID — конфликт протокола; событие помещается в quarantine.
7. Domain handler применяет событие, а результат/checkpoint фиксируется атомарно с состоянием inbox.
8. Central подтверждает durable state; acknowledgement указывает accepted, pending, rejected или quarantined.

Не задавайте глобальный порядок между аптеками и не используйте клиентские часы для разрешения складских или финансовых конфликтов.

## 5. Dispatcher и retry

- Захватывайте подходящие outbox rows в короткой транзакции с PostgreSQL FOR UPDATE SKIP LOCKED.
- Используйте уникальный lease token и срок действия. Обновлять строку после доставки может только worker с актуальным token.
- Выполняйте HTTP/network I/O вне транзакции БД.
- Помечайте событие доставленным только после durable acknowledgement от Central.
- Текущая реализация повторяет HTTP errors и неуспешные HTTP responses с exponential backoff и jitter; экспоненциальная составляющая ограничена одним часом. Сюда входят и постоянные 4xx, поэтому ошибки credentials/schema/scope могут повторяться бесконечно.
- Пока не реализованы: классификация постоянных ошибок, dead-letter/quarantine workflow, endpoint операторского replay и alerting для poison events.
- Сохраняйте ошибки для проверки и контролируемого replay. Replay сохраняет исходный event_id.
- Отслеживайте возраст старейшего pending event, backlog, attempts, последнюю ошибку, последнюю успешную синхронизацию и задержку подтверждений по каждому сайту. Специализированные sync metrics и dashboards пока не реализованы.

## 6. Политика доменных конфликтов

Никогда не разрешайте конфликты остатков, продаж, платежей, отпуска лекарств или аудита через last-write-wins.

- Pharmacy Edge авторитетен для собственных зафиксированных локальных продаж и записей складского ledger.
- Central строит консолидированное eventually consistent представление из принятых событий.
- Изменения остатков — append-only ledger facts с уникальными operation ID; вычисленное количество не является перезаписываемым реплицируемым полем.
- Межаптечные перемещения требуют явных событий резервирования/отправки источником и приёмки получателем.
- Обновления каталога и политик Central — версионируемые команды/configuration snapshots с подтверждением применённой версии от каждого Edge.
- Устаревшая версия каталога/политики видна оператору и обрабатывается согласно настроенной политике ограничений.
- Нарушающие доменные инварианты события помещаются в quarantine; не меняйте остатки молча ради совпадения итогов.

## 7. Минимизация данных и приватность

- Не включайте имена, телефоны, адреса пациентов, полное содержимое рецептов и другие прямые идентификаторы в общую telemetry синхронизации.
- Предпочитайте opaque references и минимальные доменные факты, необходимые принимающему workflow.
- Синхронизация пациентов/рецептов требует отдельно утверждённого проекта авторизации, доступа, шифрования, хранения и аудита.
- Logs, traces, metrics и сообщения об ошибках не должны сериализовать payload с данными пациентов/рецептов.
- Схемы payload должны использовать allow-list и валидацию; неожиданные поля следует отклонять, где это возможно.

## 8. Совместимость и эволюция схемы

- Типы событий версионируются независимо от релизов приложения.
- Добавочные optional fields допустимы, только если старые consumers безопасно их игнорируют.
- Breaking changes требуют новой schema version и документированного окна совместимости.
- Central сообщает Edge-узлам поддерживаемые event types/schema versions.
- Edge не отправляет неподдерживаемую версию; события остаются локально до появления совместимого маршрута.
- Миграции БД выполняются по expand/contract. Не удаляйте старые columns/handlers, пока поддерживаемые версии Edge могут использовать старый контракт.

## 9. Обязательные failure tests до production

Проверьте: потерю WAN до/во время отправки и после Central commit, но до acknowledgement; перезапуск Edge с pending/leased events; перезапуск Central после inbox insert, но до domain application; duplicate delivery и event ID с изменённым payload; duplicate aggregate version; out-of-order versions и восстановление предшественника; истечение lease и stale worker acknowledgement; истечение/ротацию/отзыв credentials и подделку pharmacy scope; неподдерживаемую schema version и malformed payload; переполнение диска/недоступность БД Edge; replay после исправления оператором без повторных бизнес-эффектов; длительное отключение и последующий catch-up backlog без вытеснения live traffic.

## 10. Условия допуска к реализации

Не включайте production dispatcher, пока не выполнены все условия:

1. Реализованы зарегистрированная Edge identity и индивидуальная аутентификация каждого узла.
2. Схемы envelope/payload валидируются и версионируются.
3. Central inbox обеспечивает durable deduplication, ordering и quarantine.
4. Domain handlers идемпотентны и используют ledger semantics для склада/финансов.
5. Lease, retries, acknowledgements и replay dispatcher протестированы.
6. Матрица offline-возможностей утверждена для юрисдикции и deployment providers.
7. Observability, backup/restore и failure-injection tests проходят в лабораторном окружении.
