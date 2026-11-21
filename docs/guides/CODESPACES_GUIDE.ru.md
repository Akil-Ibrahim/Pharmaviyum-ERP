# Руководство по GitHub Codespaces

Документ описывает текущий workflow Codespaces для Pharmaviyum ERP/CRM.

## 1. Создание Codespace

Создайте Codespace из ветки `dev`, используя конфигурацию репозитория `.devcontainer`.

После создания запускается `.devcontainer/setup.sh`.

Devcontainer использует Docker-in-Docker для запуска стека приложения. Если Docker недоступен в уже существующем Codespace после изменения `.devcontainer`, выполните **Codespaces: Rebuild Container** из Command Palette VS Code. Пересборка сохраняет workspace Codespace. Не удаляйте database volumes, если не хотите намеренно сбросить локальные данные.

## 2. Что делает setup

Скрипт настройки:
1. устанавливает Python-зависимости из `pyproject.toml + uv.lock`;
2. собирает и запускает PostgreSQL, Redis, API (включая frontend build) и Celery worker через `docker-compose.codespaces.yml`;
3. ожидает health checks PostgreSQL и Redis, затем проверяет endpoint API `/health`;
4. запускает database migrations в API container до старта API;
5. выводит URLs API и Docs для Codespaces.

В текущем проекте нет dependency-файла `requirements-ai.txt`.

## 3. Настройка окружения

Начните с шаблона репозитория:
```bash
cp .env.example .env
```

Добавьте конфигурацию провайдера, необходимую вашему окружению. В зависимости от конфигурации и доступных ресурсов приложение использует cloud LLM provider или локальный Ollama.

Никогда не коммитьте `.env` и provider API keys.

## 4. Проверка окружения

После завершения setup:
```bash
docker compose -f docker-compose.codespaces.yml ps
curl --fail http://localhost:8000/health
```

Setup запускает API и обслуживает собранный frontend из API container.

Для перезапуска и просмотра логов:
```bash
docker compose -f docker-compose.codespaces.yml restart api celery-worker
docker compose -f docker-compose.codespaces.yml logs -f api
```

Для ERP/CRM load test используйте только synthetic records и выделенную тестовую учётную запись. Следуйте профилям и ограничениям в [Stage 1 Load Testing](../devops/STAGE_1_LOAD_TESTING.md). Один успешный ответ `/health` не подтверждает работу database-backed workflows.

Для доступа к Docs используйте forwarded port 8000:
```text
https://<codespace-name>-8000.app.github.dev/docs
```

## 5. Запуск тестов

```bash
./scripts/test.sh unit
./scripts/test.sh integration
./scripts/test.sh all
```

Для полного development stack:
```bash
docker compose up --build
```

## 6. Полезные команды

```bash
docker compose -f docker-compose.codespaces.yml ps
docker compose -f docker-compose.codespaces.yml logs -f api
docker compose -f docker-compose.codespaces.yml logs -f postgres
docker compose -f docker-compose.codespaces.yml logs -f redis
docker compose -f docker-compose.codespaces.yml logs -f celery-worker
docker compose -f docker-compose.codespaces.yml exec postgres pg_isready -U postgres -d pharmaviyum
docker compose -f docker-compose.codespaces.yml stop
docker compose -f docker-compose.codespaces.yml down -v
```

Последняя команда удаляет зависимости вместе с volumes и локальными данными.

## 7. Архитектура Codespaces

```text
GitHub Codespace
      |
      +--> FastAPI application
      |       +--> AI Agent Harness
      |       +--> RAG pipeline
      |       +--> MCP tools
      |       +--> API / health / metrics
      |
      +--> PostgreSQL + pgvector
      +--> Redis
      |
      +--> configured LLM provider / Ollama
```

Codespaces — среда разработки. Hosted deployment приложения выполняется отдельно через вручную запускаемый GitHub Actions workflow FastAPI Cloud.

## 8. Устранение неполадок

### ModuleNotFoundError

```bash
python -m uv sync --frozen
```

### PostgreSQL или Redis недоступны

```bash
docker compose -f docker-compose.codespaces.yml ps
docker compose -f docker-compose.codespaces.yml restart postgres redis
```

### Команда Docker отсутствует

Docker-in-Docker feature применяется при сборке devcontainer. Пересоберите container через Command Palette VS Code, затем проверьте:

```bash
docker info
```

### Ошибка запуска API или миграций

```bash
docker compose -f docker-compose.codespaces.yml logs --tail 200 api
docker compose -f docker-compose.codespaces.yml logs --tail 100 postgres
```

### Ошибки LLM-запросов

Проверьте provider configuration в `.env` и перезапустите API после изменения environment variables. Базовый ERP/API может запускаться без provider key, но вызовы AI/RAG требуют настроенного provider key. Не коммитьте `.env` и не отправляйте provider keys в чат.

## 9. Поддержание актуальности

Источники истины для Codespaces: `.devcontainer/devcontainer.json`, `.devcontainer/setup.sh`, `docker-compose.codespaces.yml` и `.env.example`. При изменении этих файлов обновляйте данное руководство, а не создавайте вторую конкурирующую процедуру настройки.