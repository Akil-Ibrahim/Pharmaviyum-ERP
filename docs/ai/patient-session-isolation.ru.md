# Изоляция состояния диалогов Mortarium по пациентам

**Статус:** PR #287 влит в `main` (merge commit `4d761990b31ef3aa78327dda1380689f2d094e8f`). Staged end-to-end validation и Production activation не подтверждены; этот документ не является доказательством deployment.

## Область действия

Состояние диалога Mortarium изолируется по кортежу:

`pharmacy_id + authenticated user_id + patient_id + purpose + client session_id`

Отсутствие пациента является отдельной областью `patient:none`. Это не wildcard и такая сессия никогда не должна разделять состояние с диалогом, привязанным к конкретному пациенту.

## Точки применения контроля

1. **Граница API** — синхронный `/api/v1/ai/query` и потоковый `/api/v1/ai/query/stream` формируют одинаковую версионированную внутреннюю область сессии после авторизации tenant, проверки принадлежности пациента аптеке и controlled-purpose validation. Patient-bound sessions используют purpose-bound HMAC namespace (`mortarium-session:v4`), поэтому смена purpose не переиспользует memory/checkpoints предыдущей цели.
2. **Память диалога Redis** — ключи памяти выводятся через HMAC из API-scoped идентификатора сессии. Поэтому сводка, краткосрочные сообщения, архив и эпизодические факты наследуют область пациента.
3. **Agent checkpoint** — `PharmacistAgent._thread_id()` включает аутентифицированные аптеку, пользователя, пациента и область сессии во входные данные HMAC.
4. **RAG checkpoint** — `LangGraphRAG._thread_id()` включает аптеку, пользователя, пациента и область сессии во входные данные HMAC. Сохраняемый идентификатор thread checkpoint является непрозрачным digest `rag:v2:<sha256>`.
5. **Prompt cache** — точная идентичность кеша включает полный контекст запроса; область semantic cache также включает ID пациента и рецепта и остаётся opt-in только для явно безопасных запросов без данных пациента.

## Инварианты безопасности

- Повторное использование одного client session ID для пациента A и пациента B НЕ ДОЛЖНО приводить к повторному использованию памяти, Agent checkpoints, RAG checkpoints или кешированных ответов.
- Пациент A и запрос без пациента ДОЛЖНЫ использовать разные namespace состояния.
- AI API принимает выбранного пациента только после проверки active ownership в аутентифицированной аптеке и требует вместе с ним контролируемую purpose. Trusted MCP context переносит оба значения через registry dispatch. `get_patient_history` требует точного совпадения patient ID из аргумента модели с выбранным пациентом, повторно проверяет active pharmacy ownership и записывает metadata-only allowed/denied `PHIAccessAudit` до возврата данных. Unit tests покрывают mismatch, отсутствие purpose, отказ по роли, propagation context и ошибку commit аудита. Ответ пока шире целевого minimum-necessary набора; database-backed MCP audit tests, DB-role hardening и staged end-to-end validation остаются открытыми. HMAC session/checkpoint namespaces не заменяют tool-level authorization.
- Прямое создание Agent/RAG checkpoint также проверяет формат ID пациента и включает его в HMAC scope checkpoint.
- Необработанные идентификаторы пациента, пользователя, tenant и сессии НЕ ДОЛЖНЫ присутствовать в RAG checkpoint thread ID.
- `SECRET_KEY` приложения должен оставаться стабильным между экземплярами и deployment. Ротация меняет HMAC-derived namespace checkpoint и памяти и требует заранее спланированной стратегии миграции/истечения срока действия.
- Телеметрия не должна содержать исходные ID пациентов, prompts, completions или клинический контент.

## Совместимость и хранение данных

Формат API-scoped сессии версионирован как `mortarium-session:v3`. Существующие namespace сессий автоматически не мигрируются и не читаются как fallback. Это сознательно отдаёт приоритет изоляции, а не непрерывности: прежняя память Redis может оставаться недоступной для новой области до истечения настроенного TTL.

ID RAG checkpoint теперь используют версионированный HMAC namespace. Существующие записи RAG checkpoint в открытом текстовом формате автоматически не переписываются и не удаляются. До production rollout необходимо определить и выполнить утверждённый план хранения/удаления устаревших строк checkpoint и их резервных копий. Не удаляйте массово checkpoint, не подтвердив владельца данных, требования retention и последствия для rollback.

## Регрессионное покрытие

Набор тестов проверяет:
- одна client session + разные пациенты дают разные API session scopes;
- области с конкретным пациентом и без пациента различаются;
- некорректные идентификаторы пациента/сессии отклоняются;
- MCP tools должны отклонять patient ID, отличный от выбранного patient context, требовать purpose code и надёжно аудировать allowed/denied PHI reads (в текущем MCP context/tool path это ещё не реализовано);
- Agent checkpoint ID различаются по пациентам и отклоняют некорректный контекст пациента;
- RAG checkpoint ID различаются по пациенту, tenant и secret; скрывают исходные идентификаторы; fail closed при отсутствии production secret.

Перед релизом запустите полный набор AI unit tests, API tests, security tests, integration tests с PostgreSQL checkpoint storage и Redis memory, а также staged end-to-end тест, который переключает одну client session между пациентом A → пациентом B → отсутствием пациента в потоковом и обычном режимах.

## Эксплуатационные границы

Это изменение затрагивает только код приложения. Оно не мигрирует, не удаляет и не проверяет данные production Redis/PostgreSQL checkpoint, не меняет production secrets и не развертывает приложение. Это не клиническая валидация и не регуляторная сертификация.
