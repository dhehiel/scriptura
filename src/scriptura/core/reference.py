"""Canonical Bible references, the book registry, and canon profiles.

Normative source: BKB-DATA-001 section 3.

A reference must be unambiguous, stable, comparable, and independent of any single
edition's numbering. Different editions divide chapters and verses differently; the
reference system represents that without loss and records divergence rather than
forcing it (rule R8).

Books are identified by STABLE KEYS, never by display names, which vary by language
and tradition. Canon membership is a property of a PROFILE, not of a text: the same
book may be scripture in one profile and not in another. Scriptura records profiles;
it endorses none.

The book-key vocabulary and reference abbreviations follow the scheme published by
STEPBible-Data (retrieved 2026-11-05), which Scriptura adopts for interoperability.
That scheme is recorded in docs/data/source-registry.json as src-stepbible-data.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterator, Mapping, Sequence

from .errors import ReferenceError

__all__ = [
    "Book",
    "CanonProfile",
    "Reference",
    "BOOKS",
    "CANON_PROFILES",
    "DEFAULT_CANON_PROFILE",
    "get_book",
    "get_profile",
    "book_keys_for_profile",
    "parse_reference",
    "parse_references",
    "is_single_chapter_book",
]


@dataclass(frozen=True)
class Book:
    """A book in the registry.

    Attributes:
        key: Stable identifier. Never a display name.
        name_en: English display name.
        aliases: Accepted alternative abbreviations, lower-cased for lookup.
        chapters: Chapter count for validation, or ``None`` where the count is
            edition-dependent and therefore NOT asserted. Recording ``None`` is the
            honest choice: an unverified count must not be presented as a constraint.
        testament: ``ot``, ``nt``, or ``deuterocanonical``.
        notes: Edition-divergence notes.
    """

    key: str
    name_en: str
    aliases: tuple[str, ...]
    chapters: int | None
    testament: str
    notes: str = ""


@dataclass(frozen=True)
class CanonProfile:
    """An arrangement of books.

    A profile does NOT assert canonicity; it records an arrangement. Adding a profile
    is an extension at a defined seam and must not alter an existing profile.
    """

    key: str
    name: str
    description: str
    book_keys: tuple[str, ...]


@dataclass(frozen=True)
class Reference:
    """A canonical reference.

    Immutable once constructed (invariant R1).
    """

    book: str
    canon_profile: str
    chapter: int | None = None
    verse_start: int | None = None
    verse_end: int | None = None
    display: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "book", _require_book_key(self.book))
        object.__setattr__(self, "canon_profile", _require_profile_key(self.canon_profile))
        _validate_numbers(self)
        if self.display is None:
            object.__setattr__(self, "display", format_reference(self))

    @property
    def is_whole_book(self) -> bool:
        return self.chapter is None

    @property
    def is_chapter_level(self) -> bool:
        return self.chapter is not None and self.verse_start is None

    @property
    def is_single_verse(self) -> bool:
        return self.verse_start is not None and (
            self.verse_end is None or self.verse_end == self.verse_start
        )

    @property
    def is_range(self) -> bool:
        return (
            self.verse_start is not None
            and self.verse_end is not None
            and self.verse_end > self.verse_start
        )

    def sort_key(self) -> tuple[int, int, int, int]:
        """Return a total order within the profile (invariant R6)."""
        book = get_book(self.book)
        profile = get_profile(self.canon_profile)
        try:
            position = profile.book_keys.index(book.key)
        except ValueError:  # pragma: no cover - guarded by _validate_membership
            position = 0
        return (
            position,
            self.chapter or 0,
            self.verse_start or 0,
            self.verse_end or self.verse_start or 0,
        )

    def to_dict(self) -> dict[str, object]:
        """Serialise. ``layer``-independent; see BKB-DATA-001 section 9.2."""
        return {
            "book": self.book,
            "canon_profile": self.canon_profile,
            "chapter": self.chapter,
            "verse_start": self.verse_start,
            "verse_end": self.verse_end,
            "display": self.display,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "Reference":
        """Deserialise, validating strictly."""
        return cls(
            book=str(data["book"]),
            canon_profile=str(data["canon_profile"]),
            chapter=_opt_int(data.get("chapter")),
            verse_start=_opt_int(data.get("verse_start")),
            verse_end=_opt_int(data.get("verse_end")),
            display=None if data.get("display") is None else str(data["display"]),
        )


# --------------------------------------------------------------------- helpers ----


def _opt_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ReferenceError(f"Reference component must be an integer or null, got bool.")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    raise ReferenceError(f"Reference component must be an integer or null, got {value!r}.")


def _validate_numbers(ref: Reference) -> None:
    """Enforce reference invariants R2, R3."""
    if ref.chapter is not None and ref.chapter <= 0:
        raise ReferenceError(f"Chapter must be a positive integer, got {ref.chapter!r}.")
    if ref.verse_start is not None and ref.verse_start <= 0:
        raise ReferenceError(
            f"Verse must be a positive integer, got {ref.verse_start!r}."
        )
    if ref.verse_end is not None and ref.verse_start is None:
        raise ReferenceError(
            "verse_end requires verse_start (a verse range cannot start nowhere)."
        )
    if (
        ref.verse_start is not None
        and ref.verse_end is not None
        and ref.verse_end < ref.verse_start
    ):
        raise ReferenceError(
            f"Inverted verse range: verse_end {ref.verse_end} < verse_start "
            f"{ref.verse_start}. Guessing a reference is a source-integrity violation."
        )
    if ref.chapter is None and ref.verse_start is not None:
        raise ReferenceError("A verse reference requires a chapter, except for "
                             "single-chapter books where chapter 1 is implicit.")


# ---------------------------------------------------------------- book registry ----

_OT = (
    ("Gen", "Genesis", 50), ("Exo", "Exodus", 40), ("Lev", "Leviticus", 27),
    ("Num", "Numbers", 36), ("Deu", "Deuteronomy", 34), ("Jos", "Joshua", 24),
    ("Jdg", "Judges", 21), ("Rut", "Ruth", 4), ("1Sa", "1 Samuel", 31),
    ("2Sa", "2 Samuel", 24), ("1Ki", "1 Kings", 22), ("2Ki", "2 Kings", 25),
    ("1Ch", "1 Chronicles", 29), ("2Ch", "2 Chronicles", 36), ("Ezr", "Ezra", 10),
    ("Neh", "Nehemiah", 13), ("Est", "Esther", 10), ("Job", "Job", 42),
    ("Psa", "Psalms", 150), ("Pro", "Proverbs", 31), ("Ecc", "Ecclesiastes", 12),
    ("Sng", "Song of Songs", 8), ("Isa", "Isaiah", 66), ("Jer", "Jeremiah", 52),
    ("Lam", "Lamentations", 5), ("Ezk", "Ezekiel", 48), ("Dan", "Daniel", 12),
    ("Hos", "Hosea", 14), ("Jol", "Joel", 3), ("Amo", "Amos", 9),
    ("Oba", "Obadiah", 1), ("Jon", "Jonah", 4), ("Mic", "Micah", 7),
    ("Nam", "Nahum", 3), ("Hab", "Habakkuk", 3), ("Zep", "Zephaniah", 3),
    ("Hag", "Haggai", 2), ("Zec", "Zechariah", 14), ("Mal", "Malachi", 4),
)

_NT = (
    ("Mat", "Matthew", 28), ("Mrk", "Mark", 16), ("Luk", "Luke", 24),
    ("Jhn", "John", 21), ("Act", "Acts", 28), ("Rom", "Romans", 16),
    ("1Co", "1 Corinthians", 16), ("2Co", "2 Corinthians", 13), ("Gal", "Galatians", 6),
    ("Eph", "Ephesians", 6), ("Php", "Philippians", 4), ("Col", "Colossians", 4),
    ("1Th", "1 Thessalonians", 5), ("2Th", "2 Thessalonians", 3),
    ("1Ti", "1 Timothy", 6), ("2Ti", "2 Timothy", 4), ("Tit", "Titus", 3),
    ("Phm", "Philemon", 1), ("Heb", "Hebrews", 13), ("Jas", "James", 5),
    ("1Pe", "1 Peter", 5), ("2Pe", "2 Peter", 3), ("1Jn", "1 John", 5),
    ("2Jn", "2 John", 1), ("3Jn", "3 John", 1), ("Jud", "Jude", 1),
    ("Rev", "Revelation", 22),
)

# Chapter counts for the deuterocanonical books are NOT asserted: they are
# edition-dependent and vary between the Catholic, Orthodox and Rahlfs-Hanhart
# arrangements. Recording None means "not validated", which is the honest state.
# An unverified count must not be presented as a constraint.
_DEUTEROCANONICAL = (
    ("Tob", "Tobit"), ("Jdt", "Judith"), ("EsG", "Esther (Greek additions)"),
    ("Wis", "Wisdom of Solomon"), ("Sir", "Sirach / Ecclesiasticus"), ("Bar", "Baruch"),
    ("LJe", "Letter of Jeremiah"), ("S3Y", "Song of the Three Young Men"),
    ("Sus", "Susanna"), ("Bel", "Bel and the Dragon"), ("1Ma", "1 Maccabees"),
    ("2Ma", "2 Maccabees"), ("3Ma", "3 Maccabees"), ("4Ma", "4 Maccabees"),
    ("1Es", "1 Esdras"), ("2Es", "2 Esdras / 4 Ezra"), ("Man", "Prayer of Manasseh"),
    ("Ps2", "Psalm 151"), ("Oda", "Odes"), ("PsS", "Psalms of Solomon"),
)

_MAL_NOTE = (
    "Chapter count is edition-dependent: 4 chapters in most English editions, 3 in the "
    "Hebrew and Masoretic tradition, where what is numbered 4:1-6 in English editions is "
    "3:19-24. This divergence is RECORDED, not reconciled (BKB-DATA-001 rule R8)."
)


def _build_books() -> dict[str, Book]:
    books: dict[str, Book] = {}
    for key, name, chapters in _OT:
        notes = _MAL_NOTE if key == "Mal" else ""
        books[key] = Book(
            key=key, name_en=name, aliases=_aliases_for(key, name),
            chapters=chapters, testament="ot", notes=notes,
        )
    for key, name, chapters in _NT:
        books[key] = Book(
            key=key, name_en=name, aliases=_aliases_for(key, name),
            chapters=chapters, testament="nt",
        )
    for key, name in _DEUTEROCANONICAL:
        books[key] = Book(
            key=key, name_en=name, aliases=_aliases_for(key, name),
            chapters=None, testament="deuterocanonical",
            notes=(
                "Chapter count is edition-dependent across Catholic, Orthodox and "
                "Rahlfs-Hanhart arrangements, and is therefore NOT asserted here."
            ),
        )
    return books


def _aliases_for(key: str, name_en: str) -> tuple[str, ...]:
    """Derive accepted aliases from the key and the English name.

    Aliases are for PARSING convenience. Lookup is case-insensitive. The canonical
    key is never replaced by an alias in stored data.
    """
    aliases = {key.lower()}
    name_parts = name_en.replace("/", " ").split()
    if name_parts:
        aliases.add(name_parts[0].lower())
        aliases.add(" ".join(name_parts).lower())
    # Ordinal books: accept arabic and roman numerals, paired with the key stem, the
    # full English name, and the conventional three-letter truncation. This covers the
    # forms people actually write: "2 Sam", "II Sam", "2 Samuel", "IISamuel", "1 Jn".
    match = re.match(r"^([1-4])([A-Za-z]+)$", key)
    if match:
        numeral, stem = match.group(1), match.group(2)
        roman = {"1": "i", "2": "ii", "3": "iii", "4": "iv"}[numeral]
        stems = {stem.lower()}
        if len(name_parts) > 1:
            rest = " ".join(name_parts[1:])
            stems.add(rest.lower())
            if len(name_parts[1]) >= 3:
                stems.add(name_parts[1][:3].lower())
        for prefix in (numeral, roman):
            for separator in ("", " "):
                for form in stems:
                    aliases.add(f"{prefix}{separator}{form}")
    # Common long forms.
    long_forms = {
        "jhn": ("john", "joh", "jn"), "mrk": ("mark", "mk"), "mat": ("matthew", "matt", "mt"),
        "luk": ("luke", "lk"), "act": ("acts",), "rev": ("revelation", "apocalypse", "apoc"),
        "sng": ("song of solomon", "song of songs", "canticles", "canticle of canticles", "sos"),
        "ecc": ("ecclesiastes", "qoheleth", "qoh"), "pro": ("proverbs", "prov"),
        "psa": ("psalms", "psalm", "ps"), "est": ("esther",), "isa": ("isaiah", "is"),
        "jer": ("jeremiah", "jer"), "ezk": ("ezekiel", "eze", "ezechiel"),
        "dan": ("daniel", "dan"), "nam": ("nahum", "nah"), "phm": ("philemon", "philem"),
        "jas": ("james", "jam"), "jud": ("jude",), "heb": ("hebrews",),
        "jdg": ("judges",), "jos": ("joshua", "josh"), "jdt": ("judith",),
        "wis": ("wisdom",), "sir": ("sirach", "ecclesiasticus"),
    }
    aliases.update(long_forms.get(key.lower(), ()))
    return tuple(sorted(aliases))


BOOKS: Mapping[str, Book] = _build_books()


# ------------------------------------------------------------- canon profiles ----

_OT_KEYS = tuple(key for key, _, _ in _OT)
_NT_KEYS = tuple(key for key, _, _ in _NT)
_DC_KEYS = tuple(key for key, _ in _DEUTEROCANONICAL)

# The Catholic canon is 73 books: 46 Old Testament and 27 New Testament. The count
# of 46 arises because the Catholic enumeration treats the Greek additions to Esther
# and to Daniel as PART OF those books, and the Letter of Jeremiah as part of Baruch.
# Those additions are registered separately in BOOKS (EsG, S3Y, Sus, Bel, LJe) for
# editions that treat them as distinct units, but they are NOT counted as separate
# books in this profile. Adding all twelve deuterocanonical keys here would yield 78,
# which is not the Catholic canon.
#
# Books excluded from the Catholic enumeration (3 and 4 Maccabees, 1 and 2 Esdras, the
# Prayer of Manasseh, Psalm 151, the Odes, and the Psalms of Solomon) appear in the
# wider Orthodox arrangement.
_CATHOLIC_DC = ("Tob", "Jdt", "Wis", "Sir", "Bar", "1Ma", "2Ma")

# The wider Orthodox arrangement, as commonly enumerated.
_ORTHODOX_DC = ("Tob", "Jdt", "EsG", "Wis", "Sir", "Bar", "LJe", "S3Y", "Sus", "Bel",
                "1Ma", "2Ma", "3Ma", "4Ma", "1Es", "2Es", "Man", "Ps2", "Oda", "PsS")

# The Tanakh arrangement: Torah, Prophets, Writings.
_TANAKH = (
    "Gen", "Exo", "Lev", "Num", "Deu",
    "Jos", "Jdg", "1Sa", "2Sa", "1Ki", "2Ki", "Isa", "Jer", "Ezk",
    "Hos", "Jol", "Amo", "Oba", "Jon", "Mic", "Nam", "Hab", "Zep", "Hag", "Zec", "Mal",
    "Psa", "Job", "Pro", "Rut", "Sng", "Ecc", "Lam", "Est", "Dan", "Ezr", "Neh", "1Ch", "2Ch",
)


def _interleave(ot: Sequence[str], dc: Sequence[str], nt: Sequence[str]) -> tuple[str, ...]:
    """Interleave deuterocanonical books into the OT sequence at conventional points."""
    position = {
        "Tob": "Est", "Jdt": "Est", "EsG": "Est", "Wis": "Sng", "Sir": "Sng",
        "Bar": "Jer", "LJe": "Lam", "S3Y": "Dan", "Sus": "Dan", "Bel": "Dan",
        "1Ma": "Mal", "2Ma": "Mal", "3Ma": "Mal", "4Ma": "Mal", "1Es": "Ezr",
        "2Es": "Ezr", "Man": "Psa", "Ps2": "Psa", "Oda": "Psa", "PsS": "Psa",
    }
    out: list[str] = []
    pending: dict[str, list[str]] = {}
    for key in dc:
        pending.setdefault(position.get(key, "Mal"), []).append(key)
    for key in ot:
        out.append(key)
        out.extend(pending.pop(key, []))
    for leftovers in pending.values():
        out.extend(leftovers)
    return tuple(out) + tuple(nt)


CANON_PROFILES: Mapping[str, CanonProfile] = {
    p.key: p
    for p in (
        CanonProfile(
            key="protestant_66",
            name="Protestant 66-book canon",
            description=(
                "39 Old Testament books and 27 New Testament books. Records an "
                "arrangement; does not assert canonicity."
            ),
            book_keys=_OT_KEYS + _NT_KEYS,
        ),
        CanonProfile(
            key="catholic_73",
            name="Catholic 73-book canon",
            description=(
                "46 Old Testament books and 27 New Testament books, totalling 73. The "
                "Greek additions to Esther and Daniel and the Letter of Jeremiah are "
                "counted WITHIN Esther, Daniel and Baruch respectively, as the Catholic "
                "enumeration does; they are registered separately in the book registry "
                "for editions that treat them as distinct units. Records an arrangement; "
                "does not assert canonicity."
            ),
            book_keys=_interleave(_OT_KEYS, _CATHOLIC_DC, _NT_KEYS),
        ),
        CanonProfile(
            key="orthodox_broad",
            name="Wider Orthodox canon",
            description=(
                "The wider Orthodox arrangement, including 3 and 4 Maccabees, 1 and 2 "
                "Esdras, the Prayer of Manasseh, Psalm 151, the Odes, and the Psalms of "
                "Solomon. Enumeration varies between Orthodox traditions; this profile "
                "records ONE common arrangement and does not assert canonicity."
            ),
            book_keys=_interleave(_OT_KEYS, _ORTHODOX_DC, _NT_KEYS),
        ),
        CanonProfile(
            key="hebrew_bible_24",
            name="Tanakh (Hebrew Bible) arrangement",
            description=(
                "Torah, Prophets and Writings, enumerated as 39 books for reference "
                "purposes. The traditional count of 24 arises from combining Samuel, "
                "Kings, Chronicles, Ezra-Nehemiah and the Twelve; that combination is "
                "an editorial convention and is NOT applied here. Records an "
                "arrangement; does not assert canonicity."
            ),
            book_keys=_TANAKH,
        ),
        CanonProfile(
            key="nt_27",
            name="New Testament only",
            description="The 27-book New Testament. Records an arrangement.",
            book_keys=_NT_KEYS,
        ),
        CanonProfile(
            key="deuterocanonical",
            name="Deuterocanonical books only",
            description=(
                "The deuterocanonical books, for work that concerns them specifically. "
                "Records an arrangement."
            ),
            book_keys=_DC_KEYS,
        ),
    )
}

#: The profile used when a caller does not specify one. This is a CONVENIENCE for
#: parsing, never an assertion of canonicity.
DEFAULT_CANON_PROFILE = "protestant_66"


# ------------------------------------------------------------------ lookups ----

_ALIAS_INDEX: dict[str, str] = {}
for _book in BOOKS.values():
    _ALIAS_INDEX[_book.key.lower()] = _book.key
    _ALIAS_INDEX[_book.name_en.lower()] = _book.key
    for _alias in _book.aliases:
        _ALIAS_INDEX.setdefault(_alias.lower(), _book.key)


def get_book(key_or_alias: str) -> Book:
    """Return the :class:`Book` for *key_or_alias*.

    Lookup is case-insensitive and accepts registered aliases. It is STRICT: an
    unresolvable key raises rather than returning a best guess (invariant R4).

    Raises:
        ReferenceError: if the key is not in the registry.
    """
    if not isinstance(key_or_alias, str) or not key_or_alias.strip():
        raise ReferenceError("Book key must be a non-empty string.")
    normalised = " ".join(key_or_alias.strip().lower().split())
    resolved = _ALIAS_INDEX.get(normalised)
    if resolved is None:
        raise ReferenceError(
            f"Unknown book {key_or_alias!r}. It is not in the book registry. "
            f"Guessing a reference is a source-integrity violation; adding a book is "
            f"an extension at a defined seam and requires a schema update."
        )
    return BOOKS[resolved]


def get_profile(key: str) -> CanonProfile:
    """Return the :class:`CanonProfile` for *key*.

    Raises:
        ReferenceError: if the profile is not registered.
    """
    if not isinstance(key, str) or not key.strip():
        raise ReferenceError("Canon profile key must be a non-empty string.")
    try:
        return CANON_PROFILES[key.strip()]
    except KeyError:
        raise ReferenceError(
            f"Unknown canon profile {key!r}. Registered profiles: "
            + ", ".join(sorted(CANON_PROFILES))
            + ". A reference is valid only relative to a named profile (rule R5)."
        ) from None


def book_keys_for_profile(profile_key: str) -> tuple[str, ...]:
    """Return the ordered book keys of *profile_key*."""
    return get_profile(profile_key).book_keys


def is_single_chapter_book(key_or_alias: str) -> bool:
    """Return whether the book has a single chapter, so chapter 1 is implicit."""
    book = get_book(key_or_alias)
    return book.chapters == 1


def _require_book_key(key: str) -> str:
    """Validate that *key* is a registry key and return the canonical key."""
    return get_book(key).key


def _require_profile_key(key: str) -> str:
    return get_profile(key).key


def validate_membership(ref: Reference) -> Reference:
    """Validate *ref* against its canon profile and chapter count.

    Enforces invariants R4 and R5, and validates chapter numbers where the registry
    asserts a count. Where the registry records ``None`` the count is NOT validated,
    because an unverified count must not be enforced as a constraint.

    Raises:
        ReferenceError: if the book is not in the profile, or the chapter is out of range.
    """
    profile = get_profile(ref.canon_profile)
    if ref.book not in profile.book_keys:
        raise ReferenceError(
            f"Book {ref.book!r} is not part of canon profile {ref.canon_profile!r}. "
            f"A reference is valid only relative to a named profile (rule R5). Canon "
            f"membership is a property of a profile, not of a text."
        )
    book = get_book(ref.book)
    if ref.chapter is not None and book.chapters is not None and ref.chapter > book.chapters:
        raise ReferenceError(
            f"Chapter {ref.chapter} is out of range for {book.name_en} "
            f"({book.key}), which has {book.chapters} chapters in the registry. "
            f"{book.notes}".strip()
        )
    return ref


# --------------------------------------------------------------- formatting ----


def format_reference(ref: Reference, use_display_name: bool = False) -> str:
    """Return a human-readable form of *ref*.

    Display strings are DERIVED from a reference (rule R7). They are never parsed
    from an untrusted display string without validation.
    """
    book = get_book(ref.book)
    label = book.name_en if use_display_name else book.key
    if ref.chapter is None:
        return label
    if ref.verse_start is None:
        return f"{label} {ref.chapter}"
    if ref.verse_end is None or ref.verse_end == ref.verse_start:
        return f"{label} {ref.chapter}:{ref.verse_start}"
    return f"{label} {ref.chapter}:{ref.verse_start}-{ref.verse_end}"


# ------------------------------------------------------------------ parsing ----

_BOOK_PATTERN = r"(?P<book>[1-4]?\s?[A-Za-z][A-Za-z. ]*?)"
_CHAPTER_PATTERN = r"(?:\s+(?P<chapter>\d+))?"
_VERSE_PATTERN = (
    r"(?:\s*[:.]\s*(?P<verse_start>\d+)"
    r"(?:\s*[-\u2013\u2014]\s*(?P<verse_end>\d+))?)?"
)
_REFERENCE_RE = re.compile(
    rf"^{_BOOK_PATTERN}{_CHAPTER_PATTERN}{_VERSE_PATTERN}$"
)

_SPLIT_RE = re.compile(r"\s*;\s*")
_COMMA_RE = re.compile(r"\s*,\s*")


def parse_reference(
    text: str, canon_profile: str = DEFAULT_CANON_PROFILE, validate: bool = True
) -> Reference:
    """Parse a single reference string.

    Accepts common forms and normalises to the structured representation:
    ``John 3:16``, ``Jn 3:16``, ``JHN 3:16``, ``John 3:16-18``, ``1 Kings 2:4``,
    ``1Ki 2:4``, ``Philemon 2``, ``Phm 2``, ``Genesis``, ``Psa 119``.

    Parsing is STRICT. An unresolvable book key, an out-of-range chapter, or an
    inverted range raises rather than returning a best guess.

    Single-chapter books (Obadiah, Philemon, 2 and 3 John, Jude) are disambiguated
    deterministically: a number that is valid as a chapter is read as a chapter, and a
    number that cannot be a chapter is read as a verse of chapter 1. So ``Oba 1`` is
    chapter 1 and ``Phm 2`` is chapter 1 verse 2, because Philemon has no chapter 2.
    Each has exactly one possible reading, so neither is a guess.

    Args:
        text: The reference string.
        canon_profile: The profile against which the reference is valid.
        validate: When true (the default), validate membership and chapter range.

    Returns:
        A :class:`Reference`.

    Raises:
        ReferenceError: if *text* is not a single, well-formed, resolvable reference.
    """
    if not isinstance(text, str):
        raise ReferenceError(f"Reference text must be a string, got {type(text).__name__}.")
    cleaned = text.strip()
    if not cleaned:
        raise ReferenceError("Reference text must not be empty.")
    if _SPLIT_RE.search(cleaned):
        raise ReferenceError(
            f"{text!r} contains multiple references separated by ';'. "
            f"Use parse_references() for a list."
        )

    match = _REFERENCE_RE.match(cleaned)
    if match is None:
        raise ReferenceError(
            f"Could not parse {text!r} as a canonical reference. Expected a form such "
            f"as 'John 3:16', 'John 3:16-18', '1 Kings 2:4', 'Phm 2', or 'Genesis'."
        )

    book_token = " ".join(match.group("book").replace(".", " ").split())
    if not book_token:
        raise ReferenceError(f"Could not determine a book from {text!r}.")
    book = get_book(book_token)

    chapter_raw = match.group("chapter")
    verse_start_raw = match.group("verse_start")
    verse_end_raw = match.group("verse_end")

    chapter = int(chapter_raw) if chapter_raw else None
    verse_start = int(verse_start_raw) if verse_start_raw else None
    verse_end = int(verse_end_raw) if verse_end_raw else None

    single_chapter = is_single_chapter_book(book.key)

    # A verse without a chapter is only meaningful for a single-chapter book,
    # where chapter 1 is implicit. Otherwise it is an error, never a guess.
    if verse_start is not None and chapter is None:
        if single_chapter:
            chapter = 1
        else:
            raise ReferenceError(
                f"{text!r} gives a verse without a chapter. {book.name_en} has "
                f"{book.chapters if book.chapters is not None else 'an edition-dependent'} "
                f"chapter(s), so a chapter number is required. Scriptura does not guess "
                f"a chapter."
            )

    # For a single-chapter book, a bare number with no verse component can only be a
    # VERSE: the book has no chapter 2, so "Phm 2" has exactly one reading, namely
    # chapter 1 verse 2. This is a determined reading, not a guess, and it matches the
    # reference convention published by STEPBible-Data (for example "Phm.2").
    if chapter is not None and verse_start is None and single_chapter and chapter != 1:
        verse_start = chapter
        verse_end = None
        chapter = 1

    ref = Reference(
        book=book.key,
        canon_profile=canon_profile,
        chapter=chapter,
        verse_start=verse_start,
        verse_end=verse_end,
    )
    if validate:
        validate_membership(ref)
    return ref


def parse_references(
    text: str, canon_profile: str = DEFAULT_CANON_PROFILE, validate: bool = True
) -> tuple[Reference, ...]:
    """Parse a list of references.

    Accepts ``;``-separated references and expands ``a,b`` verse lists into separate
    references, so ``John 3:16,18`` yields two single-verse references and
    ``John 3:16-18`` yields one range.

    Raises:
        ReferenceError: if any component fails to parse. The error names the
            component; a partial result is never returned.
    """
    if not isinstance(text, str) or not text.strip():
        raise ReferenceError("Reference text must be a non-empty string.")

    out: list[Reference] = []
    for segment in _SPLIT_RE.split(text.strip()):
        segment = segment.strip()
        if not segment:
            continue
        parts = _COMMA_RE.split(segment)
        if len(parts) == 1:
            out.append(parse_reference(segment, canon_profile, validate))
            continue

        # A comma list: the first component carries the book and chapter, and the
        # remaining components are verse numbers or verse ranges within it.
        first = parse_reference(parts[0], canon_profile, validate)
        out.append(first)
        if first.chapter is None:
            raise ReferenceError(
                f"{text!r}: a comma-separated verse list requires a chapter. "
                f"Scriptura does not guess one."
            )
        for part in parts[1:]:
            part = part.strip()
            if not part:
                continue
            range_match = re.match(r"^(\d+)\s*[-\u2013\u2014]\s*(\d+)$", part)
            if range_match:
                start, end = int(range_match.group(1)), int(range_match.group(2))
            elif part.isdigit():
                start = end = int(part)
            else:
                raise ReferenceError(
                    f"{text!r}: could not parse {part!r} as a verse or verse range."
                )
            ref = Reference(
                book=first.book,
                canon_profile=canon_profile,
                chapter=first.chapter,
                verse_start=start,
                verse_end=end if end != start else None,
            )
            if validate:
                validate_membership(ref)
            out.append(ref)
    if not out:
        raise ReferenceError(f"No references could be parsed from {text!r}.")
    return tuple(out)


def iter_profile(
    profile_key: str, chapter_counts: Mapping[str, int] | None = None
) -> Iterator[Reference]:
    """Yield every chapter-level reference in *profile_key*.

    Books whose chapter count is not asserted by the registry are skipped unless a
    count is supplied in *chapter_counts*. Skipping is recorded behaviour, not a
    silent guess.
    """
    profile = get_profile(profile_key)
    for key in profile.book_keys:
        book = BOOKS[key]
        count = (chapter_counts or {}).get(key, book.chapters)
        if count is None:
            continue
        for chapter in range(1, count + 1):
            yield Reference(book=key, canon_profile=profile_key, chapter=chapter)
