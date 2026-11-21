# Руководство по тестированию

Это руководство описывает текущую структуру тестов и те же критерии качества, которые использует CI pipeline репозитория.

## Быстрый запуск

```bash
# Unit-тесты
./scripts/test.sh unit

# Интеграционные тесты
./scripts/test.sh integration

# Полный локальный набор
./scripts/test.sh all

# Покрытие
./scripts/test.sh coverage
```

Для отдельного теста:

```bash
uv run --locked pytest tests/<path_to_test>.py -v
uv run --locked pytest -m unit -v
uv run --locked pytest -m integration -v
```

## Структура тестов

В репозитории тесты разделены по назначению:

```text
tests/
├── unit/
├── integration/
├── security/
├── architecture/
├── evaluation/
├── conftest.py
└── ...
```

Точная структура файлов меняется вместе с реализацией. Для актуального состава тестов ориентируйтесь на файловую систему и коллекцию pytest, а не поддерживайте в этом документе статический перечень каждого тестового модуля.

## Категории тестов

В проекте используются pytest markers, где это применимо:

```bash
pytest -m unit
pytest -m integration
uv run --locked pytest -m "not slow"
```

Не каждому тесту требуется внешний LLM. RAG-, agent-, security- и integration-тесты следует запускать с зависимостями, необходимыми для соответствующей категории.

## Зависимости

Текущая команда установки runtime/test-зависимостей, используемая Docker и CI:

```bash
uv sync --frozen
```

**Не используйте и не создавайте устаревший файл `requirements-ai.txt`.**

`pyproject.toml` является источником прямых объявлений зависимостей, а `uv.lock` фиксирует разрешённое окружение. CI, Docker, Makefile и локальные точки входа тестирования должны использовать закоммиченный lockfile (`uv sync --frozen` или `uv run --locked`), а не произвольные команды `pip install`.

## Локальная инфраструктура

Интеграционные тесты используют PostgreSQL и Redis. Development Compose stack предоставляет эти сервисы:

```bash
docker compose up -d postgres redis
```

Для тестов, которым нужен полный стек:

```bash
docker compose up -d
```

## Тестирование разрушительного жизненного цикла миграций

`scripts/test_migrations.sh` выполняет `alembic downgrade base`, удаляя все мигрированные таблицы в целевой базе данных. Запускайте его только против временной disposable-базы.

Скрипт требует все следующие меры защиты:

- `ALLOW_DESTRUCTIVE_MIGRATION_TESTS=1` как явное подтверждение разрушительной операции;
- `MIGRATION_TEST_DATABASE_URL` с именем базы, содержащим `test` или `testing`;
- по умолчанию hostname loopback (`localhost`, `127.0.0.1` или `::1`);
- для выделенной удалённой тестовой базы — точный проверенный hostname в `MIGRATION_TEST_ALLOWED_HOSTS` (несколько hostnames разделяются запятыми).

Пример для локальной временной базы:

```bash
ALLOW_DESTRUCTIVE_MIGRATION_TESTS=1 \
MIGRATION_TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/pharmaviyum_test \
./scripts/test_migrations.sh
```

Не добавляйте production database hosts в `MIGRATION_TEST_ALLOWED_HOSTS`. Явное opt-in и имя базы, похожее на тестовое, не делают production-базу безопасной целью.

## Тесты RAG

Тесты RAG должны проверять production-инварианты текущего pipeline, в особенности:

- изоляцию аптеки/tenant;
- контекст страны и языка;
- поведение retrieval;
- стабильные цитаты `src-{chunk_uuid}`;
- генерацию на основе найденных источников;
- guardrails;
- наблюдаемость retrieval без меток высокой кардинальности.

Не пишите тесты, предполагающие отдельное Kubernetes-развёртывание RAG: текущая архитектура — прикладной RAG pipeline.

## Benchmark и оценка качества AI

Используйте [требования к инженерному benchmark](../devops/ENGINEERING_BENCHMARK_REQUIREMENTS.md) как каноническую спецификацию определений метрик, меток доказательств, профилей нагрузки и release gates.

Набор оценки должен сохранять раздельные измерения: ранжирование retrieval (Recall@K, Precision@K, Hit Rate@K, MRR, nDCG), поддерживаемые метрики ответов/контекста Ragas, детерминированную проверку цитат, фармацевтические/клинические метрики с проверкой фармацевтом, корректность agent/MCP, тесты tenant/security и операционную производительность. Доступность метрик Ragas и API зависит от версии; проверяйте закреплённую установленную версию. Специализированные аптечные метрики, такие как точность сущностей лекарств, точность дозировок, сохранение отрицаний и доля клинических галлюцинаций, требуют пользовательских evaluators и эталонных данных, проверенных экспертами.

Для каждого запуска фиксируйте commit SHA, среду, команду, профиль нагрузки, dataset/версию, число примеров, версии модели/prompt/index и исходный артефакт. Помечайте каждый результат как MEASURED, HISTORICAL, ESTIMATED, NOT TESTED или UNAVAILABLE. Не представляйте отсутствующие измерения как ноль или PASS. Codespaces подходит для проверок репозитория и детерминированных синтетических тестов; производительность на уровне production и управляемых сервисов требует изолированной staging-среды.

## Тесты безопасности

Проверки безопасности входят в CI и включают аудит зависимостей и Bandit. Тесты безопасности репозитория находятся в `tests/security`.

Не используйте в security fixtures реальные credentials или персональные данные.

## Критерии качества CI/CD

Канонический workflow: `.github/workflows/ci.yml`.

Сейчас pipeline включает:

1. linting Ruff;
2. проверки форматирования Black;
3. проверки isort;
4. проверку типов mypy;
5. unit-тесты;
6. integration-тесты с PostgreSQL/Redis и pgvector, где это требуется;
7. `uv run --locked pip-audit`;
8. Bandit;
9. RAG evaluation / проверки golden dataset;
10. сборку/публикацию Docker после успешного прохождения обязательных проверок.

Канонический CI workflow — `.github/workflows/ci.yml`; не документируйте CircleCI или устаревший test workflow как активную инфраструктуру.

## Отладка

Полезные команды:

```bash
uv run --locked pytest -v -s tests/<test>.py
uv run --locked pytest --showlocals tests/<test>.py
uv run --locked pytest -x tests/<test>.py
uv run --locked pytest --pdb tests/<test>.py
```

Если интеграционный тест завершился ошибкой из-за инфраструктуры, проверьте логи сервисов:

```bash
docker compose logs -f postgres
docker compose logs -f redis
docker compose logs -f api
```

## Рекомендации

- Делайте unit-тесты детерминированными и изолированными от внешних сервисов.
- Подменяйте вызовы LLM/provider в unit-тестах.
- Используйте integration-тесты для проверки реального поведения БД/Redis.
- Предпочитайте fixtures для повторно используемой подготовки и очистки.
- Применяйте Arrange → Act → Assert.
- Явно тестируйте границы безопасности, особенно изоляцию tenant.
- Никогда не ослабляйте CI-проверки, чтобы заставить падающий тест пройти.
- Обновляйте этот документ при изменении канонических команд тестирования или CI workflow.
