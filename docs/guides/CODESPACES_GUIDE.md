# 🚀 Запуск Pharmaviyum AI в GitHub Codespaces

Полный гайд для быстрого запуска проекта в облаке без необходимости GPU.

---

## 📋 Предварительные требования

1. **GitHub аккаунт** (бесплатный или Pro)
2. **Этот репозиторий** загружен на GitHub
3. **API ключ одного из провайдеров** (все предложения имеют бесплатный tier):
   - **Groq** (рекомендуется): https://console.groq.com → 14,400 запросов/день бесплатно
   - **OpenAI**: https://platform.openai.com/api-keys → pay-as-you-go (стартовый кредит $5)
   - **Anthropic**: https://console.anthropic.com/ → pay-as-you-go

---

## 🎯 ШАГ 1: Создание Codespace

### Вариант A: Через GitHub UI (проще)

1. Откройте ваш репозиторий на GitHub: `https://github.com/YOUR_USERNAME/Pharmaviyum-CRM`
2. Нажмите зелёную кнопку **"Code"** → вкладка **"Codespaces"**
3. Нажмите **"Create codespace on dev"**
4. Выберите конфигурацию:
   - **Machine type**: `4-core` (бесплатно) или `8-core` (если есть Pro план)
   - **Region**: Europe (ближайший к вам)
5. Нажмите **"Create codespace"**

**⏱️ Время создания:** 2-5 минут (первый раз медленнее из-за установки)

### Вариант B: Через GitHub CLI

```bash
gh codespace create --repo YOUR_USERNAME/Pharmaviyum-CRM --machine 4core
```

---

## 🎯 ШАГ 2: Получение API ключа Groq (рекомендуется)

### Почему Groq?
- ✅ **14,400 запросов/день бесплатно** — достаточно для разработки
- ✅ **Молниеносная скорость** — 1000+ токенов/сек
- ✅ **Не требует GPU** — работает на CPU
- ✅ **Отличные модели** — Llama 3.1 70B (сравнима с GPT-4)
- ✅ **Один клик через GitHub** — вход моментальный

### Инструкция (5 минут):

1. Откройте https://console.groq.com
2. Нажмите **"Sign in with GitHub"** (один клик)
3. В левом меню нажмите **"API Keys"**
4. Нажмите **"Create API Key"**
5. Введите название (например, `codespaces`)
6. **Скопируйте ключ** (начинается с `gsk_...`)
7. **Сохраните его** — показывается только один раз!

✅ **Ключ готов!**

---

## 🎯 ШАГ 3: Настройка .env в Codespace

Когда Codespace откроется, откройте терминал (`` Ctrl+` ``) и выполните:

```bash
# 1. Скопировать .env.example в .env
cp .env.example .env

# 2. Открыть для редактирования
code .env
```

**Замените следующие строки:**

```bash
# ============================================================================
# PHARMAVIYUM AI - Codespaces Configuration
# ============================================================================

# Environment - ВАЖНО для Codespaces
ENVIRONMENT=development
LOG_LEVEL=INFO
USE_CLOUD_LLM=true  # Обязательно true в Codespaces

# ============================================================================
# CLOUD LLM: Groq (РЕКОМЕНДУЕТСЯ для Codespaces)
# ============================================================================
GROQ_API_KEY=gsk_ВСТАВЬТЕ_ВАШ_КЛЮЧ_СЮДА
GROQ_MODEL=llama-3.1-70b-versatile
GROQ_FAST_MODEL=llama-3.1-8b-instant

# Отключить локальный Ollama (не работает в Codespaces)
OLLAMA_BASE_URL=  # Оставить пустым

# Остальное оставить как есть
```

**Сохраните файл:** `` Ctrl+S ``

✅ **Конфигурация готова!**

---

## 🎯 ШАГ 4: Автоматический запуск

Codespace автоматически запустит `.devcontainer/setup.sh` при создании.

**Что делает скрипт:**
1. Устанавливает Python зависимости (~2 мин)
2. Запускает PostgreSQL + Redis в Docker (~1 мин)
3. Выполняет миграции БД (~5 сек)
4. Проверяет готовность сервисов

**Время ожидания:** 3-4 минуты

---

## 🎯 ШАГ 5: Проверка что всё работает

### 1. Открыть Swagger UI

После запуска вы увидите уведомление в Codespaces:

> **"Your application running on port 8000 is available"**

Нажмите **"Open in Browser"** или перейдите:

```
https://<ВАШ-CODESPACE-NAME>-8000.app.github.dev/docs
```

Вы должны увидеть полную документацию API.

### 2. Проверить health endpoint

```
https://<ВАШ-CODESPACE-NAME>-8000.app.github.dev/health
```

**Ожидаемый ответ:**
```json
{
  "status": "healthy",
  "service": "pharmaviyum-ai"
}
```

### 3. Тестовый запрос

В Swagger UI найдите `POST /api/v1/ai/query` и нажмите **"Try it out"**

**Тестовый запрос:**
```json
{
  "query": "What are the drug interactions between Warfarin and Aspirin?",
  "session_id": "test-123",
  "country": "VN",
  "language": "en",
  "halal_filter": false
}
```

Нажмите **"Execute"** и дождитесь ответа (~2-3 сек с Groq).

**Ожидаемый ответ:**
```json
{
  "session_id": "test-123",
  "query": "What are the drug interactions between Warfarin and Aspirin?",
  "answer": "⚠️ Warfarin and Aspirin have a CRITICAL interaction...",
  "confidence": 0.9,
  "model_used": "llama-3.1-70b-versatile",
  "total_latency_ms": 1234.56
}
```

✅ **Всё работает!**

---

## 🎯 ШАГ 6: Демонстрация ключевых фич

### Демо 1: Halal Compliance (на арабском)

**Запрос:**
```json
{
  "query": "هل يمكنني تناول كبسولات الأموكسيسيلين؟ أنا أتبع فتوى السيد السيستاني.",
  "session_id": "test-halal-1",
  "country": "IQ",
  "language": "ar",
  "halal_filter": true
}
```

**Ожидаемый результат:**
- Ответ на арабском
- Указание школы фикха (Ja'fari)
- Источники: правила Sistani
- Статус halal: ✅ Разрешено

### Демо 2: Streaming Response

В терминале Codespace:

```bash
curl -N -X POST "https://<ВАШ-CODESPACE-NAME>-8000.app.github.dev/api/v1/ai/query/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the dosage of Paracetamol for adults?",
    "session_id": "test-stream-1",
    "country": "VN",
    "language": "en"
  }'
```

Вы увидите real-time токены по мере их генерации.

### Демо 3: Metrics

```
https://<ВАШ-CODESPACE-NAME>-8000.app.github.dev/metrics
```

Prometheus metrics со статистикой всех запросов.

---

## 🐛 TROUBLESHOOTING

### ❌ Проблема: "Connection refused" при запуске

**Причина:** PostgreSQL или Redis не готовы

**Решение:**
```bash
# Проверить статус сервисов
docker-compose -f docker-compose.codespaces.yml ps

# Если не healthy, перезапустить
docker-compose -f docker-compose.codespaces.yml restart postgres redis

# Подождать 10 сек и проверить снова
docker-compose -f docker-compose.codespaces.yml ps
```

### ❌ Проблема: "ModuleNotFoundError: No module named 'fastapi'"

**Причина:** Зависимости не установлены

**Решение:**
```bash
pip install -r requirements-ai.txt
```

### ❌ Проблема: "Groq API key invalid"

**Причина:** Неправильный ключ в .env

**Решение:**
1. Проверьте ключ в https://console.groq.com/keys
2. Убедитесь что в .env нет лишних пробелов:
   ```bash
   # ✅ Правильно:
   GROQ_API_KEY=gsk_abc123def456
   
   # ❌ Неправильно:
   GROQ_API_KEY= gsk_abc123def456
   ```
3. Сохраните .env и перезагрузите терминал (или перезапустите API)

### ❌ Проблема: "Alembic migration failed"

**Причина:** Таблица уже существует или проблема с подключением

**Решение:**
```bash
# Проверить подключение
docker-compose -f docker-compose.codespaces.yml exec postgres \
  psql -U postgres -d pharmaviyum -c "SELECT 1"

# Если ошибка, пересоздать БД
docker-compose -f docker-compose.codespaces.yml down -v
docker-compose -f docker-compose.codespaces.yml up -d postgres redis
sleep 10
alembic upgrade head
```

### ❌ Проблема: Codespace останавливается через 30 минут

**Причина:** Неактивность (бесплатный план)

**Решение:**
- Данные сохраняются (volumes persistent)
- Просто откройте Codespace снова — всё восстановится
- На Pro плане Codespaces живут дольше

---

## 📊 Архитектура в Codespaces

```
┌────────────────────────────────────────────────────┐
│         GitHub Codespace                           │
│    (4-core CPU, 8GB RAM, ~30GB SSD)                │
├────────────────────────────────────────────────────┤
│                                                    │
│  Docker Services:                                 │
│  ┌──────────────┐  ┌──────────────┐              │
│  │ PostgreSQL   │  │    Redis     │              │
│  │ + pgvector   │  │  (in-memory) │              │
│  └──────┬───────┘  └──────┬───────┘              │
│         │                  │                       │
│  ┌──────▼──────────────────▼─────────────────┐    │
│  │      FastAPI Application                 │    │
│  │  (src/pharmaviyum/main.py)                │    │
│  │                                           │    │
│  │  ├─ RAG Pipeline (Query → Answer)        │    │
│  │  ├─ Agent Orchestration (LangGraph)      │    │
│  │  ├─ MCP Tools (Halal, Drug Interaction)  │    │
│  │  └─ Health/Metrics Endpoints             │    │
│  └──────┬───────────────────────────────────┘    │
│         │                                         │
│  ┌──────▼────────────────────────────────────┐   │
│  │    Cloud LLM APIs                        │   │
│  │  ┌────────┐ ┌────────┐ ┌───────────┐   │   │
│  │  │  Groq  │ │ OpenAI │ │Anthropic  │   │   │
│  │  │(Recom.)│ │(optional) │(optional) │   │   │
│  │  └────────┘ └────────┘ └───────────┘   │   │
│  └──────────────────────────────────────────┘   │
│                                                   │
└────────────────────────────────────────────────────┘
           │
           ▼
    Port 8000 forwarded
    https://<codespace-name>-8000.app.github.dev
```

---

## ⚡ Быстрые команды

```bash
# 📊 Проверить статус всех сервисов
docker-compose -f docker-compose.codespaces.yml ps

# 🔍 Посмотреть логи FastAPI
docker-compose -f docker-compose.codespaces.yml logs -f api

# 🔍 Посмотреть логи PostgreSQL
docker-compose -f docker-compose.codespaces.yml logs -f postgres

# 🔍 Посмотреть логи Redis
docker-compose -f docker-compose.codespaces.yml logs -f redis

# 🔄 Перезапустить API
docker-compose -f docker-compose.codespaces.yml restart api

# 🔄 Перезапустить все сервисы
docker-compose -f docker-compose.codespaces.yml restart

# 🛑 Остановить все сервисы (но данные сохранятся)
docker-compose -f docker-compose.codespaces.yml stop

# 🗑️ Удалить всё (включая БД и кэш)
docker-compose -f docker-compose.codespaces.yml down -v

# 🗄️ Подключиться к БД
docker-compose -f docker-compose.codespaces.yml exec postgres \
  psql -U postgres -d pharmaviyum

# 🧪 Запустить тесты
pytest -q

# 📝 Запустить линтер
ruff check src/

# 🚀 Запустить сервер API (вручную)
uvicorn src.pharmaviyum.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🎬 Полный цикл для собеседования (5-7 минут)

### 1. Показ инфраструктуры (1 мин)
```bash
# Показать что всё поднялось автоматически
docker-compose -f docker-compose.codespaces.yml ps

# Показать что БД готова
docker-compose -f docker-compose.codespaces.yml exec postgres \
  psql -U postgres -d pharmaviyum -c "SELECT COUNT(*) FROM pg_tables;"
```

### 2. Демо Swagger UI (1 мин)
- Открыть https://your-codespace-8000.app.github.dev/docs
- Показать все эндпоинты: `/query`, `/query/stream`, `/health`, `/metrics`

### 3. Демо Drug Interaction (2 мин)
- В Swagger: `POST /api/v1/ai/query`
- Запрос: "What are the interactions between Warfarin and Aspirin?"
- Показать структурированный ответ с источниками и степенью опасности

### 4. Демо Halal Compliance (1 мин)
- Запрос на арабском: "هل يمكنني تناول كبسولات الأموكسيسيلين؟"
- Показать ответ с учётом фиква Sistani

### 5. Показ Streaming (1 мин)
```bash
curl -N -X POST "https://your-codespace-8000.app.github.dev/api/v1/ai/query/stream" \
  -H "Content-Type: application/json" \
  -d '{"query":"What is Paracetamol dosage?","session_id":"demo","country":"VN","language":"en"}'
```

### Ключевые фразы для резюме
> *"Deployed production-ready AI system in GitHub Codespaces with cloud LLM integration (Groq), demonstrating zero-GPU deployment capability and enterprise-grade scalability."*

---

## 🔗 Полезные ссылки

- **Groq Console:** https://console.groq.com
- **GitHub Codespaces Docs:** https://docs.github.com/en/codespaces
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **PostgreSQL + pgvector:** https://github.com/pgvector/pgvector
- **Redis Docs:** https://redis.io/docs

---

## ❓ Часто задаваемые вопросы

**Q: Будут ли мои данные сохранены если Codespace остановится?**
A: Да! Volumes (PostgreSQL, Redis, файлы) сохраняются даже когда Codespace off. Просто откройте его заново.

**Q: Сколько денег это будет стоить?**
A: Codespaces бесплатны до 120 часов/месяц (или 180 ядро-часов). Groq даёт 14,400 бесплатных запросов. Итого: **полностью бесплатно** для разработки.

**Q: Можно ли использовать вместо Groq другой LLM?**
A: Да! Обновите `.env`:
- OpenAI: `OPENAI_API_KEY=...`
- Anthropic: `ANTHROPIC_API_KEY=...`

Код автоматически выберет нужного провайдера.

**Q: Где находятся логи?**
A: 
```bash
# FastAPI (основное приложение)
docker-compose -f docker-compose.codespaces.yml logs -f api

# Все сервисы
docker-compose -f docker-compose.codespaces.yml logs -f
```

**Q: Как обновить зависимости?**
A:
```bash
pip install -r requirements-ai.txt --upgrade
```

---

## ✅ Чек-лист запуска

- [ ] Создан Codespace (4-core machine)
- [ ] Получен Groq API ключ
- [ ] `.env` заполнен с `GROQ_API_KEY`
- [ ] Запущен setup скрипт (автоматически)
- [ ] PostgreSQL + Redis healthy
- [ ] FastAPI запущен (port 8000)
- [ ] Swagger UI открыт
- [ ] Пробный запрос работает
- [ ] Видны логи и metrics

---

**🚀 Готово! Ваша Pharmaviyum AI система работает в облаке!**

Для вопросов или проблем откройте GitHub Issue.
