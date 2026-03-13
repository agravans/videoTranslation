"""
Pipeline Orchestrator
Runs all pipeline stages in sequence for a given job.
Used by both the Celery worker and the CLI script.
"""
import logging
from pathlib import Path
from typing import Optional

from app.models.job import Job, JobStatus, StageStatus, ProcessingTier, Language
from app.config import settings
from app.pipeline.ingest import extract_audio, validate_video
from app.pipeline.transcribe import transcribe_audio
from app.pipeline.translate import translate_transcript
from app.pipeline.qa import run_qa_check
from app.pipeline.tts import generate_tts_audio
from app.pipeline.sync_audio import build_dubbed_video
from app.pipeline.subtitle import generate_srt, generate_source_srt, burn_subtitles

logger = logging.getLogger(__name__)


def run_pipeline(job: Job, on_progress=None) -> Job:
    """
    Run the full translation pipeline for a job.
    on_progress(job) is called after each stage completes.
    """
    def progress(stage_name: str, status: StageStatus, pct: int, meta: dict = None, error: str = None):
        job.update_stage(stage_name, status, error=error, meta=meta or {})
        job.progress_pct = pct
        if on_progress:
            on_progress(job)

    try:
        job.status = JobStatus.PROCESSING

        # ── Stage 1: Ingest ─────────────────────────────────────────
        progress("ingest", StageStatus.RUNNING, 5)
        validate_video(job.input_video_path, settings.max_video_size_mb)
        ingest_result = extract_audio(
            job.input_video_path,
            output_dir=str(Path(settings.output_dir) / job.id)
        )
        job.extracted_audio_path = ingest_result["audio_path"]
        job.duration_seconds = ingest_result["duration_seconds"]
        progress("ingest", StageStatus.DONE, 15, meta={"duration_s": job.duration_seconds})

        # ── Stage 2: Transcription ────────────────────────────────────
        progress("transcribe", StageStatus.RUNNING, 20)
        job.transcript = transcribe_audio(job.extracted_audio_path)
        progress("transcribe", StageStatus.DONE, 35, meta={"segments": len(job.transcript)})

        # Save source SRT
        src_srt_path = str(Path(settings.output_dir) / job.id / "source_en.srt")
        generate_source_srt(job.transcript, src_srt_path)
        job.output_paths["en-srt"] = src_srt_path

        # ── Stages 3-7: Per-language pipeline ─────────────────────────
        n_langs = len(job.target_languages)
        for lang_idx, lang in enumerate(job.target_languages):
            lang_code = lang.value
            base_pct = 35 + int((lang_idx / n_langs) * 55)

            # Stage 3: Translate
            progress(f"translate:{lang_code}", StageStatus.RUNNING, base_pct + 2)
            translated_segs = translate_transcript(job.transcript, lang)

            # Stage 4: QA
            progress(f"qa:{lang_code}", StageStatus.RUNNING, base_pct + 5)
            translated_segs = run_qa_check(translated_segs, lang)
            job.translations[lang_code] = translated_segs

            critical_flags = [s for s in translated_segs if any("critical" in f.lower() for f in s.qa_flags)]
            progress(f"qa:{lang_code}", StageStatus.DONE, base_pct + 8,
                     meta={"critical_flags": len(critical_flags)})

            # Generate SRT (always — even for Starter tier)
            srt_path = str(Path(settings.output_dir) / job.id / lang_code / "subtitles.srt")
            generate_srt(translated_segs, srt_path)
            job.output_paths[f"{lang_code}-srt"] = srt_path
            progress(f"subtitle:{lang_code}", StageStatus.DONE, base_pct + 10)

            # Stage 5-6: TTS + Sync (Standard and Premium tiers only)
            if job.tier in (ProcessingTier.STANDARD, ProcessingTier.PREMIUM):
                progress(f"tts:{lang_code}", StageStatus.RUNNING, base_pct + 12)
                tts_segments = generate_tts_audio(
                    translated_segs,
                    lang,
                    output_dir=settings.output_dir,
                    job_id=job.id
                )
                progress(f"tts:{lang_code}", StageStatus.DONE, base_pct + 20)

                progress(f"sync:{lang_code}", StageStatus.RUNNING, base_pct + 22)
                dubbed_video_path = str(
                    Path(settings.output_dir) / job.id / lang_code / "dubbed_video.mp4"
                )
                build_dubbed_video(
                    original_video_path=job.input_video_path,
                    tts_segments=tts_segments,
                    output_path=dubbed_video_path
                )
                job.output_paths[f"{lang_code}-dubbed"] = dubbed_video_path
                progress(f"sync:{lang_code}", StageStatus.DONE, base_pct + 30)

                # Burn subtitles into dubbed video
                final_video_path = str(
                    Path(settings.output_dir) / job.id / lang_code / "final_with_subs.mp4"
                )
                burn_subtitles(dubbed_video_path, srt_path, final_video_path)
                job.output_paths[f"{lang_code}-final"] = final_video_path

            # Lip sync — Premium tier only (placeholder: VEED API integration)
            if job.tier == ProcessingTier.PREMIUM:
                logger.info(f"[{lang_code}] Lip sync: VEED API integration pending")
                progress(f"lipsync:{lang_code}", StageStatus.SKIPPED, base_pct + 35,
                         meta={"reason": "VEED API integration — see docs/lip_sync.md"})

        # ── Complete ──────────────────────────────────────────────────
        job.status = JobStatus.AWAITING_REVIEW
        job.progress_pct = 95
        if on_progress:
            on_progress(job)

        logger.info(f"Pipeline complete for job {job.id}. Awaiting human review.")
        return job

    except Exception as e:
        logger.error(f"Pipeline failed for job {job.id}: {e}", exc_info=True)
        job.status = JobStatus.FAILED
        job.error = str(e)
        if on_progress:
            on_progress(job)
        raise
