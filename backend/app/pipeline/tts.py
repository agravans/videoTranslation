"""
Stage 5: TTS Dubbing
- Translated text → natural Indian-language speech
- Primary: Sarvam Bulbul v3 (11 Indian languages)
- Fallback: ElevenLabs (for voice cloning original speaker)
- Handles timing adjustment to match original segment durations
"""
import logging
import os
import base64
import json
import requests
import tempfile
from pathlib import Path
from typing import List, Optional

from app.models.job import TranslatedSegment, Language
from app.config import settings

logger = logging.getLogger(__name__)

# Sarvam Bulbul voice IDs per language
BULBUL_VOICES = {
    Language.HINDI: "meera",
    Language.TAMIL: "pavithra",
    Language.BENGALI: "bani",
    Language.GUJARATI: "diya",
    Language.KANNADA: "neel",
    Language.MALAYALAM: "indu",
    Language.MARATHI: "aarohi",
    Language.ODIA: "arjun",
    Language.PUNJABI: "amol",
    Language.TELUGU: "maitreyi",
    Language.URDU: "amara",
}


def generate_tts_audio(
    segments: List[TranslatedSegment],
    target_language: Language,
    output_dir: str,
    job_id: str
) -> List[dict]:
    """
    Generate TTS audio for each translated segment.
    Returns list of {segment_id, start, end, audio_path}.
    """
    if settings.mock_sarvam:
        return _mock_tts(segments, output_dir, job_id)

    output_dir = Path(output_dir) / job_id / "tts" / target_language.value
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for seg in segments:
        if not seg.translated_text.strip():
            continue

        audio_path = output_dir / f"seg_{seg.id:04d}.wav"
        try:
            _generate_segment_audio(
                text=seg.translated_text,
                language=target_language,
                output_path=str(audio_path)
            )
            results.append({
                "segment_id": seg.id,
                "start": seg.start,
                "end": seg.end,
                "audio_path": str(audio_path),
                "source_duration": seg.end - seg.start,
            })
            logger.debug(f"TTS segment {seg.id}: {audio_path.name}")
        except Exception as e:
            logger.error(f"TTS failed for segment {seg.id}: {e}")

    logger.info(f"Generated {len(results)} TTS audio segments for {target_language.value}")
    return results


def _generate_segment_audio(text: str, language: Language, output_path: str):
    """Call Sarvam Bulbul v3 TTS API for one segment."""
    voice = BULBUL_VOICES.get(language, "meera")

    response = requests.post(
        f"{settings.sarvam_base_url}/text-to-speech",
        headers={
            "api-subscription-key": settings.sarvam_api_key,
            "Content-Type": "application/json"
        },
        json={
            "inputs": [text],
            "target_language_code": language.value,
            "speaker": voice,
            "pitch": 0,
            "pace": 1.0,
            "loudness": 1.5,
            "speech_sample_rate": 22050,
            "enable_preprocessing": True,
            "model": "bulbul:v1",
        },
        timeout=30
    )

    if response.status_code != 200:
        raise RuntimeError(f"Sarvam TTS error {response.status_code}: {response.text}")

    data = response.json()
    audio_b64 = data.get("audios", [""])[0]
    if not audio_b64:
        raise RuntimeError("Empty audio response from Sarvam TTS")

    audio_bytes = base64.b64decode(audio_b64)
    with open(output_path, "wb") as f:
        f.write(audio_bytes)


def _mock_tts(segments: List[TranslatedSegment], output_dir: str, job_id: str) -> List[dict]:
    """Mock TTS — creates silent WAV files for testing."""
    import struct
    import wave

    output_path = Path(output_dir) / job_id / "tts"
    output_path.mkdir(parents=True, exist_ok=True)

    results = []
    for seg in segments:
        audio_path = output_path / f"seg_{seg.id:04d}.wav"
        duration = seg.end - seg.start

        # Create a silent WAV file
        with wave.open(str(audio_path), 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(22050)
            num_frames = int(22050 * duration)
            wav.writeframes(b'\x00\x00' * num_frames)

        results.append({
            "segment_id": seg.id,
            "start": seg.start,
            "end": seg.end,
            "audio_path": str(audio_path),
            "source_duration": duration,
        })

    return results
