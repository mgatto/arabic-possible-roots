"""Canonical Arabic consonant inventory for triliteral root enumeration.

Primary source (owned copy):
    Thelwall, Robin; Sa'adeddin, M. Akram (1999). "Arabic".
    Handbook of the International Phonetic Association.
    Cambridge University Press. pp. 51-54.

Transliteration sources:
    - DIN 31635 (reversible display/storage, canonical here).
    - IJMES scheme (output variant only, see Notes comparison table).
    - IPA symbols follow Thelwall; used for phonotactic reasoning.

Unicode policy: Arabic script glyphs are the source of truth, stored as
literal UTF-8 codepoints normalized to NFC. No Buckwalter, Arabizi, or
``\\uXXXX`` escapes in code. Romanization appears only at I/O boundaries.

Scope: 28 consonantal phonemes. Hamza is the single codepoint U+0621 (ء);
carrier variants (أ إ آ ؤ ئ) and bare alif (ا U+0627) are excluded.
See ``ORDER`` for the fixed axis order used by the co-occurrence matrices.
"""

import unicodedata
from typing import NamedTuple

from frozendict import frozendict

__all__ = [
    "CATEGORIES",
    "GLYPH_SET",
    "LETTERS",
    "LOOKUP",
    "ORDER",
    "Letter",
    "is_valid_glyph",
    "normalize_glyph",
]


# TODO shouldn't this be a dataclass?
class Letter(NamedTuple):
    """One row of the alphabet table."""

    glyph: str  # Single Arabic-script codepoint, NFC.
    name: str  # Traditional name, ASCII.
    ipa: str  # Thelwall IPA symbol, Unicode.
    din31635: str  # DIN 31635 romanization, Unicode.
    place: str  # Place of articulation (IPA-chart axis).
    manner: str  # Manner of articulation (IPA-chart axis).
    emphatic: bool  # Pharyngealized (emphatic) consonant.


# TODO maybe this should be a data file, else data like `buckwalter.csv` should be
#  hard-coded Python datastructures instead?
LETTERS: tuple[Letter, ...] = (
    # TODO maybe this should have features as headers and 1/0 as the data cell
    #  = one-shot encoding instead of string labels?
    Letter("ء", "hamza", "ʔ", "ʾ", "glottal", "stop", False),
    Letter("ب", "baa", "b", "b", "bilabial", "stop", False),
    Letter("ت", "taa", "t", "t", "dental", "stop", False),
    Letter("ث", "thaa", "θ", "ṯ", "dental", "fricative", False),
    Letter("ج", "jiim", "d͡ʒ", "ǧ", "post-alveolar", "affricate", False),
    Letter("ح", "haa_pharyngeal", "ħ", "ḥ", "pharyngeal", "fricative", False),
    Letter("خ", "khaa", "x", "ḫ", "velar", "fricative", False),
    Letter("د", "daal", "d", "d", "dental", "stop", False),
    Letter("ذ", "dhaal", "ð", "ḏ", "dental", "fricative", False),
    Letter("ر", "raa", "r", "r", "alveolar", "trill", False),
    Letter("ز", "zayn", "z", "z", "alveolar", "fricative", False),
    Letter("س", "siin", "s", "s", "alveolar", "fricative", False),
    Letter("ش", "shiin", "ʃ", "š", "post-alveolar", "fricative", False),
    Letter("ص", "saad", "sˤ", "ṣ", "alveolar", "fricative", True),
    Letter("ض", "daad", "dˤ", "ḍ", "dental", "stop", True),
    Letter("ط", "taa_emphatic", "tˤ", "ṭ", "dental", "stop", True),
    Letter("ظ", "zaa", "ðˤ", "ẓ", "dental", "fricative", True),
    Letter("ع", "ayn", "ʕ", "ʿ", "pharyngeal", "fricative", False),
    Letter("غ", "ghayn", "ɣ", "ġ", "velar", "fricative", False),
    Letter("ف", "faa", "f", "f", "labio-dental", "fricative", False),
    Letter("ق", "qaaf", "q", "q", "uvular", "stop", False),
    Letter("ك", "kaaf", "k", "k", "velar", "stop", False),
    Letter("ل", "laam", "l", "l", "alveolar", "lateral-approximant", False),
    Letter("م", "miim", "m", "m", "bilabial", "nasal", False),
    Letter("ن", "nuun", "n", "n", "alveolar", "nasal", False),
    Letter("ه", "haa_glottal", "h", "h", "glottal", "fricative", False),
    Letter("و", "waaw", "w", "w", "labial-velar", "approximant", False),
    Letter("ي", "yaa", "j", "y", "palatal", "approximant", False),
)

# Fixed axis order for the M_1-2/M_2-3 co-occurrence matrices.
ORDER: tuple[str, ...] = tuple(letter.glyph for letter in LETTERS)

GLYPH_SET: frozenset[str] = frozenset(ORDER)

LOOKUP: frozendict[str, Letter] = frozendict(
    {letter.glyph: letter for letter in LETTERS}
)

# Convenience groupings derived from LETTERS (replaces the old empty stub).
# TODO recode for McCarthy's excluding categories
CATEGORIES: frozendict[str, tuple[str, ...]] = frozendict(
    {
        "bilabials": tuple(
            letter.glyph for letter in LETTERS if letter.place == "bilabial"
        ),
        "pharyngeals": tuple(
            letter.glyph for letter in LETTERS if letter.place == "pharyngeal"
        ),
        "sibilants": tuple(
            letter.glyph
            for letter in LETTERS
            if letter.glyph in frozenset({"ز", "س", "ش", "ص", "ض", "ظ"})
        ),
        "uvulars": tuple(
            letter.glyph for letter in LETTERS if letter.place == "uvular"
        ),
        "nasals": tuple(letter.glyph for letter in LETTERS if letter.manner == "nasal"),
        "emphatics": tuple(letter.glyph for letter in LETTERS if letter.emphatic),
    }
)


def normalize_glyph(glyph: str) -> str:
    """Normalize to NFC and validate membership in the 28-glyph inventory."""
    normalized = unicodedata.normalize("NFC", glyph)
    if normalized not in GLYPH_SET:
        raise ValueError(f"Glyph not in 28-consonant inventory: {glyph!r}")
    return normalized


def is_valid_glyph(glyph: str) -> bool:
    """Return True when the NFC-normalized glyph is in the inventory."""
    return unicodedata.normalize("NFC", glyph) in GLYPH_SET
