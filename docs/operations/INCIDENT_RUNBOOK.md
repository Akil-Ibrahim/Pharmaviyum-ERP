# Incident Runbook

## Fast triage

### API is unavailable
1. Check the latest deployment and CI result.
2. Check `/health`.
3. Check `/ready`.
4. If `/ready` reports PostgreSQL or Redis failure, restore the dependency before restarting application replicas.
5. If the failure started after a release, roll back to the previous immutable image.

### API is slow
1. Check request latency metrics.
2. Separate API, database, RAG retrieval, tool-call, and LLM latency.
3. Check database saturation and Redis health.
4. If only LLM/RAG latency is elevated, reduce concurrency or route to the configured fast model if the product policy permits.

### RAG answers are wrong
1. Preserve the request ID and relevant trace.
2. Determine whether the failure is retrieval, grading, rewriting, or generation.
3. Verify that ungraded/low-quality documents are not reaching generation.
4. Add the failing case to the regression evaluation set.
5. Fix and verify before re-enabling rollout.

### Security incident
1. Stop the rollout.
2. Rotate affected credentials immediately.
3. Preserve audit logs and traces.
4. Identify affected requests/data without copying sensitive payloads into tickets.
5. Patch, add a regression test, and deploy through the normal gates.

## Rollback rule

Rollback is preferred to live debugging when customer impact is material and the current release is the most likely cause. Roll back the immutable image first, then investigate.
