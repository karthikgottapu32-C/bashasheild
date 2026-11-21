import unicodedata
import re
from typing import Dict, List, Tuple, Any

# Common homoglyph mappings (Cyrillic, Greek, Fullwidth to Latin ASCII)
HOMOGLYPH_MAP = {
    # Cyrillic lookalikes to Latin
    '\u0430': 'a', '\u0410': 'A', # Cyrillic a, A
    '\u0441': 'c', '\u0421': 'C', # Cyrillic c, C
    '\u0435': 'e', '\u0415': 'E', # Cyrillic e, E
    '\u0456': 'i', '\u0406': 'I', # Cyrillic Ukrainian/Byelorussian i, I
    '\u0458': 'j', '\u0408': 'J', # Cyrillic j, J
    '\u043e': 'o', '\u041e': 'O', # Cyrillic o, O
    '\u0440': 'p', '\u0420': 'P', # Cyrillic p (er), P
    '\u0455': 's', '\u0405': 'S', # Cyrillic s, S
    '\u0445': 'x', '\u0425': 'X', # Cyrillic x (ha), X
    '\u0443': 'y', '\u0423': 'Y', # Cyrillic y (u), Y
    '\u0432': 'b', '\u0412': 'B', # Cyrillic ve
    '\u043d': 'h', '\u041d': 'H', # Cyrillic en
    '\u0442': 't', '\u0422': 'T', # Cyrillic te
    '\u043c': 'm', '\u041c': 'M', # Cyrillic em
    # Greek lookalikes
    '\u03b1': 'a', '\u0391': 'A', # Greek alpha
    '\u03b2': 'b', '\u0392': 'B', # Greek beta
    '\u03b5': 'e', '\u0395': 'E', # Greek epsilon
    '\u03b9': 'i', '\u0399': 'I', # Greek iota
    '\u03ba': 'k', '\u039a': 'K', # Greek kappa
    '\u03bf': 'o', '\u039f': 'O', # Greek omicron
    '\u03c1': 'p', '\u03a1': 'P', # Greek rho
    '\u03c4': 't', '\u03a4': 'T', # Greek tau
    '\u03c5': 'u', '\u03a5': 'Y', # Greek upsilon
    '\u03bd': 'v', '\u039d': 'N', # Greek nu
    '\u03c7': 'x', '\u03a7': 'X', # Greek chi
}

# Zero-width and invisible control characters often used for evasion
ZERO_WIDTH_CHARS = {
    '\u200b', # Zero-width space
    '\u200c', # Zero-width non-joiner
    '\u200d', # Zero-width joiner
    '\ufeff', # Zero-width no-break space / BOM
    '\u200e', # Left-to-right mark
    '\u200f', # Right-to-left mark
    '\u202a', '\u202b', '\u202c', '\u202d', '\u202e', # Bidi embedding
    '\u2060', # Word joiner
    '\u00ad', # Soft hyphen
}

class NormalizedInput:
    def __init__(
        self,
        raw_text: str,
        normalized_text: str,
        offset_map: List[int],
        detected_anomalies: List[str],
        obfuscation_score: float
    ):
        self.raw_text = raw_text
        self.normalized_text = normalized_text
        self.offset_map = offset_map
        self.detected_anomalies = detected_anomalies
        self.obfuscation_score = obfuscation_score

    def map_span_to_raw(self, norm_start: int, norm_end: int) -> Tuple[int, int, str]:
        """
        Maps character span in normalized text back to original character coordinates in raw_text.
        """
        if not self.offset_map or norm_start >= len(self.offset_map):
            return norm_start, norm_end, self.raw_text[norm_start:norm_end]

        raw_start = self.offset_map[norm_start]
        last_norm_idx = min(norm_end - 1, len(self.offset_map) - 1)
        raw_end = self.offset_map[last_norm_idx] + 1

        # Clamp within raw text bounds
        raw_start = max(0, min(raw_start, len(self.raw_text)))
        raw_end = max(raw_start, min(raw_end, len(self.raw_text)))

        return raw_start, raw_end, self.raw_text[raw_start:raw_end]

def is_indic_codepoint(char: str) -> bool:
    """Checks if character belongs to South Asian / Indic Unicode blocks (0x0900 - 0x0D7F)."""
    return 0x0900 <= ord(char) <= 0x0D7F

def is_legitimate_indic_joiner(raw_text: str, idx: int) -> bool:
    """
    Checks if ZWNJ (\u200c) or ZWJ (\u200d) is legitimate Indic orthography (used for virama/half-forms)
    as defined by the Unicode Standard, rather than an evasion obfuscation.
    """
    char = raw_text[idx]
    if char not in ('\u200c', '\u200d'):
        return False
    prev_is_indic = (idx > 0 and is_indic_codepoint(raw_text[idx - 1]))
    next_is_indic = (idx < len(raw_text) - 1 and is_indic_codepoint(raw_text[idx + 1]))
    return prev_is_indic or next_is_indic

def normalize_input(raw_text: str) -> NormalizedInput:
    """
    Layer 1 Input Normalization:
    - Unicode NFKC canonical decomposition & compatibility composition.
    - Zero-width character stripping while maintaining offset mapping.
    - Cross-script Unicode homoglyph normalization.
    - Spacing anomaly collapse (e.g. 'i g n o r e' -> 'ignore').
    - Detection of encoding and obfuscation attempts.
    """
    anomalies: List[str] = []
    obfuscation_score = 0.0

    # Step 1: Detect suspicious zero-width characters (excluding legitimate Indic grammatical ZWNJ/ZWJ or educational typography definitions)
    is_unicode_typography_discussion = bool(re.search(
        r'\b(?:zero-width|zwnj|zwj|unicode|typography|virama|half-forms?|ligatures?)\b',
        raw_text,
        re.IGNORECASE
    ))
    suspicious_zw_count = sum(
        1 for i, c in enumerate(raw_text)
        if c in ZERO_WIDTH_CHARS and not is_legitimate_indic_joiner(raw_text, i)
    )
    if is_unicode_typography_discussion and suspicious_zw_count <= 2:
        # Isolated illustrative ZWJ/ZWNJ in educational typography context is benign
        suspicious_zw_count = 0

    if suspicious_zw_count > 0:
        anomalies.append(f"ZERO_WIDTH_CHARACTERS ({suspicious_zw_count} characters detected)")
        obfuscation_score += min(35.0, suspicious_zw_count * 10.0)

    # Step 2: Unicode NFKC normalization character by character with offset mapping
    norm_chars = []
    offset_map = []
    homoglyph_count = 0

    for raw_idx, char in enumerate(raw_text):
        if char in ZERO_WIDTH_CHARS:
            continue

        # Check homoglyph mapping
        if char in HOMOGLYPH_MAP:
            norm_c = HOMOGLYPH_MAP[char]
            homoglyph_count += 1
        else:
            norm_c = unicodedata.normalize('NFKC', char)

        for c in norm_c:
            norm_chars.append(c)
            offset_map.append(raw_idx)

    if homoglyph_count > 0:
        anomalies.append(f"UNICODE_HOMOGLYPH_SUBSTITUTION ({homoglyph_count} characters normalized)")
        obfuscation_score += min(40.0, homoglyph_count * 8.0)

    intermediate_text = "".join(norm_chars)

    # Step 3: Detect inter-character spacing anomalies (e.g., 'i g n o r e   a l l   p r e v i o u s')
    # Match sequences of single alphanumeric characters separated by single whitespace (preserving word gaps)
    spaced_word_pattern = re.compile(r'(?:(?<=\s)|^)([a-zA-Z0-9] ){1,}[a-zA-Z0-9](?=\s|$)')

    final_chars = []
    final_offset_map = []
    spacing_anomaly_detected = False

    i = 0
    while i < len(intermediate_text):
        match = spaced_word_pattern.match(intermediate_text, i)
        if match and len([c for c in match.group(0) if not c.isspace()]) >= 2:
            spacing_anomaly_detected = True
            matched_slice = match.group(0)
            for sub_idx, char in enumerate(matched_slice):
                if not char.isspace():
                    final_chars.append(char)
                    final_offset_map.append(offset_map[i + sub_idx])
            i += len(matched_slice)
        else:
            final_chars.append(intermediate_text[i])
            final_offset_map.append(offset_map[i])
            i += 1

    if spacing_anomaly_detected:
        anomalies.append("CHARACTER_SPACING_EVASION (inter-character whitespace collapse applied)")
        obfuscation_score += 35.0

    final_text = "".join(final_chars)

    # Step 4: Detect Base64 or Hex Obfuscation patterns
    b64_pattern = re.compile(r'\b[A-Za-z0-9+/]{24,}={0,2}\b')
    hex_pattern = re.compile(r'\b(?:0x)?[0-9a-fA-F]{24,}\b')
    if b64_pattern.search(final_text):
        anomalies.append("POTENTIAL_BASE64_OBFUSCATION")
        obfuscation_score += 20.0
    if hex_pattern.search(final_text):
        anomalies.append("POTENTIAL_HEX_OBFUSCATION")
        obfuscation_score += 20.0

    return NormalizedInput(
        raw_text=raw_text,
        normalized_text=final_text,
        offset_map=final_offset_map,
        detected_anomalies=anomalies,
        obfuscation_score=min(100.0, obfuscation_score)
    )
