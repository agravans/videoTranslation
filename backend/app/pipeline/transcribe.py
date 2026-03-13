"""
Stage 2: Transcription (STT)
- English speech → timestamped transcript with speaker diarization
- Primary: faster-whisper (self-hosted, free)
- Fallback: OpenAI Whisper API / Sarvam Saaras v3
"""
import logging
import os
from typing import List, Optional
from pathlib import Path

from app.models.job import TranscriptSegment
from app.config import settings

logger = logging.getLogger(__name__)


def transcribe_audio(audio_path: str, language: str = "en") -> List[TranscriptSegment]:
    """
    Transcribe audio to timestamped segments.
    Returns list of TranscriptSegment with start/end times.
    """
    if settings.mock_sarvam:
        return _mock_transcript()

    # Try faster-whisper first (free, self-hosted)
    try:
        return _transcribe_whisper_local(audio_path, language)
    except ImportError:
        logger.warning("faster-whisper not installed. Falling back to OpenAI Whisper API.")
        return _transcribe_openai_api(audio_path)


def _transcribe_whisper_local(audio_path: str, language: str = "en") -> List[TranscriptSegment]:
    """Use faster-whisper for local transcription (free)."""
    from faster_whisper import WhisperModel

    logger.info(f"Loading Whisper model: {settings.whisper_model}")
    model = WhisperModel(settings.whisper_model, device="cpu", compute_type="int8")

    logger.info(f"Transcribing: {Path(audio_path).name}")
    segments, info = model.transcribe(
        audio_path,
        language=language,
        beam_size=5,
        word_timestamps=True,
        vad_filter=True,           # Voice activity detection
        vad_parameters=dict(min_silence_duration_ms=500)
    )

    transcript = []
    for i, seg in enumerate(segments):
        transcript.append(TranscriptSegment(
            id=i,
            start=seg.start,
            end=seg.end,
            text=seg.text.strip(),
            speaker=None  # Diarization requires pyannote.audio (optional)
        ))

    logger.info(f"Transcribed {len(transcript)} segments")
    return transcript


def _transcribe_openai_api(audio_path: str) -> List[TranscriptSegment]:
    """Fallback: OpenAI Whisper API."""
    import openai

    client = openai.OpenAI(api_key=settings.openai_api_key)
    logger.info("Transcribing via OpenAI Whisper API")

    with open(audio_path, "rb") as f:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",
            timestamp_granularities=["segment"]
        )

    transcript = []
    for i, seg in enumerate(response.segments):
        transcript.append(TranscriptSegment(
            id=i,
            start=seg["start"],
            end=seg["end"],
            text=seg["text"].strip()
        ))

    logger.info(f"Transcribed {len(transcript)} segments via OpenAI API")
    return transcript


def _transcribe_sarvam_api(audio_path: str, language_code: str = "en-IN") -> List[TranscriptSegment]:
    """
    Sarvam Saaras v3 — best for Indian-accented English.
    Use this when the source speaker has a strong Indian accent.
    """
    import requests
    import base64

    with open(audio_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode()

    response = requests.post(
        f"{settings.sarvam_base_url}/speech-to-text",
        headers={
            "api-subscription-key": settings.sarvam_api_key,
            "Content-Type": "application/json"
        },
        json={
            "model": "saaras:v2",
            "audio": audio_b64,
            "language_code": language_code,
            "with_timestamps": True,
            "with_diarization": False,
        },
        timeout=120
    )

    if response.status_code != 200:
        raise RuntimeError(f"Sarvam STT error {response.status_code}: {response.text}")

    data = response.json()
    transcript = []
    for i, seg in enumerate(data.get("transcript", {}).get("segments", [])):
        transcript.append(TranscriptSegment(
            id=i,
            start=seg.get("start", 0),
            end=seg.get("end", 0),
            text=seg.get("text", "").strip()
        ))

    return transcript


def segments_to_srt(segments: List[TranscriptSegment]) -> str:
    """Convert transcript segments to SRT format."""
    lines = []
    for seg in segments:
        lines.append(str(seg.id + 1))
        lines.append(f"{_format_timestamp(seg.start)} --> {_format_timestamp(seg.end)}")
        lines.append(seg.text)
        lines.append("")
    return "\n".join(lines)


def _format_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _mock_transcript() -> List[TranscriptSegment]:
    """Mock transcript for testing without API keys."""
    return [
        TranscriptSegment(id=0, start=0.0, end=4.5, text="Welcome to the AML compliance training module."),
        TranscriptSegment(id=1, start=4.5, end=9.0, text="Today we will cover the key principles of anti-money laundering regulations."),
        TranscriptSegment(id=2, start=9.0, end=14.2, text="As per RBI guidelines, all transactions above 10 lakh rupees must be reported."),
        TranscriptSegment(id=3, start=14.2, end=19.5, text="KYC verification is mandatory for all new account holders."),
        TranscriptSegment(id=4, start=19.5, end=25.0, text="Failure to comply with these regulations can result in penalties under FEMA."),
        TranscriptSegment(id=5, start=25.0, end=30.0, text="Please ensure all suspicious transactions are reported to the compliance team immediately."),
    ]
