"""
Stage 1: Ingest & Pre-process
- Extract audio from video using FFmpeg
- Normalize audio (16kHz mono WAV for Whisper)
- Basic denoising
"""
import subprocess
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def extract_audio(video_path: str, output_dir: str) -> dict:
    """
    Extract and normalize audio from video.
    Returns dict with audio_path and duration_seconds.
    """
    video_path = Path(video_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    audio_path = output_dir / f"{video_path.stem}_audio.wav"

    # Extract audio: 16kHz mono WAV (optimal for Whisper)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vn",                    # No video
        "-acodec", "pcm_s16le",   # PCM 16-bit
        "-ar", "16000",           # 16kHz sample rate
        "-ac", "1",               # Mono
        "-af", "highpass=f=80,lowpass=f=8000,afftdn=nf=-25",  # Basic denoising
        str(audio_path)
    ]

    logger.info(f"Extracting audio: {video_path.name}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg audio extraction failed:\n{result.stderr}")

    # Get video duration
    duration = get_video_duration(str(video_path))

    logger.info(f"Audio extracted to {audio_path} (duration: {duration:.1f}s)")
    return {
        "audio_path": str(audio_path),
        "duration_seconds": duration
    }


def get_video_duration(video_path: str) -> float:
    """Get video duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return 0.0
    import json
    data = json.loads(result.stdout)
    return float(data.get("format", {}).get("duration", 0))


def validate_video(video_path: str, max_size_mb: int = 500) -> bool:
    """Check video is valid and within size limits."""
    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > max_size_mb:
        raise ValueError(f"Video size {size_mb:.1f}MB exceeds limit of {max_size_mb}MB")

    # Check it's a valid video
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", video_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise ValueError(f"Invalid video file: {video_path}")

    return True
