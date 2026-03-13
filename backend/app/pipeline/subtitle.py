"""
Stage 7: Subtitle Generation & Burn-in
- Generate SRT files from translated segments
- Burn subtitles into video using FFmpeg (optional)
- Deliver as separate .srt file or embedded
"""
import subprocess
import logging
from pathlib import Path
from typing import List, Optional

from app.models.job import TranslatedSegment, TranscriptSegment, Language

logger = logging.getLogger(__name__)


def generate_srt(segments: List[TranslatedSegment], output_path: str) -> str:
    """
    Generate SRT subtitle file from translated segments.
    Returns path to generated .srt file.
    """
    content = _segments_to_srt(segments)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"SRT written: {output_path} ({len(segments)} entries)")
    return output_path


def generate_source_srt(segments: List[TranscriptSegment], output_path: str) -> str:
    """Generate SRT from original English transcript segments."""
    lines = []
    for seg in segments:
        lines.append(str(seg.id + 1))
        lines.append(f"{_ts(seg.start)} --> {_ts(seg.end)}")
        lines.append(seg.text)
        lines.append("")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_path


def burn_subtitles(
    video_path: str,
    srt_path: str,
    output_path: str,
    font_size: int = 24,
    font_color: str = "white",
    outline_color: str = "black"
) -> str:
    """
    Burn subtitles into video using FFmpeg.
    Returns path to output video.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Escape the SRT path for FFmpeg subtitles filter
    escaped_srt = srt_path.replace("\\", "/").replace(":", "\\:")

    subtitle_style = (
        f"FontSize={font_size},"
        f"PrimaryColour=&H00FFFFFF,"
        f"OutlineColour=&H00000000,"
        f"Outline=1,"
        f"Alignment=2"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"subtitles={escaped_srt}:force_style='{subtitle_style}'",
        "-c:a", "copy",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        output_path
    ]

    logger.info(f"Burning subtitles into: {Path(output_path).name}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg subtitle burn-in failed:\n{result.stderr}")

    return output_path


def _segments_to_srt(segments: List[TranslatedSegment]) -> str:
    """Convert TranslatedSegment list to SRT string."""
    lines = []
    for i, seg in enumerate(segments, 1):
        lines.append(str(i))
        lines.append(f"{_ts(seg.start)} --> {_ts(seg.end)}")
        lines.append(seg.reviewer_edited or seg.translated_text)
        lines.append("")
    return "\n".join(lines)


def _ts(seconds: float) -> str:
    """Format seconds to SRT timestamp HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
