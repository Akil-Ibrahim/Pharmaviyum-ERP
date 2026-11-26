# Аудит архитектуры Mortarium AI / RAG

**Дата аудита:** 2026-11-19  
**Проверенная ревизия:** `main` на коммите `cec7ba8ad4fa8bc40cc0b3f870a17509ca4e2743`  
**Метод:** статическая проверка исходного кода, конфигурации, документации и контрактов тестирования  
**Статус выполнения:** в рамках этого аудита документации не запускались тесты приложения, live-вызовы моделей, production-запросы или изменения deployment.

## Итоговая оценка

Mortarium — прикладной помощник фармацевта, построенный на двух workflow LangGraph: агенте фармацевта и отдельном RAG-графе LangGraph. Runtime также включает Agent Harness, память диалога и prompt cache в Redis, retrieval на PostgreSQL/pgvector, ingestion документов через Celery, MCP-инструменты с фильтрацией по ролям, медицинские guardrails и instrumentation OpenTelemetry.

В архитектуре есть существенные fail-closed механизмы: аутентифицированный контекст аптеки устанавливается на границе API; ID пациента проверяются относительно выбранной аптеки; pgvector retrieval требует положительный pharmacy ID; для чанков уровня пациента обязателен явный patient filter; выполнение MCP требует доверенного контекста запроса и RBAC; операции записи MCP запрещены, если не настроен доверенный verifier подтверждения.

**Первоначальная P0-проблема изоляции контекста пациента устранена в `main` через PR #287** (merge commit `4d761990b31ef3aa78327dda1380689f2d094e8f`). Synchronous и streaming API теперь формируют версионируемый HMAC namespace `mortarium-session:v4` на основе pharmacy, аутентифицированного user, patient (включая явную область без пациента) и client session. Agent и RAG checkpoints независимо формируют непрозрачные версионируемые HMAC identifiers с учетом patient scope. Regression tests покрывают разделение областей, неверные идентификаторы, tenant isolation и secret rotation. В merge record проверки RAG Safety Regression, Unit Tests и Integration Tests указаны как успешные.

**Production readiness пока не доказана.** Остаётся staged end-to-end release gate: переключение Patient A → Patient B → no patient с повторным использованием одной client session в streaming и non-streaming режимах, с реальной Redis memory и PostgreSQL checkpoint persistence. Старые plaintext RAG checkpoint records автоматически не мигрируются и не удаляются; до rollout необходимо утвердить retention/deletion plan и rollback behavior. Этот статический обзор не запускал тесты и не проверял production state.

Другие существенные пробелы остаются: качество русского языка/OCR/embeddings требует измеримых RU/EN benchmarks; runtime не внедряет отдельный reranker; некоторые объявленные настройки RAG не подключены к runtime; отдельный `IngestionOrchestrator` не является активным путём ingestion API.

## Карта runtime

| Уровень | Текущая реализация | Оценка аудита |
|---|---|---|
| Граница API | `src/pharmaviyum/api/v1/ai.py`; аутентифицированный пользователь, членство в аптеке и проверка принадлежности пациента аптеке | Patient-aware HMAC session scope влит; staged integration gate открыт |
| Оркестрация агента | Граф LangGraph `PharmacistAgent`: router → извлечение знаний → цикл planner/executor → структурированный reviewer | Реализовано; лимит итераций — 5 |
| Agent Harness | `AgentHarness`: memory → input guardrail → cache → model router → agent → output guardrail → memory | Реализовано |
| Оркестрация RAG | Скомпилированный `StateGraph` `LangGraphRAG` с явным PostgreSQL checkpointer | Реализовано |
| Retrieval | Векторный поиск PostgreSQL/pgvector + полнотекстовый поиск PostgreSQL + reciprocal-rank fusion | Реализовано; необязательный reranker не подключён |
| Ingestion | API отправляет авторизованные для tenant задачи Celery; worker загружает, обрабатывает, проставляет tenant metadata, разбивает на чанки, создаёт embeddings и сохраняет | Активный API-путь реализован |
| Операционные инструменты | Единый внутренний MCP registry/server с фильтрацией по ролям и доверенным контекстом запроса | Реализовано; текущие инструменты аптечных операций доступны только для чтения |
| Оценка | Проектные retrieval-метрики, фармацевтические evaluators, ленивый адаптер Ragas 0.4.3 | Offline-фреймворк реализован; измеренное клиническое качество не установлено |
| Наблюдаемость | Метрики Prometheus и ограниченные spans OpenTelemetry | Instrumentation существует; сквозное покрытие production не подтверждено |

## Выводы и приоритеты

### P0 — Изоляция контекста пациента: исправление кода влито; staged release gate открыт

PR #287 добавил в `main` следующие механизмы:

- API session namespace `mortarium-session:v4` связывает pharmacy, аутентифицированного user, patient (включая явный `None`) и client session с помощью HMAC-SHA-256.
- Оба endpoint — synchronous и streaming — проверяют tenant/patient scope до формирования внутреннего session namespace.
- `PharmacistAgent._thread_id()` использует `agent:v2:<digest>` и учитывает patient scope.
- `LangGraphRAG._thread_id()` использует `rag:v2:<digest>` и учитывает patient scope.
- Прямое создание checkpoint проверяет формат идентификаторов и завершает запрос fail-closed в staging/production при отсутствии `SECRET_KEY`.
- Regression tests проверяют разделение Patient A/B/no-patient, некорректные идентификаторы, tenant isolation и secret rotation.

**Оставшийся release gate:** провести staged end-to-end тесты с реальными Redis и PostgreSQL checkpoint persistence, повторно используя одну client session для Patient A → Patient B → no patient в streaming и non-streaming режимах. Проверить memory, summaries, checkpoints и cache behavior. Этот статический аудит не утверждает, что staged-проверка выполнена или production активирован. См. [ADR-0003](./adr/ADR-0003-patient-scoped-ai-state.ru.md) и [контракт изоляции patient session](./ai/patient-session-isolation.md).

### P1 — Псевдонимизация RAG checkpoint: исправление кода влито; retention старых записей открыт

PR #287 заменил plaintext composite RAG checkpoint identifier на `rag:v2:<HMAC-SHA256 digest>`, ограниченный pharmacy, user, patient и session. В production/staging отсутствие `SECRET_KEY` также приводит к fail-closed. Это закрывает code-level finding в `main`.

**Оставшаяся операционная работа:** старые plaintext checkpoint rows автоматически не переписываются и не удаляются. Необходимо утвердить retention/deletion и backup-expiry policy, подтвердить стабильное распространение/ротацию secret и проверить rollback до production rollout. Удаление checkpoint data не входит в этот документационный change.

### P1 — Русский язык не включён в текущую конфигурацию языков по умолчанию

Evaluation helper поддерживает отдельные retrieval-оценки `ru` и `en`, однако текущие defaults не подтверждают поддержку русского языка:

- `RAGSettings.default_languages`: `vi, en, ar, th, id`;
- defaults loader/task ingestion: `vi, en, ar, th, id`;
- core `SUPPORTED_LANGUAGES`: `vi, en, zh, ko, ms, id, th`;
- языковая ветка model-router: `vi, th, id, ar`, без `ru`.

BM25 использует конфигурацию полнотекстового поиска PostgreSQL `simple` для неанглийских языков, но это само по себе не доказывает качество multilingual embeddings или OCR/ingestion для русского. Настроенная локальная embedding-модель по умолчанию — `mxbai-embed-large`; фактическую комбинацию модели и корпуса нужно оценить измерениями RU/EN.

**Исправление:** добавлять русский язык согласованно в конфигурацию поддерживаемых API-языков, loader, OCR, ingestion и routing только после выбора и проверки профиля embeddings и OCR; затем запустить сбалансированный размеченный RU/EN retrieval benchmark и публиковать оценки раздельно.

### P1 — Reranking является точкой расширения, а не активным этапом runtime

`PgVectorStore` принимает необязательный `RerankerPort`, но `AIComponents.initialize()` создаёт его без reranker. В проверенном пути не найдено конкретной factory для reranker или внедрения в runtime. `RAG_RERANK_TOP_N` объявлен в settings/template, но не используется при создании runtime. RRF сейчас использует значение метода `hybrid_search()` по умолчанию — `rrf_k=60`.

**Оценка:** гибридный vector + keyword retrieval и RRF активны; cross-encoder или другой специализированный reranker не подтверждён как активный.

### P1 — Некоторые объявленные настройки RAG не действуют как параметры runtime

| Настройка | Объявление источника | Вывод о runtime |
|---|---|---|
| `RAG_TOP_K` | `RAGSettings.top_k` | Передаётся в `LangGraphRAG`; активна |
| `RAG_MAX_CONTEXT_DOCS` | `RAGSettings.max_context_docs` | Передаётся в `LangGraphRAG`; активна |
| `RAG_MAX_REWRITES` | `RAGSettings.max_rewrites` | Передаётся в `LangGraphRAG`; активна |
| `RAG_MAX_QUERY_VARIATIONS` | `RAGSettings.max_query_variations` | Передаётся в `LangGraphRAG`; активна |
| `RAG_ENABLE_MULTI_QUERY` | `RAGSettings.enable_multi_query` | Передаётся в граф; активна |
| `RAG_ENABLE_HYDE` | `RAGSettings.enable_hyde` | Передаётся в граф; активна |
| `RAG_RERANK_TOP_N` | Settings/template | Не используется; активный reranker не внедрён |
| `RAG_RRF_K` | Settings class | Не передаётся в runtime; hybrid search использует значение метода по умолчанию |
| `RAG_ENABLE_CONTEXTUAL_COMPRESSION` | Settings/template | Не передаётся в граф; compression node всегда присутствует в графе |
| `RAG_MAX_CHUNK_TOKENS`, `RAG_CHUNK_OVERLAP` | Settings/template | Celery ingestion task читает конфигурацию конкретной задачи с жёстко заданными defaults, а не эти настройки |
| `RAG_DEFAULT_LANGUAGES` | Settings class | Пути ingestion используют собственные defaults; использование этой настройки в runtime не найдено |

**Исправление:** удалить неиспользуемые параметры или подключить их к активному пути создания компонентов, затем добавить contract tests, доказывающие, что изменение каждой поддерживаемой переменной окружения меняет поведение runtime.

### P1 — У ingestion два пути с разными гарантиями

API routes в `src/pharmaviyum/api/v1/ingestion.py` отправляют задачи Celery. Worker task в `mortarium_rag/ingestion/tasks.py` проверяет pharmacy ID и проставляет канонические tenant/source metadata до chunking и сохранения. Это активный API-путь ingestion.

Отдельный `IngestionOrchestrator` создаётся при инициализации AI dependencies, однако вызывающих его методов `ingest_file()`/`ingest_batch()` в API не найдено. Его путь `ingest_file()` проверяет pharmacy ID для дедупликации, но явно не проставляет те же канонические tenant metadata перед `PgVectorStore.upsert()`; затем vector store завершает операцию fail-closed, если в metadata чанка отсутствуют обязательные tenant metadata.

**Исправление:** считать Celery worker единственным документированным путём ingestion и либо удалить неиспользуемый orchestrator, либо привести его к тем же гарантиям доверенного проставления tenant, авторизации, жизненного цикла и тестирования. Не предоставлять orchestrator как второй ingestion API до совпадения контрактов.

### P2 — Runtime-проверка цитат проверяет членство ID, а не логическое подтверждение утверждения

RAG graph и Agent Harness отклоняют отсутствующие/сфабрикованные ID цитат, когда есть найденные источники. Это полезная проверка происхождения, но она не доказывает, что источник подтверждает предложение, к которому прикреплена цитата. Offline evaluator `citation_correctness()` может использовать внедрённый entailment judge; без него метрика сообщает, что недоступна.

Не называйте runtime-проверку ID цитат семантической корректностью цитирования. Entailment и поддержку клинических утверждений следует оценивать offline с экспертной проверкой.

### P2 — Confidence и safety score API являются эвристическими placeholders

AI API сейчас присваивает фиксированные значения confidence и safety score в зависимости от наличия предупреждений. Это не калиброванные вероятности и не независимо измеренные показатели клинической безопасности. Считайте их только эвристиками представления; не используйте для автоматических клинических решений, ранжирования риска или приёмки релиза.

### P2 — Маршрутизация моделей эвристическая

`ModelRouter` выбирает fast/main/complex модели по длине запроса, совпадению английских ключевых слов, контексту пациента/рецепта и небольшому списку языков. Это детерминированная эвристическая маршрутизация, а не валидированный классификатор клинического риска. Она не должна заменять эскалацию на основе политик или проверку фармацевтом. Специализированная маршрутизация для русского не настроена.

### P2 — Для контроля хранения и обратной связи требуется операционное подтверждение

Checkpoint графа PostgreSQL могут содержать вопросы и найденный клинический контекст. Память Redis имеет ограниченный TTL семь дней, однако TTL не является полной политикой хранения/удаления PHI. Срок хранения резервных копий, юридические сроки хранения, распространение удаления, аудит доступа и поведение восстановления требуют явной операционной проверки. В рамках этого аудита не установлена полноценная схема «обратная связь фармацевта → проверенный набор оценки → регрессионный workflow».

## Реализация RAG и оценки

### Активный RAG-граф

`LangGraphRAG` компилирует state graph, включающий:

1. input guardrail и преобразование запроса;
2. сохранение исходного запроса вместе с ограниченным набором multi-query кандидатов и необязательным HyDE;
3. retrieval по векторному поиску и ключевым словам с фильтрацией tenant;
4. оценку документов с помощью LLM и ограниченные попытки переписывания запроса;
5. контекстное сжатие;
6. генерацию с предварительной проверкой бюджета входных токенов;
7. выходные guardrails и post-generation проверку ID цитат.

Граф требует явный checkpointer, использует deadline графа 90 секунд по умолчанию, ограничивает параллелизм retrieval до 6 и grading до 4, а также имеет явный предел рекурсии. Вывод HyDE — вспомогательный материал для поиска, а не проверенное доказательство.

### Ragas и фармацевтические evaluators

- Ragas закреплён на версии `0.4.3` в группе зависимостей `eval` в `pyproject.toml` и разрешён в `uv.lock`; группа выбирается для CI/offline evaluation, а не для установки production runtime.
- `RagasEvaluationAdapter` лениво импортирует Ragas 0.4 collections API; LLM evaluator и embeddings передаются извне.
- CI RAG evaluation job проверяет импорт collections API и запускает `tests/unit/ai/test_ragas_evaluation.py` вместе с проверкой golden dataset.
- Unit-тесты адаптера подменяют классы метрик Ragas; это проверка контракта, а не измеренный запуск с реальной judge-моделью.
- Проектные evaluators проверяют точное совпадение названия/дозировки/формы лекарства, размеченные отрицания, поддержку утверждения ID источника, долю клинических галлюцинаций, изоляцию метаданных источников и отдельный recall эталонных источников RU/EN.
- Метрики entailment цитат и клинических галлюцинаций сообщают о недоступности, если не передан независимый judge для проверки утверждений.

**В рамках этого статического аудита не запускались новый live Ragas run, клинический benchmark с оценкой фармацевтов или реальный RU/EN retrieval benchmark.** Существующие исторические результаты benchmark привязаны к исходным ревизиям и ограничениям синтетических данных/test doubles; они не являются доказательством production-производительности или клинического качества.

## MCP и аптечные операции

Текущие документированные MCP-инструменты аптечных операций доступны только для чтения. Схемы инструментов проверяются, обнаружение по ролям фильтруется, а выполнение требует доверенного контекста пользователя/роли/аптеки в рамках запроса. Generic SQL, shell, filesystem и code-execution ввод отклоняется. Инструменты записи должны явно объявлять write execution и подтверждение фармацевта; registry блокирует их, пока доверенный verifier не проверит и не использует подтверждение.

ERP остаётся источником истины для цен, остатков, FEFO, рецептурных ограничений, состояния платежей и результатов транзакций. Mortarium не должен заявлять об успешной записи или бизнес-операции без авторитетного подтверждения.

## Наблюдаемость и конфиденциальность

Узлы RAG graph и выполнение агента создают ограниченные spans OpenTelemetry. Документированная политика запрещает помещать prompts, completions, идентификаторы пациентов, найденный клинический текст и необработанные аргументы инструментов в telemetry. Метки Prometheus должны иметь низкую кардинальность. Наличие SDK/spans не доказывает, что OTLP exporter, collector, alerts, retention и incident response работают в каждом deployment.

## Доказательства проверки и ограничения

В репозитории есть unit/security-тесты контрактов RAG, MCP RBAC/authorization, бюджетов выполнения агента, изоляции метаданных пациента, проверки цитат и поведения адаптера Ragas. CI workflow определяет unit, integration, security и RAG-evaluation jobs. Этот аудит не запускал эти jobs и не утверждает, что они успешны на проверенной ревизии SHA.

Предыдущий синтетический benchmark от 2026-10-15 использовал детерминированные test doubles для LLM/embeddings/retrieval в основном результате concurrency. Отдельный pgvector smoke test использовал специально сформированные vectors и небольшой fixture corpus. Сохраняйте эти результаты только как исторические ограниченные доказательства.

## Приоритетный backlog исправлений

1. **P0 release gate:** Выполнить staged-тесты Patient A → Patient B → no-patient в одной client session для streaming/non-streaming API, Redis memory и PostgreSQL checkpoints; зафиксировать доказательства до production activation.
2. **P1 operational:** Утвердить retention/deletion старых plaintext RAG checkpoints и backup-expiry policy; проверить secret distribution, rotation и rollback.
3. **P1:** Согласовать ingestion на одном каноническом пути с одинаковыми гарантиями tenant stamping и жизненного цикла.
4. **P1:** Подключить или удалить неэффективные настройки RAG; добавить тесты, доказывающие влияние environment overrides на runtime.
5. **P1:** Определить и проверить поддержку русского языка/OCR/embeddings; запускать отдельные retrieval benchmarks RU и EN.
6. **P1:** Реализовать и внедрить конкретный reranker только если размеченный benchmark покажет измеримую пользу; иначе удалить вводящую в заблуждение настройку rerank.
7. **P2:** Отделить эвристические API confidence/safety fields от калиброванных результатов оценки.
8. **P2:** Добавить оценку цитирования/клинических утверждений на уровне claim по эталонным меткам, проверенным фармацевтами.
9. **P2:** Завершить операционную политику хранения/удаления PHI для checkpoint/memory, резервного копирования и восстановления.
10. **P2:** Создать управляемый регрессионный процесс от обратной связи фармацевта к оценке.

## Заявление о статусе релиза

Это статический архитектурный аудит, а не клиническая валидация, регуляторная оценка, сертификация production-безопасности, нагрузочный тест или разрешение на deployment. Код patient-aware session/checkpoint namespace влит, но staged-проверка изоляции и production activation остаются открытыми. Также остаются открытыми retention старых checkpoints, измеренное качество RU/EN и deployment-specific меры жизненного цикла PHI. В рамках этого аудита документации production-конфигурация, база данных, провайдер моделей и deployment не изменялись.
