# Инженерная документация Pharmaviyum

[English](README.md) · **Русский**

Этот каталог — центральный индекс инженерной документации Pharmaviyum ERP/CRM.

## С чего начать

| Раздел | Русская версия | Английский оригинал | Содержание |
|---|---|---|---|
| Технологии | [Стек и глоссарий](./technology-stack.ru.md) | [Technology Stack](./technology-stack.md) | Роли технологий, версии и управление зависимостями |
| Архитектура системы | [Архитектурное видение](./architecture/pharmaviyum-architecture.ru.md) · [Системный контекст](./architecture/system-context.ru.md) | [Architecture vision](./architecture/pharmaviyum-architecture.en.md) · [System context](./architecture/system-context.md) | Компоненты, границы и владение данными |
| AI / LLM | [Проектирование AI](./ai/AI_LLM_SYSTEM_DESIGN.ru.md) · [Архитектура Mortarium](./ai/MORTARIUM_AI_ARCHITECTURE.ru.md) | [AI system design](./ai/AI_LLM_SYSTEM_DESIGN.md) · [Mortarium glossary](./ai/MORTARIUM_AI_ARCHITECTURE.md) | Mortarium, LangGraph, RAG, MCP, безопасность и оценка |
| Международный каталог | [Источники и план импорта](./catalog/INTERNATIONAL_CATALOG_SOURCES.ru.md) | [Source coverage and import plan](./catalog/INTERNATIONAL_CATALOG_SOURCES.md) | Официальные источники лекарств/изделий, provenance и rollout |
| ADR | [Индекс ADR](./adr/README.ru.md) · [ADR-0008](./adr/ADR-0008-international-medicine-and-device-reference-catalog.ru.md) | [ADR index](./adr/README.md) · [ADR-0008](./adr/ADR-0008-international-medicine-and-device-reference-catalog.md) | Архитектурные решения и их статусы |
| Разработка | [Разработка и тестирование](./guides/DEVELOPMENT_AND_TESTING.ru.md) | [Development and testing](./guides/DEVELOPMENT_AND_TESTING.md) | Рабочий процесс и quality gates |
| Эксплуатация | [Эксплуатация Production](./operations/PRODUCTION_OPERATIONS_RUNBOOK.ru.md) | [Production operations](./operations/PRODUCTION_OPERATIONS_RUNBOOK.md) | Health, инциденты, backup и recovery |
| Развёртывание | [FastAPI Cloud](./deployment/FASTAPI_CLOUD.ru.md) | [FastAPI Cloud](./deployment/FASTAPI_CLOUD.md) | Хостинг, secrets и release |
| Наблюдаемость | [OpenTelemetry](./observability/opentelemetry.ru.md) | [OpenTelemetry](./observability/opentelemetry.md) | Tracing и конфиденциальность |

## Карта каталогов

- workflows/ — аптечные процессы.
- architecture/ — системный контекст и границы компонентов.
- adr/ — долгосрочные архитектурные решения.
- catalog/ — международные источники лекарств/изделий, provenance и план импорта.
- ai/ — Mortarium, LangGraph RAG и оценка.
- guides/ — настройка разработки и тестирование.
- operations/ — инциденты, production и release.
- deployment/ — инструкции размещения.
- observability/ — telemetry и конфиденциальность.

## Правила ведения документации

- Документируйте фактическое состояние репозитория.
- Для каждого процесса поддерживайте один канонический документ.
- Архитектурные решения храните в adr/, эксплуатационные процедуры — в operations/, инструкции — в guides/.
- Помечайте возможности как реализованные, предлагаемые, запланированные или непроверенные. Accepted ADR не доказывает production readiness.
- Обновляйте документацию при изменении команд, сервисов, путей, API-контрактов и архитектурных инвариантов.
- Не размещайте credentials, реальные данные пациентов/клиентов, секреты и неотредактированные логи.
- Используйте синтетические примеры. Клинические пороги требуют профессиональной проверки.
- Production runbook должен указывать окружение, предусловия, ответственного, проверку и recovery boundary.
