# OpenTelemetry

## Единый владелец провайдера

Единственным владельцем OpenTelemetry SDK provider на уровне всего процесса является модуль
`src/pharmaviyum/observability/opentelemetry.py`. Приложение FastAPI настраивает его один раз из `main.py` во время запуска lifespan и выполняет flush/shutdown при завершении lifespan. `src/pharmaviyum/core/telemetry.py` — только facade для обратной совместимости: он делегирует вызовы каноническому модулю и никогда не должен создавать или регистрировать provider. Устаревшая точка входа `core.lifecycle` использует тот же facade. Конфигурация берётся из `AISettings.otel` в `src/pharmaviyum/ai/config.py`; дублирующие поля OpenTelemetry удалены из `core.config.Settings`. Старое имя переменной окружения `OTEL_TRACES_SAMPLE_RATE` по-прежнему принимается как alias для `OTEL_SAMPLE_RATE`.

Завершение работы provider идемпотентно. Поскольку глобальный OpenTelemetry provider нельзя безопасно заменить в том же процессе, ссылка на закрытый provider сохраняется, а после shutdown второй provider не создаётся.

Pharmaviyum использует OpenTelemetry SDK для распределённой трассировки. Application spans AI/RAG/MCP используют проверенные атрибуты с ограниченным набором значений. Автоматическая instrumentation FastAPI requests, SQLAlchemy и HTTPX по умолчанию отключена и может быть включена только в development/test после проверки редактирования URL, SQL и данных запросов. Автоматическая instrumentation команд Redis остаётся отключённой. Передача trace context использует стандартные заголовки W3C Trace Context (`traceparent` и `tracestate`).

## Конфигурация

Трассировка по умолчанию отключена, чтобы не создавать накладные расходы instrumentation, если backend трассировки не настроен. Включайте её явно вместе с OTLP endpoint.

| Переменная | По умолчанию | Назначение |
| --- | --- | --- |
| `OTEL_ENABLED` | `false` | Включение/отключение SDK и instrumentation |
| `OTEL_SERVICE_NAME` | `pharmaviyum-ai` | Идентификатор сервиса в trace backend |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | не задан | Стандартный endpoint OTLP/gRPC collector |
| `OTEL_EXPORTER_ENDPOINT` | не задан | Переменная endpoint для обратной совместимости |
| `OTEL_SAMPLE_RATE` | `0.1` | Доля sampling корневых traces, от 0.0 до 1.0 |
| `OTEL_INCLUDE_FASTAPI_REQUEST_SPANS` | `false` | Opt-in автоматических FastAPI request spans только для development/test |
| `OTEL_INCLUDE_SENSITIVE_CLIENT_SPANS` | `false` | Opt-in автоматических SQLAlchemy и HTTPX spans только для development/test |

Укажите один endpoint в приложении FastAPI Cloud, например:

```dotenv
OTEL_ENABLED=true
OTEL_SERVICE_NAME=pharmaviyum-api
OTEL_EXPORTER_OTLP_ENDPOINT=https://your-otlp-collector.example.com:4317
OTEL_SAMPLE_RATE=0.1
```

Локальный Docker Compose stack запускает OTLP Collector и Jaeger. После `docker compose up` откройте `http://localhost:16686`, чтобы просматривать traces. Collector передаёт traces в Jaeger по OTLP/gRPC. Для локального collector без TLS используйте endpoint с `http://`. Заголовки аутентификации OTLP exporter можно передать через стандартную переменную окружения `OTEL_EXPORTER_OTLP_HEADERS`. Никогда не коммитьте токены collector или credentials в репозиторий.

Если tracing включён без endpoint, spans создаются внутри процесса, но не экспортируются. Приложение записывает warning; API остаётся доступным. Если exporter не удаётся инициализировать, настройка наблюдаемости не должна быть критичной и не должна препятствовать запуску аптечного API.

## Границы instrumentation

- Автоматические FastAPI request spans по умолчанию отключены. Opt-in `OTEL_INCLUDE_FASTAPI_REQUEST_SPANS` принимается только в development и test; перед включением убедитесь, что URL paths и headers не раскрывают идентификаторы пациента или tenant.
- Автоматическая instrumentation SQLAlchemy и HTTPX по умолчанию отключена. Opt-in `OTEL_INCLUDE_SENSITIVE_CLIENT_SPANS` принимается только в development и test; не включайте её в production или при работе с данными, содержащими PHI.
- Автоматическая instrumentation команд Redis всегда отключена. Аргументы команд могут содержать prompts, содержимое памяти и клинические payload. Используйте только ограниченные application-level operation metrics/spans, которые не содержат Redis keys, values или аргументы команд.
- Retrieval Mortarium RAG и выполнение MCP-инструментов — с ограниченными атрибутами для количества источников, количества предупреждений, имён инструментов и состояния успеха.
- Маршрутизация моделей Mortarium и выполнение агента — без записи prompts, данных пациентов, аргументов инструментов или извлечённого клинического текста.

SDK использует parent-based ratio sampler. Дочерние spans следуют sampled state родительского span. Единственный provider выполняет flush и shutdown при завершении lifespan приложения; повторные вызовы shutdown безопасны и не регистрируют новый provider.

## Критерии приёмки наблюдаемости

Instrumentation нельзя считать завершённой только потому, что SDK инициализируется. Проверьте критический путь запроса end-to-end и зафиксируйте:

- покрытие traces для определённых FastAPI, database, Redis, Celery и Mortarium workflows;
- передачу W3C trace context через границы процессов/сервисов;
- связи parent/child spans и статус ошибок;
- ошибки доставки exporter/collector и потерянную телеметрию;
- корреляцию логов и traces;
- покрытие метриками API, data services, workers, RAG, model calls и MCP tools;
- оценку alert rules и доставку уведомлений в контролируемом тесте.

Измеряйте p50/p95/p99 для определённых этапов API и AI workflow. Сохраняйте ограниченную кардинальность metric labels; не используйте идентификаторы аптеки, пользователя, пациента, сессии, prompt или raw URL в качестве Prometheus labels. Полные определения метрик и требования к benchmark evidence приведены в [требованиях к инженерным benchmark](../devops/ENGINEERING_BENCHMARK_REQUIREMENTS.md).

## Защита данных

Не добавляйте имена и идентификаторы пациентов, содержимое рецептов, access tokens, API keys, строки подключения к БД, исходные prompts или извлечённый клинический текст в атрибуты или события spans. Не включайте автоматическую request/client instrumentation в production; предпочитайте явные application spans с allowlisted attributes вместо raw URLs, SQL statements, headers или request bodies. До включения экспорта в production примените политики retention, контроля доступа и регионального хранения данных для collector.
