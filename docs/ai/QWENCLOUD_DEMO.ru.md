# Демо Mortarium AI: провайдер QwenCloud и защита квоты

**Статус:** адаптер провайдера и fail-closed application guard присутствуют в `main`. Документ описывает демонстрационный профиль конфигурации, а не подтверждение live- или production-развёртывания.  
**Область действия:** только demo environment. В документе различаются реализованный код и запланированные меры; запланированная мера не является эксплуатационной гарантией.

## 1. Цели и границы демо

Демо использует **QwenCloud как единственного cloud LLM provider** с настроенной моделью `qwen3.8-flash`. OpenRouter и дополнительные LLM-provider fallbacks намеренно исключены.

Демо должно:
- оставаться в пределах бесплатной квоты провайдера и предотвращать случайное платное использование;
- fail closed, если приложение явно не настроено на режим free-quota-only;
- ограничивать timeout, размер output и обеспечивать наблюдаемость token usage;
- сохранять независимость ERP/POS transaction path от доступности LLM;
- позволять выбирать модель конфигурацией без переписывания LangGraph;
- рассматривать embeddings как отдельную функцию с отдельными credentials и quota;
- использовать только синтетические/demo данные, пока privacy, security и contractual controls для реальных данных пациентов не утверждены.

Это demo profile, а не обещание безлимитной бесплатной ёмкости, доступности или квоты. Квотой и сроком действия управляет провайдер; проверяйте их в его консоли.

## 2. Контракт конфигурации

Настраивайте эти secrets только в изолированном FastAPI Cloud Demo environment, никогда не помещайте их в source control, issue comments или logs. Production provider credentials управляются отдельно за пределами публичного репозитория.

| Переменная | Demo value / назначение |
|---|---|
| `USE_CLOUD_LLM` | `true` |
| `CLOUD_LLM_PROVIDER` | `qwencloud` |
| `QWEN_API_KEY` | Секретный API key QwenCloud |
| `QWEN_BASE_URL` | `https://ap-southeast-1.maas.qwencloudapi.com/compatible-mode/v1` |
| `QWEN_MODEL` | `qwen3.8-flash` |
| `QWEN_FAST_MODEL` | `qwen3.8-flash` |
| `QWEN_COMPLEX_MODEL` | `qwen3.8-flash` |
| `QWEN_FREE_QUOTA_ONLY` | `true` для инициализации адаптера; по умолчанию `false` |
| `QWEN_TIMEOUT_SECONDS` | `30` |
| `QWEN_MAX_OUTPUT_TOKENS` | `500` |

Адаптер Qwen использует OpenAI-compatible LangChain client. Retries отключены; запросы имеют ограниченные timeout и output-token budget. Если API credentials отсутствуют или `QWEN_FREE_QUOTA_ONLY=false`, адаптер Qwen не создаётся.

**Необходимы два независимых controls:**

1. Application guard: адаптер требует `QWEN_FREE_QUOTA_ONLY=true`.
2. Provider guard: включите **Free quota only** в консоли QwenCloud для выбранной модели.

Флаг приложения не запрашивает квоту провайдера и сам по себе не обеспечивает enforcement billing policy. Настройка в консоли провайдера является авторитетным ограничением платного использования.

## 3. Текущий статус реализации

| Возможность | Статус | Примечание |
|---|---|---|
| QwenCloud provider adapter | Реализовано в `main` | OpenAI-compatible LangChain `ChatOpenAI` adapter |
| Выбор модели конфигурацией | Реализовано в `main` | Fast/main/complex model settings; смена ID не требует переписывания LangGraph |
| Fail-closed application free-quota flag | Реализовано в `main` | По умолчанию false; адаптер не инициализируется без явного включения |
| Ограниченные timeout и output tokens | Реализовано в `main` | Retries отключены |
| Token-usage callback/metrics | Реализация есть; end-to-end telemetry требует проверки | Это operational telemetry, не авторитетный quota ledger |
| Provider-console Free quota only | Ручное требование оператора | Нужно включить и проверить в консоли QwenCloud |
| Per-request prompt/token budget | Уже реализовано | Ограничивает размер prompt, но не является дневной квотой провайдера |
| Общий дневной Redis token cap | Запланировано, ещё не реализовано | Требует атомарного резервирования до вызова provider и сверки фактического usage |
| Concurrency-safe quota reservation | Запланировано, ещё не реализовано | Должно работать между всеми API/worker replicas |
| Классификация ошибок провайдера | Запланировано, ещё не реализовано | Различать authentication, permission, quota/rate-limit, timeout и provider/server failures |
| Provider circuit breaker / cooldown | Запланировано, ещё не реализовано | Предотвращать повторные вызовы при outage или исчерпании квоты |
| Проверка quota expiry/renewal | Ручной процесс; автоматизация отсутствует | Перед демо проверять баланс, срок и условия в консоли |
| Автоматический LLM fallback | Намеренно отключён | Нет OpenRouter или платного provider fallback |

Не называйте запланированные controls активными, пока не проверены код, тесты и deployment configuration.

## 4. Целевой поток запроса и контроля квоты

Предполагаемый строгий demo flow:

1. Проверить, что Qwen provider включён и application configuration free-quota-only равна true.
2. Проверить состояние provider circuit и локальный demo budget.
3. До внешнего вызова атомарно зарезервировать оценочный token allowance в общем Redis.
4. Отклонить AI request, если Redis недоступен в strict mode, бюджет исчерпан или circuit открыт.
5. Вызвать QwenCloud с ограниченными timeout/output tokens и без автоматических retries.
6. При успехе сохранить usage от провайдера и сверить reservation.
7. При ошибке освободить или консервативно учесть reservation с учётом вероятности обработки запроса провайдером; классифицировать ошибку и обновить circuit state.
8. Вернуть контролируемый ответ AI-unavailable. Не блокировать и не откатывать независимые POS/database transactions из-за ошибки AI.

Redis quota accounting — application-level safety budget. Он не заменяет billing/free-quota enforcement в консоли QwenCloud. Неизвестный usage нужно учитывать консервативно, а не считать нулём.

### Целевая политика ошибок

| Ошибка | Целевое поведение |
|---|---|
| 401 / неверный key | Остановить retries; сообщить оператору о конфигурации; без fallback |
| 403 / нет разрешения или доступа к модели | Остановить retries; требуется действие оператора |
| 429 / quota или rate limit | Открыть cooldown/circuit; отклонять новые AI calls до безопасного повтора; без платного fallback |
| Timeout / connection failure | Ограниченная ошибка; консервативный учёт reservation; circuit protection |
| 5xx provider failure | Ограниченная ошибка и cooldown; без автоматической смены provider |
| Redis unavailable | Fail closed для Qwen calls при включённом strict quota mode |
| Локальный дневной бюджет исчерпан | Отклонять новую генерацию до сброса бюджетного окна |

Коды ответов и структурированные error bodies необходимо сверить с реальным QwenCloud API до завершения реализации классификации.

## 5. RAG и embeddings — отдельные компоненты

В этом demo QwenCloud является **generation provider**. Он автоматически не настраивает embedding model.

Cloud embedding path конфигурируется отдельно. До заявления о работоспособности cloud RAG проверьте:
- настроены embedding provider и model;
- runtime располагает embedding API key;
- embedding dimensions соответствуют схеме pgvector;
- ingestion и retrieval tests проходят;
- tenant, pharmacy и patient filters продолжают применяться.

Не отправляйте patient-identifiable или другие чувствительные данные в free-tier endpoint без утверждённого privacy/security основания и проверки условий провайдера.

## 6. Операции с квотой и сроком действия

Перед каждым demo release/session:

- проверьте QwenCloud project, region, выбранную модель, остаток free quota и expiry date;
- убедитесь, что в provider console включён **Free quota only**;
- проверьте ожидаемые Qwen environment variables в приложении FastAPI Cloud Demo, не раскрывая значения секретов;
- выполните небольшой synthetic smoke test и изучите token-usage telemetry;
- остановите demo AI calls, если квота исчерпана или free-quota entitlement истёк.

Не предполагайте, что бесплатная квота автоматически обновляется. После истечения entitlement снова проверьте консоль и актуальные условия. Не переключайтесь незаметно на платный план или другого провайдера.

## 7. Проверки и release gates

PR #244 нельзя объединять, пока:
- backend lint, formatting, type checks и unit tests не пройдут;
- frontend CI и security scans не пройдут;
- focused tests не покрывают missing key, отключённый free-quota guard, model configuration, usage extraction, budget reservation/reconciliation и provider error handling по мере реализации этих controls;
- provider smoke test не выполняется только с явно одобренным demo key и включённым provider-console free-only guard.

Успешный CI не доказывает, что live provider key, free quota, embedding service или production deployment настроены корректно.

Работа над PR не меняет production environment variables, production database, migrations или deployment. Merge и deployment требуют отдельного явного разрешения.

## 8. Связанная документация

- [Runbook FastAPI Cloud](../deployment/FASTAPI_CLOUD.ru.md)
- [Архитектура AI](../ai_architecture.ru.md)
- [Аудит архитектуры RAG](../rag_architecture_audit.ru.md)
- [Требования к инженерному benchmark](../devops/ENGINEERING_BENCHMARK_REQUIREMENTS.md)
- [PR #244](https://github.com/Akil-Ibrahim/Pharmaviyum-ERP/pull/244)
