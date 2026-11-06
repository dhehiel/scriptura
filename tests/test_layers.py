"""Epistemic layers, per-layer requirements, promotion guard. R3: 5, 9."""
import unittest
from scriptura.core.errors import LayerValidationError
from scriptura.core.layers import (
    LAYER_VALUES, EpistemicLayer, assert_not_promotion, coerce_layer,
    compose_layer, is_valid_layer, require_flag, serialise_layer_metadata,
    validate_layer_fields, weakest_layer,
)

GOOD = {
    "scripture": {"edition_id": "e", "reference": {"book": "Jhn"}},
    "historical_evidence": {"evidence_type": "inscription", "source_uri": "s"},
    "linguistic_observation": {"observation_type": "morphology", "analyst": "a"},
    "theological_interpretation": {"tradition": "T", "source_uri": "s"},
    "ai_hypothesis": {"model": "m", "method": "mt", "inputs": ["i"],
                        "confidence": 0.4, "generated_at": "t"},
}


class LayerTest(unittest.TestCase):
    def test_closed_set(self):
        self.assertEqual(set(LAYER_VALUES), {
            "scripture", "historical_evidence", "linguistic_observation",
            "theological_interpretation", "ai_hypothesis"})
        self.assertTrue(is_valid_layer("scripture"))
        self.assertTrue(is_valid_layer(EpistemicLayer.SCRIPTURE))
        self.assertFalse(is_valid_layer("gospel_truth"))
        self.assertFalse(is_valid_layer(None))

    def test_no_default_layer(self):
        with self.assertRaises(LayerValidationError):
            coerce_layer(None)
        with self.assertRaises(LayerValidationError):
            coerce_layer("gospel_truth")
        self.assertEqual(coerce_layer("scripture"), EpistemicLayer.SCRIPTURE)

    def test_valid_fields_pass(self):
        for layer, fields in GOOD.items():
            with self.subTest(layer=layer):
                validate_layer_fields(layer, dict(fields))

    def test_rejections(self):
        bad = {
            "scripture": {},
            "historical_evidence": {},
            "linguistic_observation": {"observation_type": "morphology"},
            "theological_interpretation": {"source_uri": "s"},
            "ai_hypothesis": {"model": "m"},
        }
        for layer, fields in bad.items():
            with self.subTest(layer=layer):
                with self.assertRaises(LayerValidationError):
                    validate_layer_fields(layer, fields)

    def test_confidence_bounds(self):
        base = dict(GOOD["ai_hypothesis"])
        for bad in (-0.1, 1.5, "high", True):
            with self.subTest(bad=bad):
                fields = dict(base, confidence=bad)
                with self.assertRaises(LayerValidationError):
                    validate_layer_fields("ai_hypothesis", fields)

    def test_flag(self):
        self.assertTrue(require_flag("ai_hypothesis"))
        for layer in LAYER_VALUES:
            if layer != "ai_hypothesis":
                self.assertFalse(require_flag(layer))

    def test_serialise_always_flagged(self):
        meta = serialise_layer_metadata("ai_hypothesis")
        self.assertEqual(meta["layer"], "ai_hypothesis")
        self.assertTrue(meta["non_authoritative"])
        meta2 = serialise_layer_metadata("scripture")
        self.assertFalse(meta2["non_authoritative"])

    def test_compose_weakest(self):
        self.assertEqual(compose_layer(["scripture", "ai_hypothesis"]),
                         EpistemicLayer.AI_HYPOTHESIS)
        self.assertEqual(weakest_layer(["scripture"]), EpistemicLayer.SCRIPTURE)
        with self.assertRaises(LayerValidationError):
            weakest_layer([])

    def test_promotion_guard(self):
        # downgrade always fine
        self.assertEqual(assert_not_promotion("scripture", "ai_hypothesis", None, None),
                         EpistemicLayer.AI_HYPOTHESIS)
        # upgrade without evidence/actor refused
        with self.assertRaises(LayerValidationError):
            assert_not_promotion("ai_hypothesis", "linguistic_observation", None, None)
        with self.assertRaises(LayerValidationError):
            assert_not_promotion("ai_hypothesis", "linguistic_observation", "e", None)
        # upgrade with both recorded
        self.assertEqual(
            assert_not_promotion("ai_hypothesis", "linguistic_observation", "e", "human"),
            EpistemicLayer.LINGUISTIC_OBSERVATION)
        # ai -> scripture never
        with self.assertRaises(LayerValidationError):
            assert_not_promotion("ai_hypothesis", "scripture", "e", "human")


if __name__ == "__main__":
    unittest.main()
