# Руководство по разработке и тестированию

Это практическая отправная точка для участников проекта. Подробные инструкции по настройке окружения и тестированию остаются каноническими источниками для специфичных шагов.

## Источники истины

- Метаданные Python-проекта и ограничения зависимостей: `pyproject.toml`.
- Разрешённый граф Python-зависимостей: `uv.lock`.
- Манифест frontend-пакетов: `frontend/shadcn-admin/package.json`.
- Точка входа backend-приложения: `src.pharmaviyum.main:app`.
- Backend-тесты: `tests/`.
- Frontend-тесты: `frontend/shadcn-admin`.
- CI workflows: `.github/workflows/`.

Не добавляйте второй манифест Python-зависимостей и не редактируйте lockfile вручную.

## Локальное окружение

Следуйте [руководству по настройке окружения](./ENVIRONMENT_SETUP.md), чтобы установить предварительные требования, переменные окружения и локальные сервисы.

Типичный запуск локального Docker:

```bash
cp .env.example .env
docker compose up --build
```

Прямой запуск API после подготовки зависимостей и локальной инфраструктуры:

```bash
uv sync --frozen
uv run alembic upgrade head
uv run uvicorn src.pharmaviyum.main:app --reload --port 8000
```

Запускайте миграции только против предназначенной для этого локальной/test базы данных. Никогда не копируйте production credentials в среду разработки.

## Критерии качества backend

```bash
uv run ruff check .
uv run black --check .
uv run isort --check-only .
uv run mypy --explicit-package-bases src
uv run pytest
```

Для запуска отдельного тестового набора передайте его путь в pytest, например:

```bash
uv run pytest tests/unit/ai/
```

Интеграционные тесты должны использовать изолированные временные сервисы и не должны зависеть от production-данных.

## Критерии качества frontend

```bash
cd frontend/shadcn-admin
bun install --frozen-lockfile
bun run lint
bun run test
bun run test:e2e
bun run build
```

Если имена scripts изменятся, источником истины должны оставаться scripts в package manifest.

## Оценка AI / RAG

Ragas — зависимость только для оценки, объявленная в группе `eval` файла `pyproject.toml` и зафиксированная в `uv.lock`. Устанавливайте эту группу только в среде оценки:

```bash
uv sync --frozen --group eval
uv run pytest tests/unit/ai/test_ragas_evaluation.py -v -m unit
```

Правила подготовки datasets и семантика метрик описаны в документе [«Фармацевтическая оценка Ragas»](../ai/ragas-pharmaceutical-evaluation.ru.md). Успешный adapter/unit test не доказывает, что измеренное клиническое качество является приемлемым.

## Пирамида тестирования и доказательства

| Уровень | Назначение | Требуемые доказательства |
|---|---|---|
| Unit | Чистая логика, валидация, сериализаторы и graph helpers | Детерминированные assertions |
| API | Аутентифицированные запросы/ответы и авторизация tenant | Fixtures ролей и tenant |
| Integration | Границы PostgreSQL, Redis и worker | Временные сервисы и очистка |
| Contract | Frontend/backend, события и схемы MCP | Проверки схем с контролем версий |
| E2E | Критические workflow фармацевта | Воспроизводимый браузерный сценарий с синтетическими данными |
| Load | Пропускная способность, latency и saturation | Отчёт k6 и предположения о нагрузке |
| AI evaluation | Retrieval, цитаты, grounding и фармацевтические метрики | Версионируемый отчёт и экспертная оценка человеком |

Не делайте вывод о сквозном покрытии бизнес-процессов только по ответу endpoint с HTTP 200 или отображению экрана UI.

## Контрольный список Pull Request

- [ ] Ограниченная область изменений и связанная issue/decision.
- [ ] Проверены авторизация и границы tenant/пациента.
- [ ] Изменения БД обратно совместимы либо план миграции проверен.
- [ ] Зависимости обоснованы, lockfile актуален.
- [ ] Lint, форматирование, типы и релевантные тесты проходят.
- [ ] Security и dependency scans проходят.
- [ ] Документация и ADR обновлены.
- [ ] Не добавлены секреты или реальные данные пациентов.
- [ ] Результаты CI относятся к последнему head SHA PR.
- [ ] Production deployment и миграции не запускаются непреднамеренно.

## Связанные руководства

- [Настройка окружения](./ENVIRONMENT_SETUP.md)
- [Руководство по тестированию](./TESTING.md)
- [Руководство по Codespaces](./CODESPACES_GUIDE.md)
- [Технологический стек](../technology-stack.ru.md)
- [Runbook релиза](../operations/RELEASE_RUNBOOK.md)
