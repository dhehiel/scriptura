"""Reference parsing, book registry, canon profiles. R3 coverage: 1-2."""
import unittest
from scriptura.core.errors import ReferenceError
from scriptura.core.reference import (
    BOOKS, CANON_PROFILES, Reference, book_keys_for_profile, format_reference,
    get_book, get_profile, is_single_chapter_book, iter_profile,
    parse_reference, parse_references, validate_membership,
)


class BookRegistryTest(unittest.TestCase):
    def test_counts(self):
        self.assertEqual(len(BOOKS), 86)
        self.assertEqual(len(book_keys_for_profile("protestant_66")), 66)
        self.assertEqual(len(book_keys_for_profile("catholic_73")), 73)
        self.assertEqual(len(book_keys_for_profile("orthodox_broad")), 86)
        self.assertEqual(len(book_keys_for_profile("hebrew_bible_24")), 39)
        self.assertEqual(len(book_keys_for_profile("nt_27")), 27)
        self.assertEqual(len(book_keys_for_profile("deuterocanonical")), 20)

    def test_catholic_counts_additions_within_books(self):
        keys = set(book_keys_for_profile("catholic_73"))
        for extra in ("EsG", "S3Y", "Sus", "Bel", "LJe"):
            self.assertNotIn(extra, keys)
        for core in ("Tob", "Jdt", "Wis", "Sir", "Bar", "1Ma", "2Ma"):
            self.assertIn(core, keys)

    def test_malachi_notes_divergence(self):
        self.assertIn("edition", BOOKS["Mal"].notes.lower())

    def test_deuterocanonical_chapters_unasserted(self):
        for key in book_keys_for_profile("deuterocanonical"):
            self.assertIsNone(BOOKS[key].chapters, key)

    def test_unknown_book_strict(self):
        with self.assertRaises(ReferenceError):
            get_book("Foo")
        with self.assertRaises(ReferenceError):
            get_book("")

    def test_unknown_profile_strict(self):
        with self.assertRaises(ReferenceError):
            get_profile("sola_scriptura")

    def test_aliases(self):
        for token in ("john", "Jn", "JHN", "i kings", "ii sam", "2 sam",
                      "1 jn", "song of songs", "qoh", "psalm"):
            self.assertTrue(get_book(token).key, token)

    def test_single_chapter(self):
        for key in ("Oba", "Phm", "Jud", "2Jn", "3Jn"):
            self.assertTrue(is_single_chapter_book(key), key)
        self.assertFalse(is_single_chapter_book("Jhn"))


class ParseTest(unittest.TestCase):
    def test_forms(self):
        cases = {
            "John 3:16": ("Jhn", 3, 16, None),
            "Jn 3:16": ("Jhn", 3, 16, None),
            "JHN 3:16": ("Jhn", 3, 16, None),
            "John 3:16-18": ("Jhn", 3, 16, 18),
            "1 Kings 2:4": ("1Ki", 2, 4, None),
            "1Ki 2:4": ("1Ki", 2, 4, None),
            "ii sam 5:1": ("2Sa", 5, 1, None),
            "Philemon 2": ("Phm", 1, 2, None),
            "Phm 2": ("Phm", 1, 2, None),
            "Oba 1": ("Oba", 1, None, None),
            "Genesis": ("Gen", None, None, None),
            "Psa 119": ("Psa", 119, None, None),
            "Wisdom 3:1": ("Wis", 3, 1, None),
        }
        for text, (book, ch, vs, ve) in cases.items():
            with self.subTest(text=text):
                profile = ("orthodox_broad" if book in set(
                    book_keys_for_profile("deuterocanonical")) else "protestant_66")
                ref = parse_reference(text, canon_profile=profile)
                self.assertEqual((ref.book, ref.chapter, ref.verse_start,
                                  ref.verse_end), (book, ch, vs, ve))

    def test_strict_rejections(self):
        # "John 3" is a VALID chapter-level reference and must NOT raise.
        for bad in ("Foo 1:1", "John 99:1", "John 3:20-10", "Esther 11:1",
                    "nonexistent", "", "John 3:16; Rom 1:1"):
            with self.subTest(bad=bad):
                with self.assertRaises(ReferenceError):
                    parse_reference(bad)

    def test_lists(self):
        refs = parse_references("John 3:16,18; Rom 1:1-3")
        self.assertEqual([r.display for r in refs],
                         ["Jhn 3:16", "Jhn 3:18", "Rom 1:1-3"])

    def test_profile_rejection(self):
        with self.assertRaises(ReferenceError):
            parse_reference("Wisdom 3:1", canon_profile="protestant_66")

    def test_reference_roundtrip(self):
        ref = parse_reference("1 Cor 13:4")
        self.assertEqual(Reference.from_dict(ref.to_dict()), ref)
        self.assertEqual(format_reference(ref), "1Co 13:4")
        self.assertLess(parse_reference("Jhn 1:1").sort_key(),
                        parse_reference("Jhn 1:2").sort_key())

    def test_iter_profile_skips_unasserted(self):
        chapters = list(iter_profile("protestant_66"))
        self.assertEqual(len(chapters), sum(BOOKS[k].chapters
                                            for k in book_keys_for_profile("protestant_66")))
        self.assertEqual(list(iter_profile("deuterocanonical")), [])
        filled = list(iter_profile("deuterocanonical", {"Tob": 2}))
        self.assertEqual(len(filled), 2)


if __name__ == "__main__":
    unittest.main()
