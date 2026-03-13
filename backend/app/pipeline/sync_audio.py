"""
Stage 6: Audio/Video Sync
- Place TTS audio segments at correct timestamps
- Mix dubbed audio with background music (if present)
- Output final dubbed MP4
"""
import subprocess
import logging
import json
import os
import tempfile
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


def build_dubbed_video(
    original_video_path: str,
    tts_segments: List[dict],
    output_path: str,
    preserve_background_audio: bool = True,
    bg_audio_volume: float = 0.1,
) -> str:
    """
    Assemble dubbed video by placing TTS audio at correct timestamps.

    Strategy:
    1. Create a silent audio track matching original video duration
    2. Overlay each TTS segment at the correct timestamp
    3. Optionally mix with low-volume original audio (for background music/ambient)
    4. Merge dubbed audio back into video
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    duration = _get_duration(original_video_path)
    temp_dir = Path(output_path).parent / "temp"
    temp_dir.mkdir(exist_ok=True)

    # Step 1: Create silent base track
    silent_track = str(temp_dir / "silent_base.wav")
    _create_silent_track(duration, silent_track)

    # Step 2: Build FFmpeg filter_complex to overlay all TTS segments
    dubbed_audio = str(temp_dir / "dubbed_audio.wav")
    _overlay_tts_segments(silent_track, tts_segments, dubbed_audio)

    # Step 3: Optionally mix with original (background music)
    if preserve_background_audio:
        final_audio = str(temp_dir / "final_audio.wav")
        _mix_audio_tracks(dubbed_audio, original_video_path, final_audio, bg_audio_volume)
    else:
        final_audio = dubbed_audio

    # Step 4: Merge audio into video
    _merge_audio_video(original_video_path, final_audio, output_path)

    # Cleanup temp files
    for f in [silent_track, dubbed_audio]:
        try:
            os.unlink(f)
        except Exception:
            pass

    logger.info(f"Dubbed video written: {output_path}")
    return output_path


def _create_silent_track(duration: float, output_path: str):
    """Create a silent WAV track of given duration."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"anullsrc=channel_layout=mono:sample_rate=22050",
        "-t", str(duration),
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to create silent track: {result.stderr}")


def _overlay_tts_segments(base_track: str, tts_segments: List[dict], output_path: str):
    """
    Overlay TTS audio segments onto base silent track at correct timestamps.
    Uses FFmpeg adelay filter.
    """
    if not tts_segments:
        import shutil
        shutil.copy(base_track, output_path)
        return

    # Build filter_complex with adelay for each segment
    inputs = ["-i", base_track]
    filter_parts = ["[0:a]anull[base]"]
    current_label = "base"

    for i, seg in enumerate(tts_segments):
        delay_ms = int(seg["start"] * 1000)
        seg_audio = seg["audio_path"]

        if not Path(seg_audio).exists():
            logger.warning(f"TTS audio missing: {seg_audio}")
            continue

        inputs.extend(["-i", seg_audio])
        input_idx = i + 1
        new_label = f"mix{i}"

        filter_parts.append(
            f"[{input_idx}:a]adelay={delay_ms}|{delay_ms}[delayed{i}];"
            f"[{current_label}][delayed{i}]amix=inputs=2:duration=first[{new_label}]"
        )
        current_label = new_label

    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", f"[{current_label}]",
        "-c:a", "pcm_s16le",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg overlay failed: {result.stderr}")


def _mix_audio_tracks(dubbed_track: str, original_video: str, output_path: str, bg_volume: float):
    """Mix dubbed audio with original video audio at reduced volume (for background music)."""
    cmd = [
        "ffmpeg", "-y",
        "-i", dubbed_track,
        "-i", original_video,
        "-filter_complex",
        f"[1:a]volume={bg_volume}[bg];[0:a][bg]amix=inputs=2:duration=first[out]",
        "-map", "[out]",
        "-c:a", "pcm_s16le",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg audio mix failed: {result.stderr}")


def _merge_audio_video(video_path: str, audio_path: str, output_path: str):
    """Replace video audio with dubbed audio."""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg merge failed: {result.stderr}")


def _get_duration(video_path: str) -> float:
    """Get video duration in seconds."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return 60.0  # Default fallback
    data = json.loads(result.stdout)
    return float(data.get("format", {}).get("duration", 60.0))
