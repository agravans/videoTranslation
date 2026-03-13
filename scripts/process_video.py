#!/usr/bin/env python3
"""
CLI script for end-to-end video translation pipeline.

Week 1 goal: Process a sample bank training video end-to-end in CLI.
No UI needed yet — just verify the pipeline works.

Usage:
    python scripts/process_video.py --input video.mp4 --languages hi-IN,ta-IN
    python scripts/process_video.py --input video.mp4 --languages hi-IN --mock
    python scripts/process_video.py --input video.mp4 --tier starter --languages hi-IN

Requirements:
    - FFmpeg installed (brew install ffmpeg)
    - .env file in backend/ with API keys
    - pip install -r backend/requirements.txt
"""
import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# Load .env
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / "backend" / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        description="AI L&D Video Translation — CLI Pipeline"
    )
    parser.add_argument("--input", "-i", required=True, help="Input video file path")
    parser.add_argument(
        "--languages", "-l", default="hi-IN",
        help="Comma-separated target languages (e.g. hi-IN,ta-IN). Default: hi-IN"
    )
    parser.add_argument(
        "--tier", "-t", default="standard",
        choices=["starter", "standard", "premium"],
        help="Processing tier. starter=SRT only, standard=+dubbing, premium=+lipsync"
    )
    parser.add_argument(
        "--output-dir", "-o", default="./outputs",
        help="Output directory. Default: ./outputs"
    )
    parser.add_argument(
        "--mock", action="store_true",
        help="Run in mock mode (no real API calls, for testing)"
    )
    parser.add_argument(
        "--whisper-model", default="base",
        choices=["tiny", "base", "small", "medium", "large-v3"],
        help="Whisper model size. 'base' is fastest for testing. Default: base"
    )
    parser.add_argument(
        "--title", default=None,
        help="Video title (used in job metadata)"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Override settings if mock mode
    if args.mock:
        os.environ["MOCK_SARVAM"] = "true"
        os.environ["MOCK_CLAUDE"] = "true"
        logger.info("🔧 Mock mode enabled — no real API calls will be made")

    os.environ["WHISPER_MODEL"] = args.whisper_model
    os.environ["OUTPUT_DIR"] = args.output_dir

    from app.config import settings
    from app.models.job import Job, Language, ProcessingTier

    # Validate input
    input_path = Path(args.input).resolve()
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    # Parse languages
    lang_codes = [l.strip() for l in args.languages.split(",")]
    try:
        languages = [Language(code) for code in lang_codes]
    except ValueError as e:
        logger.error(f"Invalid language code: {e}")
        logger.info(f"Valid codes: {[l.value for l in Language]}")
        sys.exit(1)

    tier = ProcessingTier(args.tier)
    title = args.title or input_path.stem

    logger.info("=" * 60)
    logger.info("AI L&D Video Translation Platform — POC Pipeline")
    logger.info("=" * 60)
    logger.info(f"  Input:     {input_path}")
    logger.info(f"  Title:     {title}")
    logger.info(f"  Languages: {', '.join(lang_codes)}")
    logger.info(f"  Tier:      {tier.value}")
    logger.info(f"  Output:    {args.output_dir}")
    logger.info(f"  Mock:      {args.mock}")
    logger.info("=" * 60)

    # Create job
    job = Job(
        title=title,
        target_languages=languages,
        tier=tier,
        input_video_path=str(input_path),
    )

    # Run pipeline
    from app.pipeline.orchestrator import run_pipeline

    start_time = time.time()
    last_stage = [None]

    def on_progress(updated_job: Job):
        current_stages_done = [s.name for s in updated_job.stages if s.status.value == "done"]
        if current_stages_done and current_stages_done != last_stage[0]:
            last_stage[0] = current_stages_done
            pct = updated_job.progress_pct
            bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
            logger.info(f"[{bar}] {pct}% — {current_stages_done[-1]}")

    try:
        result = run_pipeline(job, on_progress=on_progress)
        elapsed = time.time() - start_time

        logger.info("")
        logger.info("=" * 60)
        logger.info("✅  Pipeline complete!")
        logger.info(f"   Status:    {result.status.value}")
        logger.info(f"   Duration:  {elapsed:.1f}s")
        logger.info(f"   Segments:  {len(result.transcript)}")
        logger.info("")
        logger.info("📁  Output files:")
        for key, path in result.output_paths.items():
            logger.info(f"   [{key}] {path}")

        # Print sample transcript
        if result.transcript:
            logger.info("")
            logger.info("📝  Sample transcript (first 3 segments):")
            for seg in result.transcript[:3]:
                logger.info(f"   [{seg.start:.1f}s → {seg.end:.1f}s] {seg.text}")

        # Print sample translations
        for lang_code, segs in result.translations.items():
            if segs:
                logger.info("")
                logger.info(f"🌐  Sample translation [{lang_code}] (first 3 segments):")
                for seg in segs[:3]:
                    logger.info(f"   EN: {seg.source_text}")
                    logger.info(f"   {lang_code}: {seg.translated_text}")
                    if seg.qa_flags:
                        logger.warning(f"   ⚠️  QA flags: {seg.qa_flags}")
                    logger.info("")

        logger.info("=" * 60)
        logger.info("Next step: Open the review portal to approve translations.")
        logger.info("Run: cd frontend && npm run dev")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
