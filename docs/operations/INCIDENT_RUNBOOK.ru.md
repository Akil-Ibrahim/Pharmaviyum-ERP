# Runbook реагирования на инциденты

## Быстрая диагностика

### API недоступен

1. Проверьте последний deployment и результат CI.
2. Проверьте `/health`.
3. Проверьте `/ready`.
4. Если `/ready` сообщает о сбое PostgreSQL или cache/broker dependency, восстановите зависимость до перезапуска application services. Production использует PostgreSQL и Valkey Compose services на аптечном сервере; у Demo собственные изолированные dependencies.
5. Если проблема появилась после Production release, используйте утверждённый Ansible rollback playbook с точным подтверждением выбранных hosts, предыдущим immutable image digest и доказательством совместимости со схемой БД. После rollback проверьте `/ready`. Для Demo используйте только Demo FastAPI Cloud release workflow; не применяйте Production Ansible rollback path.

### API работает медленно

1. Проверьте метрики latency запросов.
2. Разделите задержки API, БД, RAG retrieval, tool calls и LLM.
3. Проверьте saturation базы данных и состояние Redis.
4. Если повышена только LLM/RAG latency, уменьшите concurrency или переключитесь на настроенную fast model, если это допускает продуктовая политика.

### RAG выдаёт неправильные ответы

1. Сохраните request ID и соответствующий trace без чувствительного содержимого.
2. Определите этап сбоя: retrieval, grading, rewriting или generation.
3. Проверьте, что документы с низким качеством или без grading не попадают в generation.
4. Добавьте случай в regression evaluation set.
5. Исправьте и проверьте проблему до возобновления rollout.

### Инцидент безопасности

1. Остановите rollout.
2. Немедленно ротируйте затронутые credentials.
3. Сохраните audit logs и traces.
4. Определите затронутые запросы/данные, не копируя чувствительные payloads в tickets.
5. Подготовьте исправление, добавьте regression test и выполните deployment через обычные release gates.

## Правило rollback

Если влияние на клиентов существенно и наиболее вероятная причина — текущий релиз, rollback предпочтительнее live-debugging. Сначала верните immutable application revision, затем проводите расследование. Откат схемы БД рассматривается отдельно и не выполняется автоматически.
