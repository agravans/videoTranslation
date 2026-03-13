"""
BFSI Domain Glossary — 150+ key terms with Hindi and Tamil translations.
This is your quality moat: correct translation of regulatory terms is non-negotiable.

Philosophy:
- Many BFSI acronyms (RBI, SEBI, KYC, AML) are KEPT in English in all Indian languages
  because these are used as-is in official communications.
- Descriptive terms (like "Anti-Money Laundering") get translated.
- Numbers, thresholds, and proper nouns (bank names) stay in English/numerals.
"""
from typing import Dict
from app.models.job import Language

# ── Regulatory bodies & acronyms (KEEP in English) ────────────────────────
# These are NEVER translated — they appear as-is in official Indian documents.
KEEP_AS_ENGLISH = {
    "RBI", "SEBI", "IRDAI", "NABARD", "NHB", "SIDBI", "EXIM",
    "KYC", "AML", "CTF", "STR", "CTR", "SAR",
    "FEMA", "PMLA", "FATF", "FIU-IND", "ED", "CBI",
    "NBFC", "HFC", "MFI", "UIDAI", "Aadhaar", "PAN",
    "NEFT", "RTGS", "IMPS", "UPI", "NACH",
    "NPA", "CIBIL", "CERSAI",
    "SCORM", "LMS", "xAPI",
}

# ── Hindi translations ─────────────────────────────────────────────────────
HINDI_GLOSSARY: Dict[str, str] = {
    # Regulatory & Compliance
    "Anti-Money Laundering": "धन शोधन निवारण",
    "money laundering": "मनी लॉन्ड्रिंग / धन शोधन",
    "Combating the Financing of Terrorism": "आतंकवाद के वित्तपोषण का मुकाबला",
    "Know Your Customer": "अपने ग्राहक को जानें",
    "Suspicious Transaction Report": "संदिग्ध लेनदेन रिपोर्ट",
    "Cash Transaction Report": "नकद लेनदेन रिपोर्ट",
    "Suspicious Activity Report": "संदिग्ध गतिविधि रिपोर्ट",
    "Financial Intelligence Unit": "वित्तीय खुफिया इकाई",
    "Prevention of Money Laundering Act": "धन शोधन निवारण अधिनियम",
    "Foreign Exchange Management Act": "विदेशी मुद्रा प्रबंधन अधिनियम",
    "Financial Action Task Force": "वित्तीय कार्रवाई कार्यबल",

    # Banking Terms
    "bank account": "बैंक खाता",
    "savings account": "बचत खाता",
    "current account": "चालू खाता",
    "fixed deposit": "सावधि जमा",
    "recurring deposit": "आवर्ती जमा",
    "loan": "ऋण",
    "interest rate": "ब्याज दर",
    "principal": "मूलधन",
    "collateral": "संपार्श्विक",
    "mortgage": "बंधक",
    "cheque": "चेक",
    "demand draft": "माँग ड्राफ्ट",
    "credit card": "क्रेडिट कार्ड",
    "debit card": "डेबिट कार्ड",
    "transaction": "लेनदेन",
    "transfer": "हस्तांतरण",
    "withdrawal": "निकासी",
    "deposit": "जमा",
    "balance": "शेष राशि",
    "statement": "विवरण",
    "branch": "शाखा",
    "nominee": "नामांकित व्यक्ति",

    # Risk & Compliance
    "compliance": "अनुपालन",
    "regulatory compliance": "नियामक अनुपालन",
    "risk assessment": "जोखिम मूल्यांकन",
    "risk management": "जोखिम प्रबंधन",
    "due diligence": "उचित परिश्रम",
    "enhanced due diligence": "उन्नत उचित परिश्रम",
    "Customer Due Diligence": "ग्राहक उचित परिश्रम",
    "Beneficial Owner": "लाभकारी स्वामी",
    "Politically Exposed Person": "राजनीतिक रूप से उजागर व्यक्ति",
    "high-risk customer": "उच्च जोखिम वाला ग्राहक",
    "money mule": "मनी म्यूल",
    "shell company": "शेल कंपनी",
    "layering": "स्तरीकरण",
    "integration": "एकीकरण",
    "placement": "नियोजन",
    "terrorist financing": "आतंकवादी वित्तपोषण",
    "sanction": "प्रतिबंध",
    "watchlist": "निगरानी सूची",
    "blacklist": "काली सूची",
    "penalty": "जुर्माना",
    "fine": "अर्थदंड",
    "audit": "लेखापरीक्षा",
    "internal audit": "आंतरिक लेखापरीक्षा",
    "regulatory audit": "नियामक लेखापरीक्षा",

    # Insurance Terms
    "insurance policy": "बीमा पॉलिसी",
    "premium": "प्रीमियम",
    "claim": "दावा",
    "policyholder": "पॉलिसीधारक",
    "insured": "बीमाधारक",
    "beneficiary": "लाभार्थी",
    "sum assured": "बीमित राशि",
    "maturity": "परिपक्वता",
    "surrender value": "समर्पण मूल्य",
    "underwriting": "हामीदारी",
    "life insurance": "जीवन बीमा",
    "health insurance": "स्वास्थ्य बीमा",
    "general insurance": "सामान्य बीमा",

    # Securities & Capital Markets
    "equity": "इक्विटी",
    "share": "शेयर",
    "stock": "स्टॉक",
    "bond": "बॉन्ड",
    "mutual fund": "म्यूचुअल फंड",
    "portfolio": "पोर्टफोलियो",
    "dividend": "लाभांश",
    "capital gain": "पूंजीगत लाभ",
    "market capitalization": "बाजार पूंजीकरण",
    "Initial Public Offering": "प्रारंभिक सार्वजनिक प्रस्ताव",
    "Non-Performing Asset": "गैर-निष्पादित परिसंपत्ति",

    # General Training Terms
    "training": "प्रशिक्षण",
    "compliance training": "अनुपालन प्रशिक्षण",
    "mandatory training": "अनिवार्य प्रशिक्षण",
    "assessment": "मूल्यांकन",
    "certification": "प्रमाणन",
    "module": "मॉड्यूल",
    "employee": "कर्मचारी",
    "manager": "प्रबंधक",
    "guidelines": "दिशानिर्देश",
    "policy": "नीति",
    "procedure": "प्रक्रिया",
    "regulation": "विनियम",
    "reporting": "रिपोर्टिंग",
    "threshold": "सीमा",
    "investigation": "जाँच",
    "fraud": "धोखाधड़ी",
    "cybersecurity": "साइबर सुरक्षा",
    "data privacy": "डेटा गोपनीयता",
    "whistleblower": "मुखबिर",
}

# ── Tamil translations ─────────────────────────────────────────────────────
TAMIL_GLOSSARY: Dict[str, str] = {
    # Regulatory & Compliance
    "Anti-Money Laundering": "பண மோசடி தடுப்பு",
    "money laundering": "பண மோசடி",
    "Combating the Financing of Terrorism": "தீவிரவாத நிதியுதவி தடுப்பு",
    "Know Your Customer": "உங்கள் வாடிக்கையாளரை அறிக",
    "Suspicious Transaction Report": "சந்தேகத்திற்குரிய பரிவர்த்தனை அறிக்கை",
    "Cash Transaction Report": "பண பரிவர்த்தனை அறிக்கை",
    "Suspicious Activity Report": "சந்தேகத்திற்குரிய செயல்பாடு அறிக்கை",
    "Financial Intelligence Unit": "நிதி புலனாய்வு அலகு",
    "Prevention of Money Laundering Act": "பண மோசடி தடுப்பு சட்டம்",
    "Foreign Exchange Management Act": "அந்நிய செலாவணி மேலாண்மை சட்டம்",
    "Financial Action Task Force": "நிதி நடவடிக்கை பணிக்குழு",

    # Banking Terms
    "bank account": "வங்கிக் கணக்கு",
    "savings account": "சேமிப்புக் கணக்கு",
    "current account": "நடப்புக் கணக்கு",
    "fixed deposit": "நிலையான வைப்பு",
    "recurring deposit": "தொடர் வைப்பு",
    "loan": "கடன்",
    "interest rate": "வட்டி விகிதம்",
    "principal": "அசல்",
    "collateral": "இணை பிணையம்",
    "mortgage": "அடமானம்",
    "cheque": "காசோலை",
    "demand draft": "கோரிக்கை வரைவு",
    "credit card": "கடன் அட்டை",
    "debit card": "பற்று அட்டை",
    "transaction": "பரிவர்த்தனை",
    "transfer": "பரிமாற்றம்",
    "withdrawal": "திரும்பப் பெறுதல்",
    "deposit": "வைப்பு",
    "balance": "இருப்பு",
    "statement": "அறிக்கை",
    "branch": "கிளை",
    "nominee": "நியமிக்கப்பட்டவர்",

    # Risk & Compliance
    "compliance": "இணக்கம்",
    "regulatory compliance": "ஒழுங்குமுறை இணக்கம்",
    "risk assessment": "அபாய மதிப்பீடு",
    "risk management": "அபாய மேலாண்மை",
    "due diligence": "உரிய விடாமுயற்சி",
    "enhanced due diligence": "மேம்படுத்தப்பட்ட விடாமுயற்சி",
    "Customer Due Diligence": "வாடிக்கையாளர் விடாமுயற்சி",
    "Beneficial Owner": "பயனுள்ள உரிமையாளர்",
    "Politically Exposed Person": "அரசியல் ரீதியில் வெளிப்படும் நபர்",
    "high-risk customer": "அதிக அபாய வாடிக்கையாளர்",
    "money mule": "பண கோவேறு கழுதை",
    "shell company": "வெற்று நிறுவனம்",
    "layering": "அடுக்கமைவு",
    "placement": "நிலைப்படுத்தல்",
    "terrorist financing": "தீவிரவாத நிதியுதவி",
    "sanction": "தடை",
    "watchlist": "கண்காணிப்பு பட்டியல்",
    "penalty": "அபராதம்",
    "audit": "தணிக்கை",
    "investigation": "விசாரணை",
    "fraud": "மோசடி",

    # Insurance Terms
    "insurance policy": "காப்பீட்டு திட்டம்",
    "premium": "காப்பீட்டு கட்டணம்",
    "claim": "உரிமை கோரிக்கை",
    "policyholder": "பாலிசி வைத்திருப்பவர்",
    "insured": "காப்பீடு செய்யப்பட்டவர்",
    "beneficiary": "பயனாளி",
    "sum assured": "உறுதி தொகை",
    "life insurance": "ஆயுள் காப்பீடு",
    "health insurance": "உடல்நல காப்பீடு",
    "general insurance": "பொது காப்பீடு",

    # Securities
    "equity": "பங்கு மூலதனம்",
    "share": "பங்கு",
    "bond": "பத்திரம்",
    "mutual fund": "பரஸ்பர நிதி",
    "dividend": "ஈவுத்தொகை",
    "Non-Performing Asset": "செயல்படாத சொத்து",

    # Training Terms
    "training": "பயிற்சி",
    "compliance training": "இணக்க பயிற்சி",
    "mandatory training": "கட்டாய பயிற்சி",
    "assessment": "மதிப்பீடு",
    "certification": "சான்றிதழ்",
    "module": "தொகுதி",
    "employee": "பணியாளர்",
    "guidelines": "வழிகாட்டுதல்கள்",
    "policy": "கொள்கை",
    "regulation": "விதிமுறை",
    "reporting": "அறிக்கையிடல்",
    "threshold": "வரம்பு",
    "fraud": "மோசடி",
    "cybersecurity": "இணைய பாதுகாப்பு",
    "data privacy": "தரவு தனியுரிமை",
    "whistleblower": "தகவல் அளிப்பவர்",
}

# English BFSI terms list (used for QA flagging)
BFSI_TERMS_EN = list(KEEP_AS_ENGLISH) + [
    "Anti-Money Laundering", "Know Your Customer", "Suspicious Transaction",
    "Cash Transaction", "due diligence", "Beneficial Owner",
    "Politically Exposed Person", "terrorist financing",
    "Non-Performing Asset", "compliance", "regulatory"
]


def get_glossary(language: Language) -> Dict[str, str]:
    """Return the glossary for the given target language."""
    if language == Language.HINDI:
        return HINDI_GLOSSARY
    elif language == Language.TAMIL:
        return TAMIL_GLOSSARY
    else:
        # For other languages, return a minimal English-passthrough glossary
        # These will be expanded as the platform grows
        return {term: term for term in KEEP_AS_ENGLISH}
