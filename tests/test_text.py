"""Unicode normalisation and diacritic folding. R3 coverage: 3."""
import unittest
from scriptura.core.text import fold_diacritics, is_folded, strip_marks

G = "\u1f41 \u03bb\u03cc\u03b3\u03bf\u03c2 \u1f26\u03bd"
H = "\u05d0\u05b1\u05dc\u05b9\u05d4\u05b4\u05d9\u05dd"


class TextTest(unittest.TestCase):
    def test_strip_greek(self):
        self.assertEqual(strip_marks("\u03bb\u03cc\u03b3\u03bf\u03c2"), "\u03bb\u03bf\u03b3\u03bf\u03c2")

    def test_strip_hebrew(self):
        self.assertEqual(strip_marks(H), "\u05d0\u05dc\u05d4\u05d9\u05dd")

    def test_fold_matches(self):
        self.assertEqual(fold_diacritics("\u03bb\u03cc\u03b3\u03bf\u03c2"),
                         fold_diacritics("\u03bb\u03bf\u03b3\u03bf\u03c2"))
        self.assertEqual(fold_diacritics(H), fold_diacritics("\u05d0\u05dc\u05d4\u05d9\u05dd"))
        self.assertEqual(fold_diacritics("De\u00e9sus"), "deesus")

    def test_no_romanization(self):
        self.assertNotEqual(fold_diacritics("\u03bb\u03cc\u03b3\u03bf\u03c2"), "logos")
        self.assertNotEqual(fold_diacritics(H), "elohim")

    def test_final_sigma_normalised(self):
        self.assertEqual(fold_diacritics("\u03bb\u03bf\u03b3\u03bf\u03c2"),
                         fold_diacritics("\u039b\u039f\u0393\u039f\u03a3"))

    def test_is_folded(self):
        self.assertTrue(is_folded("logos"))
        self.assertFalse(is_folded("\u03bb\u03cc\u03b3\u03bf\u03c2"))

    def test_type_error(self):
        with self.assertRaises(TypeError):
            fold_diacritics(42)


if __name__ == "__main__":
    unittest.main()
