"""
Jobs API — CRUD + file upload + review endpoints
"""
import os
import uuid
import json
import logging
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse

from app.models.job import (
    Job, JobCreateRequest, JobStatus, StageStatus,
    Language, ProcessingTier, TranslatedSegment
)
from app.config import settings
from app.worker.celery_app import process_job_task

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/jobs", tags=["jobs"])

# In-memory job store for POC (replace with Redis/DB in production)
_jobs: dict[str, Job] = {}


def _save_job(job: Job):
    _jobs[job.id] = job
    # Persist to disk for recovery
    job_file = Path(settings.output_dir) / job.id / "job.json"
    job_file.parent.mkdir(parents=True, exist_ok=True)
    with open(job_file, "w") as f:
        f.write(job.model_dump_json(indent=2))


def _load_job(job_id: str) -> Job:
    if job_id in _jobs:
        return _jobs[job_id]
    job_file = Path(settings.output_dir) / job_id / "job.json"
    if not job_file.exists():
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    with open(job_file) as f:
        return Job.model_validate_json(f.read())


@router.post("/", response_model=Job, status_code=201)
async def create_job(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    target_languages: str = Form(...),   # comma-separated, e.g. "hi-IN,ta-IN"
    tier: str = Form(default="standard"),
    client_name: Optional[str] = Form(default=None),
    notes: Optional[str] = Form(default=None),
):
    """Upload a video and create a translation job."""
    # Parse languages
    lang_codes = [l.strip() for l in target_languages.split(",")]
    try:
        langs = [Language(code) for code in lang_codes]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid language code: {e}")

    # Validate tier
    try:
        tier_enum = ProcessingTier(tier)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid tier: {tier}. Use: starter/standard/premium")

    # Save uploaded video
    job_id = str(uuid.uuid4())
    upload_dir = Path(settings.upload_dir) / job_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    video_filename = file.filename or f"input_{job_id}.mp4"
    video_path = upload_dir / video_filename

    with open(video_path, "wb") as f:
        content = await file.read()
        f.write(content)

    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.max_video_size_mb:
        video_path.unlink()
        raise HTTPException(status_code=413, detail=f"File too large: {size_mb:.1f}MB > {settings.max_video_size_mb}MB")

    # Create job
    job = Job(
        id=job_id,
        title=title,
        target_languages=langs,
        tier=tier_enum,
        client_name=client_name,
        notes=notes,
        input_video_path=str(video_path),
    )
    _save_job(job)

    # Dispatch async task
    background_tasks.add_task(_dispatch_job, job_id)

    logger.info(f"Job created: {job_id} ({title}) → {lang_codes}")
    return job


async def _dispatch_job(job_id: str):
    """Dispatch job to Celery worker (or run inline for dev)."""
    try:
        process_job_task.delay(job_id)
    except Exception as e:
        logger.warning(f"Celery unavailable, running inline: {e}")
        # Fallback: run synchronously (dev mode)
        from app.pipeline.orchestrator import run_pipeline
        job = _load_job(job_id)
        updated = run_pipeline(job, on_progress=_save_job)
        _save_job(updated)


@router.get("/", response_model=List[Job])
def list_jobs():
    """List all jobs."""
    # Load from disk to catch any jobs not in memory
    output_root = Path(settings.output_dir)
    jobs = []
    for job_file in output_root.glob("*/job.json"):
        try:
            with open(job_file) as f:
                jobs.append(Job.model_validate_json(f.read()))
        except Exception:
            pass
    return sorted(jobs, key=lambda j: j.created_at, reverse=True)


@router.get("/{job_id}", response_model=Job)
def get_job(job_id: str):
    """Get job status and details."""
    return _load_job(job_id)


@router.delete("/{job_id}", status_code=204)
def delete_job(job_id: str):
    """Delete a job and its files."""
    job = _load_job(job_id)
    import shutil
    for path in [
        Path(settings.upload_dir) / job_id,
        Path(settings.output_dir) / job_id,
    ]:
        if path.exists():
            shutil.rmtree(path)
    _jobs.pop(job_id, None)


@router.get("/{job_id}/download/{output_key}")
def download_output(job_id: str, output_key: str):
    """Download a specific output file (e.g., hi-IN-srt, hi-IN-dubbed)."""
    job = _load_job(job_id)
    file_path = job.output_paths.get(output_key)
    if not file_path or not Path(file_path).exists():
        raise HTTPException(status_code=404, detail=f"Output '{output_key}' not found")
    return FileResponse(file_path, filename=Path(file_path).name)


# ── Review API ──────────────────────────────────────────────────────────────

@router.get("/{job_id}/review/{lang_code}")
def get_review_data(job_id: str, lang_code: str):
    """Get translation segments for human review, side-by-side."""
    job = _load_job(job_id)
    segments = job.translations.get(lang_code, [])
    if not segments:
        raise HTTPException(status_code=404, detail=f"No translations for {lang_code}")

    return {
        "job_id": job_id,
        "lang_code": lang_code,
        "status": job.status,
        "segments": [s.model_dump() for s in segments],
        "qa_summary": {
            "total": len(segments),
            "flagged": sum(1 for s in segments if s.qa_flags),
            "approved": sum(1 for s in segments if s.reviewer_approved),
        }
    }


@router.patch("/{job_id}/review/{lang_code}/segment/{segment_id}")
def update_segment(
    job_id: str,
    lang_code: str,
    segment_id: int,
    body: dict
):
    """
    Reviewer updates a translated segment.
    Body: {"reviewed_text": "...", "approved": true}
    """
    job = _load_job(job_id)
    segments = job.translations.get(lang_code, [])
    for seg in segments:
        if seg.id == segment_id:
            if "reviewed_text" in body:
                seg.reviewer_edited = body["reviewed_text"]
            if "approved" in body:
                seg.reviewer_approved = body["approved"]
            _save_job(job)
            return seg.model_dump()

    raise HTTPException(status_code=404, detail=f"Segment {segment_id} not found")


@router.post("/{job_id}/review/{lang_code}/approve-all")
def approve_all_segments(job_id: str, lang_code: str):
    """Approve all segments for a language (bulk approve)."""
    job = _load_job(job_id)
    segments = job.translations.get(lang_code, [])
    for seg in segments:
        seg.reviewer_approved = True
    _save_job(job)
    return {"approved": len(segments)}


@router.post("/{job_id}/review/complete")
def complete_review(job_id: str):
    """
    Mark review as complete — triggers final SRT regeneration
    from any reviewer edits and marks job as ready.
    """
    job = _load_job(job_id)
    if job.status != JobStatus.AWAITING_REVIEW:
        raise HTTPException(status_code=400, detail="Job is not awaiting review")

    from app.pipeline.subtitle import generate_srt
    # Regenerate SRTs with reviewer edits
    for lang_code, segments in job.translations.items():
        srt_path = job.output_paths.get(f"{lang_code}-srt")
        if srt_path:
            generate_srt(segments, srt_path)

    job.status = JobStatus.COMPLETED
    from datetime import datetime
    job.completed_at = datetime.utcnow()
    job.progress_pct = 100
    _save_job(job)

    return {"status": "completed", "job_id": job_id}
