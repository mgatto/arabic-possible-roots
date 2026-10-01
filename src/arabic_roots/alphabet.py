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
from enum import StrEnum
from typing import NamedTuple

from frozendict import frozendict

__all__ = [
    "GLYPH_SET",
    "LETTERS",
    "LOOKUP",
    "ORDER",
    "Letter",
    "Manner",
    "Place",
    "is_valid_glyph",
    "nfc",
    "normalize_glyph",
]


class Place(StrEnum):
    """Place of articulation (IPA-chart axis)."""

    GLOTTAL = "glottal"
    BILABIAL = "bilabial"
    DENTAL = "dental"
    POST_ALVEOLAR = "post-alveolar"
    PHARYNGEAL = "pharyngeal"
    VELAR = "velar"
    ALVEOLAR = "alveolar"
    LABIO_DENTAL = "labio-dental"
    UVULAR = "uvular"
    LABIAL_VELAR = "labial-velar"
    PALATAL = "palatal"


class Manner(StrEnum):
    """Manner of articulation (IPA-chart axis)."""

    STOP = "stop"
    FRICATIVE = "fricative"
    AFFRICATE = "affricate"
    TRILL = "trill"
    LATERAL_APPROXIMANT = "lateral-approximant"
    NASAL = "nasal"
    APPROXIMANT = "approximant"


class Letter(NamedTuple):
    """One row of the alphabet table.

    Better as a child class of ``NamedTuple`` compared to a dataclass because of
    NamedTuple's memory model and immutability.
    """

    glyph: str  # Single Arabic-script codepoint, NFC.
    name: str  # Traditional name, ASCII.
    ipa: str  # Thelwall IPA symbol, Unicode.
    din31635: str  # DIN 31635 romanization, Unicode.
    place: Place  # Place of articulation (IPA-chart axis).
    manner: Manner  # Manner of articulation (IPA-chart axis).
    emphatic: bool  # Pharyngealized (emphatic) consonant.


# Kept as a typed Python literal (not a CSV): it is Unicode-native reference
# data, not a phonotactic rule. Only the matrices are CSV because they are
# edited with page citations; the external Buckwalter scheme lives in
# data/buckwalter.csv to keep its symbols out of .py (AGENTS.md §4).
LETTERS: tuple[Letter, ...] = (
    Letter("ء", "hamza", "ʔ", "ʾ", Place.GLOTTAL, Manner.STOP, False),
    Letter("ب", "baa", "b", "b", Place.BILABIAL, Manner.STOP, False),
    Letter("ت", "taa", "t", "t", Place.DENTAL, Manner.STOP, False),
    Letter("ث", "thaa", "θ", "ṯ", Place.DENTAL, Manner.FRICATIVE, False),
    Letter("ج", "jiim", "d͡ʒ", "ǧ", Place.POST_ALVEOLAR, Manner.AFFRICATE, False),
    Letter("ح", "haa_pharyngeal", "ħ", "ḥ", Place.PHARYNGEAL, Manner.FRICATIVE, False),
    Letter("خ", "khaa", "x", "ḫ", Place.VELAR, Manner.FRICATIVE, False),
    Letter("د", "daal", "d", "d", Place.DENTAL, Manner.STOP, False),
    Letter("ذ", "dhaal", "ð", "ḏ", Place.DENTAL, Manner.FRICATIVE, False),
    Letter("ر", "raa", "r", "r", Place.ALVEOLAR, Manner.TRILL, False),
    Letter("ز", "zayn", "z", "z", Place.ALVEOLAR, Manner.FRICATIVE, False),
    Letter("س", "siin", "s", "s", Place.ALVEOLAR, Manner.FRICATIVE, False),
    Letter("ش", "shiin", "ʃ", "š", Place.POST_ALVEOLAR, Manner.FRICATIVE, False),
    Letter("ص", "saad", "sˤ", "ṣ", Place.ALVEOLAR, Manner.FRICATIVE, True),
    Letter("ض", "daad", "dˤ", "ḍ", Place.DENTAL, Manner.STOP, True),
    Letter("ط", "taa_emphatic", "tˤ", "ṭ", Place.DENTAL, Manner.STOP, True),
    Letter("ظ", "zaa", "ðˤ", "ẓ", Place.DENTAL, Manner.FRICATIVE, True),
    Letter("ع", "ayn", "ʕ", "ʿ", Place.PHARYNGEAL, Manner.FRICATIVE, False),
    Letter("غ", "ghayn", "ɣ", "ġ", Place.VELAR, Manner.FRICATIVE, False),
    Letter("ف", "faa", "f", "f", Place.LABIO_DENTAL, Manner.FRICATIVE, False),
    Letter("ق", "qaaf", "q", "q", Place.UVULAR, Manner.STOP, False),
    Letter("ك", "kaaf", "k", "k", Place.VELAR, Manner.STOP, False),
    Letter("ل", "laam", "l", "l", Place.ALVEOLAR, Manner.LATERAL_APPROXIMANT, False),
    Letter("م", "miim", "m", "m", Place.BILABIAL, Manner.NASAL, False),
    Letter("ن", "nuun", "n", "n", Place.ALVEOLAR, Manner.NASAL, False),
    Letter("ه", "haa_glottal", "h", "h", Place.GLOTTAL, Manner.FRICATIVE, False),
    Letter("و", "waaw", "w", "w", Place.LABIAL_VELAR, Manner.APPROXIMANT, False),
    Letter("ي", "yaa", "j", "y", Place.PALATAL, Manner.APPROXIMANT, False),
)

# Fixed axis order for the M_1-2/M_2-3 co-occurrence matrices.
ORDER: tuple[str, ...] = tuple(letter.glyph for letter in LETTERS)

GLYPH_SET: frozenset[str] = frozenset(ORDER)

LOOKUP: frozendict[str, Letter] = frozendict(
    {letter.glyph: letter for letter in LETTERS}
)


def nfc(text: str) -> str:
    """Return the NFC normalization of ``text``.

    This is the only function in the package that calls
    :func:`unicodedata.normalize`; every other module routes NFC through it.

    Args:
        text: Any string, typically a single Arabic glyph or a joined row.

    Returns:
        The NFC-normalized string. Idempotent: ``nfc(nfc(s)) == nfc(s)``.

    Notes:
        Total: never raises, including for non-Arabic input.
    """
    return unicodedata.normalize("NFC", text)


def normalize_glyph(glyph: str) -> str:
    """Return the NFC-normalized form of a single inventory glyph.

    Args:
        glyph: A candidate consonant, normalized to NFC before lookup.

    Returns:
        The NFC-normalized glyph, one of :data:`ORDER`.

    Raises:
        ValueError: If the normalized glyph is not in the 28-glyph inventory.

    Notes:
        Idempotent: ``normalize_glyph(normalize_glyph(g))`` equals
        ``normalize_glyph(g)``. The result is already NFC, so callers must not
        re-normalize it; route raw input through :func:`nfc` at the boundary.
    """
    normalized = nfc(glyph)
    if normalized not in GLYPH_SET:
        raise ValueError(f"Glyph not in 28-consonant inventory: {glyph!r}")
    return normalized


def is_valid_glyph(glyph: str) -> bool:
    """Return whether ``glyph`` is one of the 28 inventory consonants.

    Args:
        glyph: A candidate consonant; compared after NFC normalization.

    Returns:
        ``True`` when the NFC-normalized glyph is in :data:`ORDER`.

    Notes:
        Never raises, unlike :func:`normalize_glyph`.
    """
    return nfc(glyph) in GLYPH_SET
