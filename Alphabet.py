"""
Primary Source

**I own a copy**
Thelwall, Robin; Sa'adeddin, M. Akram (1999). "Arabic". Handbook of the International Phonetic Association. Cambridge University Press. pp. 51–54.

Source for Transliteration Schemes
- IJMES PDF

"""

from frozendict import frozendict

"""

## Horizontal Axis (Columns): Called the Place of Articulation. 

This indicates where in the mouth or throat the sound is produced:
- bilabial
- labio-dental
- dental
- alveolar
- post-alveolar
- palatal
- velar
- uvular
- pharyngeal
    - epiglottal? IPA still categorizes them as pharyngeal
- glottal

Emphatics (Pharyngealized Consonants) are seemingly set out as a line item outside the IPA chart!


It moves from the front of the mouth (left) to the back of the throat (right).


## Vertical Axis (Rows): Called the Manner of Articulation. 

This indicates how the airflow is obstructed to make the sound:
- plosive
- nasal
- fricative
- affricate
- trill 
- approximant
- lateral-approximant
"""

"""
The International Phonetic Alphabet (IPA) table for Modern Standard Arabic (MSA) maps each Arabic letter to its corresponding phonetic symbol and description. [1, 2]
## Arabic Consonants

| Arabic Letter | Name | IPA Symbol | Description |
|---|---|---|---|
| ء / أ | hamza | [ʔ] | Glottal stop |
| ب | baa' | [b] | Voiced bilabial stop |
| ت | taa' | [t] | Voiceless dento-alveolar stop |
| ث | thaa' | [θ] | Voiceless interdental fricative |
| ج | jiim | [d͡ʒ] (or [ʒ]) | Voiced palato-alveolar affricate (or voiced postalveolar fricative) |
| ح | Haa' | [ħ] | Voiceless pharyngeal fricative |
| خ | khaa' | [x] | Voiceless velar/uvular fricative |
| د | daal | [d] | Voiced dento-alveolar stop |
| ذ | dhaal | [ð] | Voiced interdental fricative |
| ر | raa' | [r] (or [ɾ]) | Alveolar trill or tap |
| ز | zayn | [z] | Voiced alveolar fricative |
| س | siin | [s] | Voiceless alveolar fricative |
| ش | shiin | [ʃ] | Voiceless postalveolar fricative |
| ص | Saad | [sˤ] | Pharyngealized/emphatic voiceless alveolar fricative |
| ض | Daad | [dˤ] | Pharyngealized/emphatic voiced dental stop |
| ط | Taa' | [tˤ] | Pharyngealized/emphatic voiceless dental stop |
| ظ | Zaa' | [ðˤ] (or [zˤ]) | Pharyngealized/emphatic voiced interdental fricative |
| ع | ‘ayn | [ʕ] | Voiced pharyngeal fricative/approximant |
| غ | ghayn | [ɣ] | Voiced velar/uvular fricative |
| ف | faa' | [f] | Voiceless labiodental fricative |
| ق | qaaf | [q] | Voiceless uvular stop |
| ك | kaaf | [k] | Voiceless velar stop |
| ل | laam | [l] (or [lɫ]) | Alveolar lateral approximant (velarized in Allah) |
| م | miim | [m] | Bilabial nasal |
| ن | nuun | [n] | Alveolar nasal |
| ه | haa' | [h] | Voiceless glottal fricative |
| و | waaw | [w] | Voiced labial-velar approximant |
| ي | yaa' | [j] | Voiced palatal approximant |


ayn romanization = U+02BF ʿ
hamza romanization = U+02BE ʾ
"""

from typing import NamedTuple


# List entries are the keys to the Pandas alphabet table
categories = frozendict(
    {
        "bilabials": [""],
        "pharyngals": [],
        "sibilants": [],
        "uvulars": [],
        "nasals": [],
        "emphatics": [],
    }
)


# 1. Define the column headers and types once
class EmployeeRow(NamedTuple):
    name: str
    age: int
    role: str


# 2. Build the table using a standard list
table = [
    EmployeeRow("Alice", 25, "Engineer"),
    EmployeeRow("Bob", 30, "Designer"),
    EmployeeRow("Charlie", 28, "Manager"),
]

# 3. Access data cleanly using header names
print(table[0].name)  # Output: Alice
print(table[1].role)  # Output: Designer


class Alphabet:
    def __init__(self):
        pass
