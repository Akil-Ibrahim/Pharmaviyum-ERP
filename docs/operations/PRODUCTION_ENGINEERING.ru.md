# Стандарт Production Engineering — Pharmaviyum ERP/CRM

Документ определяет минимальный эксплуатационный контракт Pharmaviyum CRM. Он строже, чем workflow только для разработки.

## 1. Контракт надёжности

### Целевые показатели сервиса

- **Целевая доступность:** 99,9% в месяц для API.
- **Целевая API latency:** p95 < 1,5 секунды для endpoints без LLM.
- **Целевая RAG latency:** p95 < 5 секунд при поддерживаемой нагрузке.
- **Error budget:** 43 минуты 12 секунд в месяц при доступности 99,9%.

Это инженерные цели, пока production traffic не сформирует фактические baseline.

### Семантика health checks

- `/health` — только liveness; endpoint должен оставаться дешёвым.
- `/ready` проверяет PostgreSQL, Redis и AI initialization.
- При ошибке readiness возвращается HTTP 503, а не успешный HTTP 200.
- Production startup должен завершаться fail-fast при сбое критической инициализации.

## 2. Контракт deployment

Каждый production release должен следовать процедуре:

1. CI проходит lint, type checking, unit tests, integration tests, dependency audit, Bandit и image build.
2. Database migrations проверяются отдельно от изменений приложения.
3. Миграции выполняются один раз как release operation, а не параллельно из каждой API replica.
4. Новая image запускается только после успешного выполнения migration operation.
5. До переключения traffic endpoint `/ready` должен возвращать 200.
6. Rollback означает повторное развёртывание предыдущего immutable image tag.

Application image **не запускает** `alembic upgrade head` при старте API. Это предотвращает гонки миграций между replicas.

## 3. Наблюдаемость

Обязательные сигналы:

- Structured request logs с correlation/request IDs.
- Prometheus metrics на `/metrics`.
- OpenTelemetry traces при включённой instrumentation.
- RAG retrieval latency и tool-call metrics.
- LLM token/cost metrics, если доступны provider metadata.
- Evaluation score и pass-rate metrics для offline evaluation runs.

Никогда не помещайте secrets, authorization headers, raw patient/customer data или полное содержимое prompts в logs.

## 4. Quality gates RAG

Перед изменением retrieval или generation запускайте evaluation set, содержащий:

- вопросы с ответом, подтверждённым фактами;
- вопросы без достаточных данных для ответа;
- retrieval misses;
- документы с prompt injection;
- multilingual queries;
- safety/compliance cases;
- regression cases ранее исправленных инцидентов.

Релиз не должен сознательно снижать безопасность или groundedness ради увеличения answer rate.

## 5. Security gates

CI считает уязвимости зависимостей и Bandit findings блокирующими ошибками. Исключения требуют явного reviewed suppression с причиной и датой истечения.

Production configuration должна задавать явные CORS origins. Development может оставаться более permissive.

## 6. Реагирование на инциденты

При production incident:

1. Определите категорию: availability, latency, data, security или AI quality.
2. Проверьте `/health`, `/ready`, metrics и последние deployments.
3. Остановите rollout, если подозрение падает на текущий release.
4. При продолжающемся влиянии на пользователей выполните rollback на предыдущую immutable image.
5. Сохраните необходимые logs/traces/metrics.
6. Если причиной был код, добавьте regression test до закрытия инцидента.

## 7. Управление изменениями

Изменения production behavior выполняются через reviewed commits/PRs. Прямые изменения production infrastructure допустимы только как emergency action.

Ветка `main` — каноническая integration branch публичной Demo. FastAPI Cloud размещает только Demo. Production использует тот же технологический стек приложения, развёрнутый на аптечном сервере через Ansible. Публичные Ansible roles и playbooks определяют контракт автоматизации; реальные Production inventory, per-site secrets, доступ к host и approvals остаются под контролем оператора и никогда не коммитятся. Deployment на аптечном сервере, локальные сервисы БД, health checks, backups/restore, observability и rollback требуют отдельных доказательств приёмки площадки.
