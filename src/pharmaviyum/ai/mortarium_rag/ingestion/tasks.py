            source = source_info["source"]
            source_type = source_info["source_type"]
            try:
                child_config = {**config, "batch_job_id": job_id}
                task = ingest_document.delay(
                    source, source_type, f"{job_id}_doc_{index}", child_config
                )
                results.append(
                    {"source": source, "task_id": task.id, "status": "queued"}
                )
            except Exception:
                failed += 1
                loop.run_until_complete(tracker.record_batch_result(job_id, False))
                results.append(
                    {"source": source, "status": "failed", "error": "Queue dispatch failed"}
                )

        if failed == 0:
            loop.run_until_complete(
                tracker.update_status(
                    job_id,