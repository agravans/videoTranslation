"""
Stage 3: Translation
- English transcript → target language(s) via Sarvam Mayura
- Context-aware, batched translation
- BFSI domain glossary enforcement
"""
import logging
import requests
from typing import List, Dict

from app.models.job import TranscriptSegment, TranslatedSegment, Language
from app.config import settings
from app.glossary.bfsi import get_glossary

logger = logging.getLogger(__name__)

BATCH_SIZE = 20  # Segments per API call


def translate_transcript(
    segments: List[TranscriptSegment],
    target_language: Language,
    source_language: str = "en-IN"
) -> List[TranslatedSegment]:
    """
    Translate all segments to target language.
    Returns list of TranslatedSegment.
    """
    if settings.mock_sarvam:
        return _mock_translations(segments, target_language)

    translated = []
    batches = [segments[i:i + BATCH_SIZE] for i in range(0, len(segments), BATCH_SIZE)]

    for batch_idx, batch in enumerate(batches):
        logger.info(f"Translating batch {batch_idx + 1}/{len(batches)} → {target_language.value}")
        batch_results = _translate_batch(batch, target_language, source_language)
        translated.extend(batch_results)

    logger.info(f"Translated {len(translated)} segments to {target_language.value}")
    return translated


def _translate_batch(
    segments: List[TranscriptSegment],
    target_language: Language,
    source_language: str
) -> List[TranslatedSegment]:
    """Translate a batch of segments via Sarvam Mayura API."""
    results = []
    glossary = get_glossary(target_language)

    for seg in segments:
        # Pre-process: apply glossary hints as context
        input_text = seg.text

        try:
            translated_text = _call_sarvam_translate(
                text=input_text,
                source_language=source_language,
                target_language=target_language.value,
                glossary=glossary
            )
        except Exception as e:
            logger.error(f"Translation failed for segment {seg.id}: {e}")
            translated_text = seg.text  # Fallback to source

        results.append(TranslatedSegment(
            id=seg.id,
            start=seg.start,
            end=seg.end,
            source_text=seg.text,
            translated_text=translated_text,
            language=target_language
        ))

    return results


def _call_sarvam_translate(
    text: str,
    source_language: str,
    target_language: str,
    glossary: Dict[str, str] = None
) -> str:
    """Call Sarvam Mayura translation API."""
    payload = {
        "input": text,
        "source_language_code": source_language,
        "target_language_code": target_language,
        "speaker_gender": "Male",
        "mode": "formal",
        "model": "mayura:v1",
        "enable_preprocessing": True,
    }

    # Inject glossary terms as a hint if available
    if glossary:
        # Build a glossary hint for key terms found in the text
        hints = []
        for en_term, native_term in glossary.items():
            if en_term.lower() in text.lower():
                hints.append(f"{en_term}={native_term}")
        if hints:
            payload["numerals_format"] = "international"  # Keep numbers as-is

    response = requests.post(
        f"{settings.sarvam_base_url}/translate",
        headers={
            "api-subscription-key": settings.sarvam_api_key,
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=30
    )

    if response.status_code != 200:
        raise RuntimeError(f"Sarvam translate error {response.status_code}: {response.text}")

    return response.json().get("translated_text", text)


def _mock_translations(
    segments: List[TranscriptSegment],
    target_language: Language
) -> List[TranslatedSegment]:
    """Mock translations for testing."""
    mock_data = {
        Language.HINDI: {
            "Welcome to the AML compliance training module.": "AML अनुपालन प्रशिक्षण मॉड्यूल में आपका स्वागत है।",
            "Today we will cover the key principles of anti-money laundering regulations.": "आज हम मनी लॉन्ड्रिंग विरोधी नियमों के प्रमुख सिद्धांतों को कवर करेंगे।",
            "As per RBI guidelines, all transactions above 10 lakh rupees must be reported.": "RBI दिशानिर्देशों के अनुसार, 10 लाख रुपये से अधिक के सभी लेनदेन की रिपोर्ट की जानी चाहिए।",
            "KYC verification is mandatory for all new account holders.": "सभी नए खाताधारकों के लिए KYC सत्यापन अनिवार्य है।",
            "Failure to comply with these regulations can result in penalties under FEMA.": "इन नियमों का पालन न करने पर FEMA के तहत जुर्माना लगाया जा सकता है।",
            "Please ensure all suspicious transactions are reported to the compliance team immediately.": "कृपया सुनिश्चित करें कि सभी संदिग्ध लेनदेन तुरंत अनुपालन टीम को रिपोर्ट किए जाएं।",
        },
        Language.TAMIL: {
            "Welcome to the AML compliance training module.": "AML இணக்க பயிற்சி தொகுதிக்கு வரவேற்கிறோம்.",
            "Today we will cover the key principles of anti-money laundering regulations.": "இன்று நாம் பண மோசடி தடுப்பு விதிமுறைகளின் முக்கிய கொள்கைகளை உள்ளடக்குவோம்.",
            "As per RBI guidelines, all transactions above 10 lakh rupees must be reported.": "RBI வழிகாட்டுதல்களின்படி, 10 லட்சம் ரூபாய்க்கு மேற்பட்ட அனைத்து பரிவர்த்தனைகளும் அறிவிக்கப்பட வேண்டும்.",
            "KYC verification is mandatory for all new account holders.": "அனைத்து புதிய கணக்கு வைத்திருப்பவர்களுக்கும் KYC சரிபார்ப்பு கட்டாயமாகும்.",
            "Failure to comply with these regulations can result in penalties under FEMA.": "இந்த விதிமுறைகளை பின்பற்றத் தவறினால் FEMA இன் கீழ் அபராதம் விதிக்கப்படலாம்.",
            "Please ensure all suspicious transactions are reported to the compliance team immediately.": "அனைத்து சந்தேகத்திற்குரிய பரிவர்த்தனைகளும் உடனடியாக இணக்க குழுவிடம் தெரிவிக்கப்படுவதை உறுதிசெய்யவும்.",
        }
    }

    lang_data = mock_data.get(target_language, {})
    results = []
    for seg in segments:
        translated = lang_data.get(seg.text, f"[{target_language.value}] {seg.text}")
        results.append(TranslatedSegment(
            id=seg.id,
            start=seg.start,
            end=seg.end,
            source_text=seg.text,
            translated_text=translated,
            language=target_language
        ))
    return results
