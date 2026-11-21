import re
from typing import Tuple, Dict, Any

TELUGU_RANGE = (0x0C00, 0x0C7F)
DEVANAGARI_RANGE = (0x0900, 0x097F)
LATIN_RANGE = (0x0041, 0x007A) # Standard A-Za-z

# Characteristic Telugu Romanized vocabulary and morphological markers
ROMANIZED_TELUGU_KEYWORDS = {
    "cheyyi", "cheyyandi", "cheyandi", "chey", "cheyyaku", "choodu", "chudandi", "chudu",
    "marchipo", "marchipondi", "ivvu", "ivvandi", "undi", "undali", "lekapothe", "ledu",
    "ippudu", "appudu", "motham", "mottham", "cheppandi", "cheppu", "kosam", "pettuko",
    "adugu", "adugutunna", "teliyadu", "avunu", "kaadu", "raasi", "raayi", "pampu", "pampandi",
    "chusi", "mundu", "venuka", "naa", "mee", "nenu", "meeru", "manaki", "danini", "veetini",
    "sare", "ayithe", "chesuko", "chepinchuko", "thondaraga", "ventane", "kavali", "vaddu",
    "ani", "ela", "ekkada", "evaru", "enduku", "emiti", "entha", "inkoti", "cheppina",
    "nirdeshanaalu", "suchanalu", "aadhesalu", "podduna", "raatri", "dabbu", "dabbulu",
    "katteyi", "kattandi", "theesuko", "theeyi", "vadilayi"
}

# Characteristic Hindi Romanized vocabulary and morphological markers
ROMANIZED_HINDI_KEYWORDS = {
    "karo", "kijiye", "kijiye ga", "karna", "karoge", "kar sakti", "kar sakte",
    "bhejo", "bhejiye", "bhejna", "bhool", "bhoolo", "jao", "dikhaye", "dikhao",
    "batao", "bataye", "chahiye", "nahi", "nahin", "mat", "hoga", "hogi", "honge",
    "apna", "apne", "apni", "mera", "meri", "mere", "tumhara", "tumhari", "aapka", "aapki",
    "kuch", "sab", "sabhi", "aur", "lekin", "kyunki", "kripya", "jaldi", "turant",
    "paise", "rupaye", "nirdesh", "soochana", "aadesh", "pichhle", "pichhla", "pichhli",
    "dhyan", "rakho", "dekh", "dekho", "dekhiye", "kaam", "band", "shuru", "khatam",
    "bina", "saath", "pehle", "baad", "mein", "par", "se", "ko", "hai", "hain", "tha", "the",
    "karo mat", "chori", "khata", "bhejo mat"
}

COMMON_ENGLISH_WORDS = {
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i", "it", "for", "not",
    "on", "with", "he", "as", "you", "do", "at", "this", "but", "his", "by", "from",
    "they", "we", "say", "her", "she", "or", "an", "will", "my", "one", "all", "would",
    "there", "their", "what", "so", "up", "out", "if", "about", "who", "get", "which",
    "go", "me", "when", "make", "can", "like", "time", "no", "just", "him", "know",
    "take", "people", "into", "year", "your", "good", "some", "could", "them", "see",
    "other", "than", "then", "now", "look", "only", "come", "its", "over", "think",
    "also", "back", "after", "use", "two", "how", "our", "work", "first", "well", "way",
    "even", "new", "want", "because", "any", "these", "give", "day", "most", "us"
}

def analyze_script(text: str) -> Dict[str, Any]:
    total_chars = len(text.strip())
    if total_chars == 0:
        return {"primary_script": "Latin", "scripts": {"Latin": 1.0}, "confidence": 1.0}

    telugu_count = 0
    devanagari_count = 0
    latin_count = 0
    other_count = 0

    for char in text:
        cp = ord(char)
        if TELUGU_RANGE[0] <= cp <= TELUGU_RANGE[1]:
            telugu_count += 1
        elif DEVANAGARI_RANGE[0] <= cp <= DEVANAGARI_RANGE[1]:
            devanagari_count += 1
        elif ('a' <= char <= 'z') or ('A' <= char <= 'Z'):
            latin_count += 1
        elif not char.isspace() and not char.isdigit() and char not in '.,!?;:\'\"()-[]{}':
            other_count += 1

    counted = telugu_count + devanagari_count + latin_count + other_count
    if counted == 0:
        return {"primary_script": "Latin", "scripts": {"Latin": 1.0}, "confidence": 0.5}

    t_ratio = telugu_count / counted
    d_ratio = devanagari_count / counted
    l_ratio = latin_count / counted

    scripts = {}
    if t_ratio > 0.05:
        scripts["Telugu"] = round(t_ratio, 3)
    if d_ratio > 0.05:
        scripts["Devanagari"] = round(d_ratio, 3)
    if l_ratio > 0.05:
        scripts["Latin"] = round(l_ratio, 3)

    # Determine primary script
    if t_ratio > 0.40 and d_ratio < 0.15 and l_ratio < 0.35:
        primary_script = "Telugu"
        confidence = t_ratio
    elif d_ratio > 0.40 and t_ratio < 0.15 and l_ratio < 0.35:
        primary_script = "Devanagari"
        confidence = d_ratio
    elif l_ratio > 0.60:
        primary_script = "Latin"
        confidence = l_ratio
    elif (t_ratio > 0.2 and l_ratio > 0.2) or (d_ratio > 0.2 and l_ratio > 0.2) or (t_ratio > 0.2 and d_ratio > 0.2):
        primary_script = "Mixed"
        confidence = 0.85
    else:
        primary_script = "Latin"
        confidence = 0.70

    return {
        "primary_script": primary_script,
        "scripts": scripts,
        "confidence": round(confidence, 2),
        "telugu_chars": telugu_count,
        "devanagari_chars": devanagari_count,
        "latin_chars": latin_count
    }

def detect_language(text: str, language_hint: str = "auto") -> Dict[str, Any]:
    script_info = analyze_script(text)
    primary_script = script_info["primary_script"]

    # Native scripts directly determine native language
    if primary_script == "Telugu":
        # Check if code-mixed with English keywords
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        if len(words) >= 3 and any(w in COMMON_ENGLISH_WORDS for w in words):
            return {
                "language": "Mixed (Telugu-English)",
                "language_code": "mixed",
                "script": "Telugu + Latin",
                "confidence": 0.90,
                "script_info": script_info
            }
        return {
            "language": "Telugu",
            "language_code": "te",
            "script": "Telugu",
            "confidence": script_info["confidence"],
            "script_info": script_info
        }

    if primary_script == "Devanagari":
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        if len(words) >= 3 and any(w in COMMON_ENGLISH_WORDS for w in words):
            return {
                "language": "Mixed (Hindi-English)",
                "language_code": "mixed",
                "script": "Devanagari + Latin",
                "confidence": 0.90,
                "script_info": script_info
            }
        return {
            "language": "Hindi",
            "language_code": "hi",
            "script": "Devanagari",
            "confidence": script_info["confidence"],
            "script_info": script_info
        }

    if primary_script == "Mixed":
        return {
            "language": "Mixed",
            "language_code": "mixed",
            "script": "Mixed",
            "confidence": 0.88,
            "script_info": script_info
        }

    # For Latin script: analyze whether it is Romanized Telugu, Romanized Hindi, English, or Mixed
    lower_text = text.lower()
    tokens = set(re.findall(r'\b[a-z]{2,}\b', lower_text))

    te_hits = tokens.intersection(ROMANIZED_TELUGU_KEYWORDS)
    hi_hits = tokens.intersection(ROMANIZED_HINDI_KEYWORDS)
    en_hits = tokens.intersection(COMMON_ENGLISH_WORDS)

    # Phonetic and suffix heuristics for Telugu & Hindi
    te_suffix_score = len(re.findall(r'\b[a-z]+(andi|cheyyi|chey|chudandi|motham|undu|leka|galara|kundaa)\b', lower_text))
    hi_suffix_score = len(re.findall(r'\b[a-z]+(kijiye|karo|bhejo|wala|wali|wale|chahiye|gaya|gayi|diya|dega)\b', lower_text))

    te_total = len(te_hits) * 2 + te_suffix_score
    hi_total = len(hi_hits) * 2 + hi_suffix_score
    en_total = len(en_hits)

    if language_hint and language_hint != "auto":
        hint_lower = language_hint.lower()
        if "telugu" in hint_lower or hint_lower == "te" or hint_lower == "te-latn":
            te_total += 3
        elif "hindi" in hint_lower or hint_lower == "hi" or hint_lower == "hi-latn":
            hi_total += 3
        elif "english" in hint_lower or hint_lower == "en":
            en_total += 3

    if te_total >= 2 and te_total > hi_total:
        if en_total >= 4 and len(te_hits) <= 2:
            detected_lang = "Mixed (Telugu-English)"
            lang_code = "mixed"
        else:
            detected_lang = "Romanized Telugu"
            lang_code = "te-Latn"
        conf = min(0.95, 0.70 + (te_total * 0.05))
    elif hi_total >= 2 and hi_total > te_total:
        if en_total >= 4 and len(hi_hits) <= 2:
            detected_lang = "Mixed (Hindi-English)"
            lang_code = "mixed"
        else:
            detected_lang = "Romanized Hindi"
            lang_code = "hi-Latn"
        conf = min(0.95, 0.70 + (hi_total * 0.05))
    elif te_total >= 1 and hi_total >= 1:
        detected_lang = "Mixed"
        lang_code = "mixed"
        conf = 0.75
    elif en_total >= 1:
        detected_lang = "English"
        lang_code = "en"
        conf = min(0.98, 0.70 + (en_total * 0.04))
    elif len(tokens) > 0:
        detected_lang = "Undetermined (Latin)"
        lang_code = "und"
        conf = 0.45
    else:
        detected_lang = "English"
        lang_code = "en"
        conf = 0.50

    return {
        "language": detected_lang,
        "language_code": lang_code,
        "script": "Latin",
        "confidence": round(conf, 2),
        "script_info": script_info,
        "token_matches": {
            "telugu_romanized": list(te_hits),
            "hindi_romanized": list(hi_hits),
            "english": list(en_hits)[:10]
        }
    }
