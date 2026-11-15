# ADR-0003: Привязка состояния диалога Mortarium к пациенту

## Статус

Proposed — реализация была влита в `main` через [PR #287](https://github.com/Akil-Ibrahim/Pharmaviyum-ERP/pull/287) (merge commit `4d761990b31ef3aa78327dda1380689f2d094e8f`). ADR остаётся в статусе Proposed, поскольку требуемая поэтапная end-to-end проверка и production rollout не подтверждены. Merge и успешный CI не доказывают активацию в production или клиническую безопасность.

## Контекст

До PR #287 Mortarium использовал аутентифицированный pharmacy context, Agent Harness с Redis dialogue memory и два LangGraph workflow с checkpoint persistence, но API session и checkpoint identities не были последовательно связаны с идентичностью пациента. Повторное использование client session при переключении пациентов могло привести к повторному использованию прежнего диалога или checkpoint state.

Одних patient retrieval filters недостаточно: memory и graph checkpoints — отдельные хранилища состояния.

## Предлагаемое решение

Формировать namespace каждого диалога, содержащего patient context, из аутентифицированного server-side набора:

**pharmacy_id + authenticated_user_id + patient_id + client_session_id**

Запрос без пациента должен использовать явную область no-patient, а не wildcard. Для сохранённых session/checkpoint identifiers использовать версионируемый keyed HMAC digest, чтобы не раскрывать raw tenant, user, patient и session IDs в именах ключей. HMAC secret должен оставаться стабильным между экземплярами приложения и deployment.

Одинаковый контракт идентичности применять к synchronous и streaming AI endpoints, Redis dialogue memory и derived summaries, Agent checkpoints, RAG checkpoints и cache entries, влияющим на ответы для конкретного пациента.

API должен аутентифицировать вызывающего, определять tenant membership и проверять patient membership до формирования scope. Переданный клиентом patient ID — только selector, а не доказательство авторизации.

## Требования безопасности и корректности

- Области Patient A, Patient B и явная no-patient остаются раздельными при повторном использовании client session ID.
- Области разных pharmacies и users не пересекаются.
- Неверные patient/session identifiers отклоняются валидацией.
- В staging/production отсутствие HMAC secret приводит к fail-closed.
- Cache reuse не пересекает patient contexts.
- Logs, traces и metrics не раскрывают raw identifiers или clinical content.
- Тесты охватывают оба API режима, memory, Agent/RAG checkpoints и cache behavior.

## Совместимость и rollout

Изменение namespace намеренно делает старые memory/checkpoint keys недоступными, если миграция отдельно не утверждена.

До production rollout:

1. Подтвердите Redis memory TTL и retention.
2. Определите проверенный retention/deletion plan для legacy plaintext checkpoint rows и backups; не удаляйте их автоматически.
3. Подтвердите secret distribution и rotation policy.
4. Запустите session-switch tests Patient A → Patient B → no-patient в streaming и non-streaming режимах.
5. Проверьте PostgreSQL checkpoint persistence и Redis memory на изолированных тестовых сервисах.
6. Опишите rollback. Возврат старого кода может снова открыть прежнюю семантику namespace и требует осознанной оценки риска.

## Рассмотренные альтернативы

- Только patient ID в retrieval filters: недостаточно, поскольку не изолирует dialogue memory и graph checkpoints.
- Создание новой session при каждом переключении пациента: полезная UI-защита, но не backend security boundary.
- Plaintext composite IDs: раскрывают идентификаторы и провоцируют несогласованное формирование ключей.
- Автоматическое удаление старых checkpoints: отклонено до анализа ownership, retention и последствий для backups.

## Статус реализации

PR #287 добавил в `main` API session HMAC v3, patient-aware Agent/RAG checkpoint IDs, строгую валидацию и regression tests. Для merge commit прошли проверки RAG Safety Regression, Unit Tests и Integration Tests. Эти автоматические проверки не заменяют оставшийся staged release gate: повторное использование одной client session для Patient A → Patient B → no patient в streaming и non-streaming путях с проверкой изоляции на PostgreSQL checkpoint persistence и Redis memory.

В этом документе нет доказательств выполнения такой staged-проверки или production deployment. ADR не разрешает миграцию production data или удаление legacy checkpoints.

## Ссылки

- [Аудит Mortarium RAG](../rag_architecture_audit.ru.md)
- [Архитектура AI](../ai_architecture.ru.md)
- [PR #287](https://github.com/Akil-Ibrahim/Pharmaviyum-ERP/pull/287)
