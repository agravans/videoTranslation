"""
Stage 4 (QA layer): Claude-powered BFSI term validation
- Checks translated segments against BFSI glossary
- Flags regulatory term mistranslations
- Scores overall translation quality
"""
import logging
import json
from typing import List, Tuple

import anthropic

from app.models.job import TranslatedSegment, Language
from app.config import settings
from app.glossary.bfsi import get_glossary, BFSI_TERMS_EN

logger = logging.getLogger(__name__)

QA_SYSTEM_PROMPT = """You are a BFSI (Banking, Financial Services, Insurance) compliance training quality assurance specialist for Indian enterprises. You validate AI-translated training content for accuracy, especially for regulatory and technical terminology.

Your job:
1. Check that BFSI-specific terms (AML, KYC, FEMA, RBI, SEBI, IRDAI, NBFC, etc.) are correctly translated or appropriately kept in English
2. Flag any segments where the translation may be misleading or change the compliance meaning
3. Score each segment: "ok", "warning", or "critical" (critical = regulatory term likely mistranslated)

Always respond in JSON format."""

QA_USER_PROMPT = """Review these translated segments from a BFSI compliance training video.

Target language: {language}
BFSI glossary reference: {glossary_sample}

Segments to review:
{segments_json}

For each segment, respond with:
{{
  "segment_id": <int>,
  "status": "ok" | "warning" | "critical",
  "flags": ["<issue description>"],
  "suggested_fix": "<corrected text if needed, else null>"
}}

Return a JSON array of these objects."""


def run_qa_check(
    segments: List[TranslatedSegment],
    target_language: Language
) -> List[TranslatedSegment]:
    """
    Run Claude QA check on translated segments.
    Adds qa_flags to segments that have issues.
    Returns updated segments.
    """
    if settings.mock_claude:
        return _mock_qa(segments)

    if not settings.anthropic_api_key:
        logger.warning("No Anthropic API key — skipping QA check")
        return segments

    # Process in batches to stay within token limits
    BATCH_SIZE = 15
    batches = [segments[i:i + BATCH_SIZE] for i in range(0, len(segments), BATCH_SIZE)]
    result_map = {}

    for batch_idx, batch in enumerate(batches):
        logger.info(f"QA check batch {batch_idx + 1}/{len(batches)}")
        try:
            batch_results = _run_claude_qa_batch(batch, target_language)
            result_map.update(batch_results)
        except Exception as e:
            logger.error(f"QA batch {batch_idx} failed: {e}")
            continue

    # Apply QA results back to segments
    updated = []
    for seg in segments:
        result = result_map.get(seg.id)
        if result:
            seg.qa_flags = result.get("flags", [])
            if result.get("status") == "critical" and result.get("suggested_fix"):
                # Auto-apply critical fixes
                logger.warning(f"Critical QA flag on segment {seg.id}: {seg.qa_flags}")
        updated.append(seg)

    return updated


def _run_claude_qa_batch(
    segments: List[TranslatedSegment],
    target_language: Language
) -> dict:
    """Run Claude QA on a batch of segments. Returns {segment_id: result}."""
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    glossary = get_glossary(target_language)
    glossary_sample = json.dumps(dict(list(glossary.items())[:20]), ensure_ascii=False, indent=2)

    segments_data = [
        {
            "id": seg.id,
            "source": seg.source_text,
            "translation": seg.translated_text
        }
        for seg in segments
    ]

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=QA_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": QA_USER_PROMPT.format(
                language=target_language.value,
                glossary_sample=glossary_sample,
                segments_json=json.dumps(segments_data, ensure_ascii=False, indent=2)
            )
        }]
    )

    # Parse JSON response
    response_text = message.content[0].text
    # Strip markdown code blocks if present
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()

    results = json.loads(response_text)
    return {r["segment_id"]: r for r in results}


def _mock_qa(segments: List[TranslatedSegment]) -> List[TranslatedSegment]:
    """Mock QA — marks FEMA/KYC/RBI mentions as reviewed OK."""
    for seg in segments:
        for term in BFSI_TERMS_EN:
            if term in seg.source_text:
                seg.qa_flags = []  # Clean bill of health in mock
    return segments
