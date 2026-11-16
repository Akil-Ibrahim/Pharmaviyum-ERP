# Инженерная документация Pharmaviyum

[English](README.md) · **Русский**

Этот каталог — центральный индекс инженерной документации Pharmaviyum ERP/CRM. Здесь собраны архитектура, AI/RAG, разработка, эксплуатация, развёртывание и Pharmacy Edge.

## С чего начать

| Раздел | Русская версия | Английский оригинал | Содержание |
|---|---|---|---|
| Технологии | [Стек и глоссарий](./technology-stack.ru.md) | [Technology Stack & Glossary](./technology-stack.md) | Определения технологий, роли в архитектуре, версии и управление зависимостями |
| Структура репозитория | [Руководство](./architecture/repository-structure.ru.md) | [Repository Structure Guide](./architecture/repository-structure.md) | Назначение каталогов, правила размещения файлов и безопасные перемещения |
| Офлайн-операции | [Матрица возможностей](./devops/PHARMACY_OFFLINE_CAPABILITY_MATRIX.ru.md) | [Pharmacy Offline Capability Matrix](./devops/PHARMACY_OFFLINE_CAPABILITY_MATRIX.md) | Поддерживаемые, ограниченные, online-only и заблокированные сценарии |
| Оценка RAG | [Фармацевтическая оценка Ragas](./ai/ragas-pharmaceutical-evaluation.ru.md) | [Ragas evaluation](./ai/ragas-pharmaceutical-evaluation.md) | Offline-метрики RAG и специализированные фармацевтические проверки |
| Безопасность AI | [Выявление галлюцинаций и red-team](./ai/hallucination-detection-and-red-team.ru.md) | [Hallucination detection and red-team](./ai/hallucination-detection-and-red-team.md) | Оценка groundedness, adversarial-тестирование и правила безопасного отказа |
| Аптечные процессы | [Спецификация аптечного процесса](./workflows/pharmacy-workflow.ru.md) | [Pharmacy workflow specification](./workflows/pharmacy-workflow.en.md) | POS, отпуск, склад, закупки, аудит и offline-границы |
| Архитектура системы | [Архитектурное видение](./architecture/pharmaviyum-architecture.ru.md) · [Системный контекст](./architecture/system-context.ru.md) · [Контракт событий синхронизации](./architecture/PHARMACY_SYNC_EVENT_CONTRACT_V1.ru.md) · [Аудит POS и каталога](./architecture/PHARMACY_POS_CATALOG_AUDIT.ru.md) | [Architecture vision](./architecture/pharmaviyum-architecture.en.md) · [Sync event contract](./architecture/PHARMACY_SYNC_EVENT_CONTRACT_V1.md) · [POS catalog audit](./architecture/PHARMACY_POS_CATALOG_AUDIT.md) | Компоненты, Central/Edge, синхронизация, POS и лекарственный каталог |
| Chunking | [Pipeline чанкинга](./ai/chunking-pipeline.ru.md) | [Chunking pipeline](./ai/chunking-pipeline.md) | Текущая реализация разбиения документов и целевая архитектура |



## Остальные разделы документации

| Раздел | Что содержит | Статус русской версии |
|---|---|---|
| Системный контекст | [Английский оригинал](./architecture/system-context.md) | Доступен только английский оригинал | Границы компонентов, владение данными и Central/Edge |
| ADR | [Индекс архитектурных решений](./adr/README.ru.md) · [ADR-0001](./adr/ADR-0001-websocket-gateway.ru.md) · [ADR-0002](./adr/ADR-0002-offline-first-central-edge.ru.md) · [ADR-0003](./adr/ADR-0003-patient-scoped-ai-state.ru.md) · [ADR-0005: цены и роли аптек](./adr/ADR-0005-tenant-scoped-pricing-and-pharmacy-rbac.ru.md) | [ADR index](./adr/README.md) | Архитектурные решения и история изменений | Решения, статусы и жизненный цикл архитектурных изменений |
| AI / LLM | [Демо QwenCloud](./ai/QWENCLOUD_DEMO.ru.md) · [Архитектура Mortarium и глоссарий](./ai/MORTARIUM_AI_ARCHITECTURE.ru.md) · [Проектирование AI-системы](./ai/AI_LLM_SYSTEM_DESIGN.ru.md) · [Архитектура AI](./ai_architecture.ru.md) · [Аудит архитектуры RAG](./rag_architecture_audit.ru.md) · [Стандарт инженерии LLM](./llm_engineering_standards.ru.md) · [Архитектура LangGraph RAG](./ai/langgraph-rag-architecture.ru.md) · [Операционная работа Mortarium](./ai/mortarium-pharmacy-operations.ru.md) · [Изоляция состояния пациента](./ai/patient-session-isolation.ru.md) | [English originals](./README.md) | Mortarium, Agent Harness, LangGraph, RAG, MCP, безопасность и наблюдаемость |
| Разработка | [Руководство по разработке и тестированию](./guides/DEVELOPMENT_AND_TESTING.ru.md) · [Настройка окружения](./guides/ENVIRONMENT_SETUP.ru.md) · [GitHub Codespaces](./guides/CODESPACES_GUIDE.ru.md) | [Development and testing handbook](./guides/DEVELOPMENT_AND_TESTING.md) | Локальная среда, Codespaces, quality gates и контроль PR |
| Тестирование | [Руководство по тестированию](./guides/TESTING.ru.md) | [Testing guide](./guides/TESTING.md) | Структура тестов, маркеры pytest, CI и критерии качества |
| Эксплуатация | [Production operations](./operations/PRODUCTION_OPERATIONS_RUNBOOK.ru.md) · [Production Engineering](./operations/PRODUCTION_ENGINEERING.ru.md) · [Реагирование на инциденты](./operations/INCIDENT_RUNBOOK.ru.md) · [Релиз](./operations/RELEASE_RUNBOOK.ru.md) | [English originals](./README.md) | Health checks, SLO, инциденты, backup/restore и rollback |
| Развёртывание | [FastAPI Cloud](./deployment/FASTAPI_CLOUD.ru.md) · [Настройка окружения](./guides/ENVIRONMENT_SETUP.ru.md) | [FastAPI Cloud deployment](./deployment/FASTAPI_CLOUD.md) · [Environment setup](./guides/ENVIRONMENT_SETUP.md) | Hosted deployment, secrets, runtime и ручной release |
| DevOps и Pharmacy Edge | [Инженерные benchmarks](./devops/ENGINEERING_BENCHMARK_REQUIREMENTS.ru.md) · [Контракт benchmarks](./devops/ENGINEERING_BENCHMARK_REQUIREMENTS.md) · [Индекс DevOps](./devops/README.ru.md) · [Roadmap](./devops/ENGINEERING_ROADMAP.ru.md) · [Руководство Ansible](./devops/ANSIBLE_PHARMACY_EDGE_GUIDE.ru.md) · [План внедрения](./devops/PHARMACY_EDGE_ANSIBLE_ROLLOUT.ru.md) | [Ansible guide](./devops/ANSIBLE_PHARMACY_EDGE_GUIDE.md) · [Fleet rollout plan](./devops/PHARMACY_EDGE_ANSIBLE_ROLLOUT.md) | Benchmarks, rollout, Ansible, нагрузочные испытания, backup и recovery |
| Наблюдаемость | [OpenTelemetry](./observability/opentelemetry.ru.md) | [English original](./observability/opentelemetry.md) | Tracing, защита данных и критерии приёмки telemetry |
| WebSocket | [Протокол WebSocket](./websocket-protocol.ru.md) | [WebSocket protocol](./websocket-protocol.md) | Контракт и ограничения текущей реализации |
| Материалы для интервью | [Английский оригинал](./interview/README.md) | Доступен только английский оригинал | Python, system design и инженерные вопросы |

## Карта каталогов

- `workflows/` — аптечные бизнес-процессы и операционная модель.
- `architecture/` — системный контекст, границы компонентов и структура репозитория.
- `adr/` — долгосрочные архитектурные решения.
- `ai/` — Mortarium, LangGraph RAG, оценка и AI system design.
- `guides/` — настройка разработки и тестирование.
- `operations/` — инциденты, production operations и release.
- `devops/` — roadmap, benchmarks, load tests, observability и Pharmacy Edge.
- `deployment/` — инструкции по платформам размещения.
- `observability/` — telemetry и контроль конфиденциальности.
- `interview/` — учебные материалы и подготовка к интервью.

## Правила ведения документации

- Документируйте фактическое состояние репозитория, а не историческую или предполагаемую инфраструктуру.
- Для каждого процесса поддерживайте один канонический документ; в других местах размещайте ссылки на него.
- Архитектурные решения храните в `adr/`, эксплуатационные процедуры — в `operations/`, инструкции разработчика — в `guides/`, планы и benchmarks — в `devops/`.
- Помечайте возможности как реализованные, предлагаемые, запланированные или не прошедшие проверку. Статус Accepted у ADR не доказывает готовность реализации или Production.
- При изменении команд, сервисов, путей, API-контрактов или архитектурных инвариантов обновляйте соответствующую документацию в том же изменении.
- Не размещайте credentials, реальные данные клиентов/пациентов, секреты провайдеров или неотредактированные логи.
- Используйте синтетические примеры. Клинические пороги оценки требуют проверки квалифицированными специалистами.
- В каждом production runbook указывайте окружение, предусловия, ответственного, способ проверки и границы rollback/recovery.

## Языковая навигация

Английские документы остаются каноническими для инженерной и эксплуатационной терминологии. Русские версии должны сохранять структуру, смысл, команды, кодовые примеры, таблицы и внутренние ссылки оригинала. Если перевод ещё не опубликован, это явно отмечается в индексе — ссылка на несуществующий файл не создаётся.
