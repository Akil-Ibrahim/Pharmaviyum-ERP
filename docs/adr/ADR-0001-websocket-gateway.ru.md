# ADR-0001: WebSocket Gateway

## Статус

Accepted — текущая реализация является development template и пока не соответствует полному production-контракту, описанному в этом ADR.

## Контекст

Pharmaviyum требуется обмен данными в реальном времени между клиентами, фармацевтами и менеджерами аптек для чатов, уведомлений и presence updates.

Сейчас приложение представляет собой модульный FastAPI monolith. WebSocket support должен оставаться внутри границ приложения, пока измеренный масштаб или эксплуатационные требования не обоснуют выделенный gateway.

## Решение

- Сохранять WebSocket handling внутри FastAPI application.
- Использовать namespace `/ws`.
- Версионировать протокол (`v1`), чтобы контракт клиента можно было развивать управляемо.
- По мере развития реализации разделять routing, connection management, authentication, schemas, channel naming и feature handlers.
- Включить heartbeat/ping-pong, логирование жизненного цикла соединения, authorization и message rate limiting как часть production-контракта.
- Использовать Redis-backed coordination/pub-sub только при необходимости горизонтального масштабирования WebSocket; не вводить отдельный сервис преждевременно.

## Текущий статус реализации

Текущий код в `src/pharmaviyum/api/websocket/` намеренно минимален:

- `router.py` подключает WebSocket handlers под `/ws`.
- `handlers/chat.py` сейчас предоставляет echo-style development endpoint `/ws/chat`.
- Текущий handler пока не реализует JWT authentication, role-based authorization, persistence, heartbeat или production connection controls, требуемые этим ADR.

Следовательно, ADR фиксирует архитектурное решение и целевой контракт; его нельзя считать доказательством реализации полноценной production WebSocket-функции.

## Последствия

- WebSocket functionality остаётся в существующей модели deployment приложения.
- Код можно развивать из текущего development template без преждевременного перехода к microservice.
- Версионированный протокол даёт frontend явную границу совместимости.
- Горизонтальное масштабирование позднее можно добавить через shared Redis coordination, если это подтвердит измеренная нагрузка.

## Рассмотренные альтернативы

1. **Несколько WebSocket endpoints для отдельных функций**
   - Не выбрано как основная архитектура из-за роста сложности routing и совместимости.
2. **Отдельный WebSocket microservice**
   - Не выбран при текущем масштабе: добавляет эксплуатационную сложность до появления подтверждённой необходимости.
3. **Polling через REST API**
   - Не выбран для сценариев, которым требуется двусторонняя связь с низкой задержкой.

## Ссылки

- `src/pharmaviyum/api/websocket/` — текущая реализация.
- [WebSocket protocol](../websocket-protocol.md) — текущая заметка о протоколе и дизайне.

**Автор:** Ibrahim Akil  
**Дата:** 2026-01-28
