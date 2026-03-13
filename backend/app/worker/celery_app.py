"""
Celery worker configuration for async job processing.
"""
import logging
import json
from pathlib import Path
from celery import Celery

from app.config import settings

logger = logging.getLogger(__name__)

celery = Celery(
    "audio_translation",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.worker.celery_app"]
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,       # One job at a time per worker
    task_acks_late=True,                # Acknowledge only after completion
    task_reject_on_worker_lost=True,
)


@celery.task(bind=True, name="process_job", max_retries=2, soft_time_limit=3600)
def process_job_task(self, job_id: str):
    """
    Main Celery task: runs the full translation pipeline for a job.
    """
    from app.models.job import Job
    from app.pipeline.orchestrator import run_pipeline

    # Load job from disk
    job_file = Path(settings.output_dir) / job_id / "job.json"
    if not job_file.exists():
        raise FileNotFoundError(f"Job file not found: {job_file}")

    with open(job_file) as f:
        job = Job.model_validate_json(f.read())

    def on_progress(updated_job: Job):
        # Update task state for frontend polling
        self.update_state(
            state="PROGRESS",
            meta={
                "job_id": job_id,
                "progress_pct": updated_job.progress_pct,
                "status": updated_job.status.value,
            }
        )
        # Persist to disk
        with open(job_file, "w") as f:
            f.write(updated_job.model_dump_json(indent=2))

    logger.info(f"[Celery] Starting pipeline for job {job_id}")
    result = run_pipeline(job, on_progress=on_progress)
    logger.info(f"[Celery] Pipeline done for job {job_id} — status: {result.status}")

    return {"job_id": job_id, "status": result.status.value}
