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
| Архитектура системы | [Архитектурное видение](./architecture/pharmaviyum-architecture.ru.md) | [Architecture vision](./architecture/pharmaviyum-architecture.en.md) | Компоненты, границы доверия, владение данными и Central/Edge |
| Chunking | [Pipeline чанкинга](./ai/chunking-pipeline.ru.md) | [Chunking pipeline](./ai/chunking-pipeline.md) | Текущая реализация разбиения документов и целевая архитектура |



## Остальные разделы документации

| Раздел | Что содержит | Статус русской версии |
|---|---|---|
| Системный контекст | Границы компонентов, владение данными и Central/Edge | Перевод готовится |
| ADR | [Индекс архитектурных решений](./adr/README.ru.md) | [ADR index](./adr/README.md) | Решения, статусы и жизненный цикл архитектурных изменений |
| AI / LLM | [Архитектура Mortarium и глоссарий](./ai/MORTARIUM_AI_ARCHITECTURE.ru.md) · [Проектирование AI-системы](./ai/AI_LLM_SYSTEM_DESIGN.ru.md) · [Архитектура LangGraph RAG](./ai/langgraph-rag-architecture.ru.md) · [Операционная работа Mortarium](./ai/mortarium-pharmacy-operations.ru.md) · [Изоляция состояния пациента](./ai/patient-session-isolation.ru.md) | [English originals](./README.md) | Mortarium, Agent Harness, LangGraph, RAG, MCP, безопасность и наблюдаемость |
| Разработка | Настройка окружения, рабочий процесс и quality gates | Перевод готовится |
| Тестирование | Структура тестов, markers и CI | Перевод готовится |
| Эксплуатация | Проверки работоспособности, инциденты, backup и recovery | Перевод готовится |
| Развёртывание | FastAPI Cloud, секреты, runtime и контролируемый release | Перевод готовится |
| DevOps и Pharmacy Edge | Roadmap, Ansible, нагрузочные испытания, резервное копирование и rollout | Перевод готовится |
| Наблюдаемость | OpenTelemetry, tracing и защита данных | Перевод готовится |
| WebSocket | Протокол и ограничения текущей реализации | Перевод готовится |
| Материалы для интервью | Python, system design и инженерные вопросы | Перевод готовится |

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
