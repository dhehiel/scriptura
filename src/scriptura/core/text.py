"""Text normalisation and diacritic folding.

Normative source: BKB-DATA-001 section 7; ADR-0009.

WHY THIS MODULE EXISTS
----------------------
SQLite's FTS5 ``unicode61 remove_diacritics 2`` option was verified on SQLite 3.40.1
to fold LATIN diacritics (``Deésus`` matches ``Deesus``) but NOT Greek polytonic
diacritics (``λόγος`` does not match ``λογος``) and NOT Hebrew niqqud (``אֱלֹהִים``
does not match ``אלהים``).

Since accent-insensitive search over Greek and Hebrew is a hard requirement for this
domain, folding is performed EXPLICITLY here, at index time, and the folded form is
indexed alongside the stored text.

The stored text is NEVER altered. Diacritic folding is a SEARCH affordance only
(BKB-DATA-001 rule U6). Byte-exact comparison uses the stored text; folded matching
uses the folded form.
"""

from __future__ import annotations

import unicodedata

__all__ = [
    "DEFAULT_NORMALISATION_FORM",
    "STRIPPED_CATEGORIES",
    "fold_diacritics",
    "is_folded",
    "strip_marks",
]

#: The default normalisation form for stored original-language text.
DEFAULT_NORMALISATION_FORM = "NFC"

#: Unicode general categories removed when folding. ``Mn`` (non-spacing mark) covers
#: Greek combining accents produced by NFD decomposition and Hebrew niqqud and
#: cantillation. ``Me`` (enclosing mark) is included for completeness. ``Mc``
#: (spacing combining mark) is deliberately KEPT, because spacing marks can carry
#: lexical meaning in some scripts.
STRIPPED_CATEGORIES = frozenset({"Mn", "Me"})


def strip_marks(text: str) -> str:
    """Return *text* with combining marks in :data:`STRIPPED_CATEGORIES` removed.

    Decomposes to NFD first, so that precomposed characters such as ``λόγος`` expose
    their combining accents, then removes the marks, then recomposes to NFC.

    This is what makes ``λόγος`` and ``λογος`` comparable, and ``אֱלֹהִים`` and
    ``אלהים`` comparable.
    """
    decomposed = unicodedata.normalize("NFD", text)
    kept = [
        char for char in decomposed
        if unicodedata.category(char) not in STRIPPED_CATEGORIES
    ]
    return unicodedata.normalize("NFC", "".join(kept))


def fold_diacritics(text: str) -> str:
    """Return a diacritic-folded form of *text*, for SEARCH MATCHING ONLY.

    Folds Greek polytonic diacritics, Hebrew niqqud and cantillation, and Latin
    diacritics. Does NOT transliterate or romanize: ``λόγος`` folds to a form
    without diacritics, not to ``logos``. Romanization is a different operation with
    different semantics and is not performed here.

    Case is folded in a folding-consistent way: the same transform is applied to
    indexed text and to queries, so case differences never affect matching, and
    Greek final sigma (U+03C2) is normalised to medial sigma (U+03C3) so that a
    word matches regardless of its position in a phrase.

    The folded form is used to populate a separate indexed column. The stored text is
    never replaced by it.
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}.")
    folded = strip_marks(text).casefold()
    return folded.replace("ς", "σ")


def is_folded(text: str) -> bool:
    """Return whether *text* is already equal to its own folded form."""
    return fold_diacritics(text) == text
