# Протокол WebSocket (v1)

**Статус:** предлагаемый протокол приложения. Текущие handlers являются development scaffolds, а не production-реализацией.

## Пространство имён и текущие маршруты

Приложение подключает handlers под `/ws`. Текущие исходные файлы:
- `src/pharmaviyum/api/websocket/router.py`
- `src/pharmaviyum/api/websocket/handlers/chat.py`
- `src/pharmaviyum/api/websocket/handlers/notifications.py`

Development handlers принимают соединение и echo/acknowledge обычный текст. Они не реализуют приведённый ниже JSON envelope, JWT-аутентификацию, авторизацию аптеки, гарантированную доставку, heartbeat policy или production connection controls. Не используйте их для реального patient traffic или production traffic.

## Цели протокола

Контракт v1 предназначен для realtime chat, уведомлений в пределах аптеки и presence. Он должен обеспечивать явные protocol version и message type, корреляцию запросов, строгие payload schemas, аутентифицированную идентичность, авторизованное сервером членство в каналах, ограничение размера сообщений/частоты/параллельных соединений, предсказуемые ошибки и корректное закрытие соединения.

## Предлагаемый JSON envelope

```json
{
  "version": "v1",
  "type": "chat.message",
  "request_id": "opaque-client-generated-id",
  "payload": {}
}
```

- `version`: обязательная версия протокола.
- `type`: тип события с namespace, например `chat.message`, `notification.subscribe` или `presence.update`.
- `request_id`: непрозрачный correlation ID, не являющийся credential для авторизации.
- `payload`: объект конкретного события, проверяемый по серверной schema.

Payload schemas и ограничения должны быть реализованы и проверены contract tests до стабилизации протокола. Неизвестные версии/типы и некорректные payloads не должны попадать в business handlers.

## Предлагаемые типы серверных событий

| Тип | Назначение | Требование безопасности |
|---|---|---|
| `connection.ready` | Подтверждение аутентифицированного соединения и версии | Генерируется сервером |
| `chat.message` | Отправка сообщения чата | Проверка tenant, отправителя и получателя |
| `chat.message.ack` | Подтверждение принятого сообщения | Корреляция и durable ID, если есть persistence |
| `notification.subscribe` | Запрос подписки | Сервер авторизует каждый канал |
| `notification.event` | Доставка уведомления | Запрет broadcast между tenant |
| `presence.update` | Обновление статуса/присутствия | Ограничение ролью и аптекой |
| `protocol.error` | Сообщение об ошибке протокола | Без stack traces и secrets |

Эти имена задают терминологию проектирования, а не возможности текущего runtime.

## Аутентификация и авторизация

При production-подключении пользователь должен быть аутентифицирован до приёма application messages. Проверяйте активность пользователя, активное членство в аптеке, разрешения роли и доступ к ресурсу.

Не доверяйте pharmacy ID, role, channel name или recipient, переданным клиентом. Определяйте идентичность по аутентифицированному server-side principal. Опишите поведение при истечении/отзыве token для долгоживущих соединений. Избегайте долгоживущих bearer tokens в query strings.

## Валидация, ограничения и ошибки

Определите максимальный размер frame/payload, допустимые content types, rate limits на пользователя/tenant/соединение, максимальное количество одновременных соединений, idle timeout, heartbeat interval, backpressure и поведение при медленных consumers.

Предлагаемые error codes: `UNAUTHENTICATED`, `FORBIDDEN`, `UNSUPPORTED_VERSION`, `UNKNOWN_EVENT_TYPE`, `INVALID_PAYLOAD`, `RATE_LIMITED`, `MESSAGE_TOO_LARGE` и `TEMPORARILY_UNAVAILABLE`.

Ошибки должны содержать безопасное сообщение и `request_id`, если он доступен. Никогда не возвращайте текст исключения, SQL, credentials или данные пациента.

## Жизненный цикл и семантика доставки

Целевой lifecycle: connect → authenticate → negotiate version → authorize subscriptions → validate messages → enforce rate/backpressure → acknowledge accepted work → emit bounded telemetry → graceful close.

Если будет реализована гарантированная доставка, определите message IDs, deduplication, acknowledgement, retention и replay. Не обещайте exactly-once delivery. Там, где это уместно, предпочитайте at-least-once delivery с идемпотентными consumers.

## Масштабирование

На первом этапе оставьте gateway внутри FastAPI в соответствии с [ADR-0001](./adr/ADR-0001-websocket-gateway.ru.md). Добавляйте Redis pub/sub только при подтверждённой измерениями необходимости горизонтального масштабирования. Pub/sub не является durable queue; для гарантированной доставки уведомлений нужны persistence и replay semantics.

## Наблюдаемость и конфиденциальность

Записывайте количество соединений, категории закрытия, результаты rate limiting, тип события, latency обработки и ошибки доставки с ограниченной кардинальностью labels. Не записывайте тела сообщений, tokens, идентификаторы пациентов или полные списки участников каналов.

## Чек-лист готовности к production

- [ ] Аутентификация до приёма application messages.
- [ ] Tenant- и role-авторизация для каждого канала/действия.
- [ ] Авторизация доступа к ресурсам там, где применимо.
- [ ] Строгие versioned schemas и contract tests.
- [ ] Ограничения frame, rate limits и quotas соединений.
- [ ] Heartbeat, idle timeout и graceful shutdown.
- [ ] Backpressure и политика slow consumers.
- [ ] Документированная семантика durable delivery, если она требуется.
- [ ] Проверка поведения между экземплярами при горизонтальном масштабировании.
- [ ] Privacy-reviewed telemetry и security tests.

Пока эти условия не выполнены, `/ws/chat` и `/ws/notifications` остаются development-only scaffolding.

## Ссылки

- [ADR-0001: WebSocket Gateway](./adr/ADR-0001-websocket-gateway.ru.md)
- [Контекст системы](./architecture/system-context.ru.md)
- [Руководство по тестированию](./guides/TESTING.ru.md)