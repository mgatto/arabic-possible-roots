# Raw Notes for Myself

## How to best include Github data sources?

https://github.com/CAMeL-Lab/ArabicChainBank


## Do we need these?

- python-bidi
- arabic_reshaper

What each does:

- `arabic_reshaper` maps Arabic letters to their contextual presentation forms (U+FE70–U+FEFF) so renderers lacking shaping show joined script.
- `python-bidi` applies the Unicode Bidirectional Algorithm to reorder RTL runs for display.

- Why they don't fit here:
- **Data path / tests**: presentation forms are different codepoints from the logical letters in alphabet.ORDER. Using them would violate the repo's Unicode/NFC policy and break the golden tests, which compare logical order (ء-ء-ب, كتب). Bidi reordering likewise changes the sequence and would corrupt the machine-readable --output TSV.
- **CLI stdout**: modern terminals already do Arabic shaping + BiDi, so enumerate-roots needs neither. docs/running.md already just says "use a terminal that renders Arabic."
- **Deps**: AGENTS.md says no new deps without justification; these would only be justified by a rendering target that can't shape/reorder on its own.

Where they could legitimately belong (future, isolated):
- A rendering/visualization layer that draws Arabic to a target with no shaping/BiDi — e.g. Pillow/matplotlib axis labels or a PDF export (a render.py/visualize CLI subcommand). There you'd take logical NFC glyphs → `arabic_reshaper` → `python-bidi` → draw, keeping the core alphabet/enumerator/attestation untouched.
- PRD 3 (transliteration output) does not need them — it's romanization, not Arabic-script display.
