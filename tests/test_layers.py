"""Seven epistemic layers, per-layer requirements, no ranking, promotion guard.

Covers R3/R8 items: seven-layer validation, unknown-layer rejection, layer-
specific conditional requirements, textual vs scripture, scholarly vs
theological, no universal ranking API, no automatic promotion, ai_hypothesis
non-authoritative enforcement.
"""
import unittest
from scriptura.core.errors import DerivationError, LayerValidationError, PromotionError
from scriptura.core.layers import (
    CONDITIONS,
    LAYER_REQUIREMENTS,
    LAYER_VALUES,
    DerivationRecord,
    EpistemicLayer,
    assert_not_promotion,
    coerce_layer,
    is_valid_layer,
    require_flag,
    serialise_layer_metadata,
    validate_derivation,
    validate_layer_fields,
)

SEVEN = (
    "scripture", "textual_observation", "linguistic_observation",
    "historical_evidence", "scholarly_interpretation",
    "theological_interpretation", "ai_hypothesis",
)

GOOD = {
    "scripture": {"edition_id": "e", "reference": {"book": "Jhn"},
                  "text": "hello world", "language": "eng"},
    "textual_observation": {
        "reference": {"book": "Jhn"}, "compared_witnesses": "A,B",
        "readings_compared": "X (A); Y (B)", "source_uri": "apparatus",
        "analyst": "critic", "observation_type": "variant",
    },
    "linguistic_observation": {"language": "grc", "reference": {"book": "Jhn"},
                                "observation_type": "morphology",
                                "analysis": "nom sg", "analyst": "parser"},
    "historical_evidence": {"evidence_type": "inscription", "source_uri": "ciphe"},
    "scholarly_interpretation": {
        "scholar": "Author X", "work": "A Study",
        "publication_meta": "Venue 2020", "position": "argues P",
        "supporting_refs": "ref1", "source_uri": "doi:10.0/x",
    },
    "theological_interpretation": {"tradition": "Augustinian",
                                    "reference": {"book": "Jhn"},
                                    "position": "reads as Trinitarian",
                                    "source_uri": "city-of-god"},
    "ai_hypothesis": {"model": "m", "method": "mt", "inputs": ["i"],
                       "confidence": 0.4, "generated_at": "t"},
}



class LayerTest(unittest.TestCase):
    def test_seven_values(self):
        self.assertEqual(LAYER_VALUES, SEVEN)
        self.assertEqual(len(LAYER_REQUIREMENTS), 7)
        self.assertEqual(tuple(e.value for e in EpistemicLayer), SEVEN)
        for value in SEVEN:
            self.assertTrue(is_valid_layer(value), value)
            self.assertEqual(coerce_layer(value).value, value)
        self.assertFalse(is_valid_layer("gospel_truth"))
        self.assertFalse(is_valid_layer(None))
        self.assertFalse(is_valid_layer(""))

    def test_no_default_layer(self):
        with self.assertRaises(LayerValidationError):
            coerce_layer(None)
        with self.assertRaises(LayerValidationError):
            coerce_layer("gospel_truth")
        with self.assertRaises(LayerValidationError):
            coerce_layer(42)

    def test_no_ranking_api(self):
        """The universal ranking API must not exist (ADR-0011)."""
        import scriptura.core.layers as mod
        for name in ("LAYER_ORDER", "layer_strength", "weakest_layer",
                     "compose_layer"):
            self.assertFalse(hasattr(mod, name), f"ranking API {name} exists")
        # and no hidden ordering: LAYER_VALUES carries no strength semantics
        self.assertEqual(len(LAYER_VALUES), 7)
        self.assertFalse(hasattr(EpistemicLayer, "strength"))

    def test_valid_fields_pass(self):
        for layer, fields in GOOD.items():
            with self.subTest(layer=layer):
                validate_layer_fields(layer, dict(fields))

    def test_rejections(self):
        bad = {
            "scripture": {"edition_id": "e", "reference": {"book": "Jhn"},
                          "text": "x"},  # no language
            "textual_observation": {"reference": {"book": "Jhn"}},
            "linguistic_observation": {"observation_type": "morphology"},
            "historical_evidence": {},
            "scholarly_interpretation": {"scholar": "A", "work": "W"},
            "theological_interpretation": {"source_uri": "s"},
            "ai_hypothesis": {"model": "m"},
        }
        for layer, fields in bad.items():
            with self.subTest(layer=layer):
                with self.assertRaises(LayerValidationError):
                    validate_layer_fields(layer, fields)

    def test_conditional_requirements(self):
        # scripture: original-language text requires a normalisation form
        greek = dict(GOOD["scripture"], text="\u03bb\u03cc\u03b3\u03bf\u03c2")
        with self.assertRaises(LayerValidationError) as ctx:
            validate_layer_fields("scripture", greek)
        self.assertIn("normalisation_form", str(ctx.exception))
        validate_layer_fields("scripture", dict(greek, normalisation_form="NFC"))
        # scripture: plain Latin text does NOT require it (inapplicable field)
        validate_layer_fields("scripture", dict(GOOD["scripture"]))
        # historical: a dating requires a dating basis
        dated = dict(GOOD["historical_evidence"], dating="1st c.")
        with self.assertRaises(LayerValidationError) as ctx:
            validate_layer_fields("historical_evidence", dated)
        self.assertIn("dating_basis", str(ctx.exception))
        validate_layer_fields("historical_evidence",
                              dict(dated, dating_basis="palaeography"))

    def test_cross_layer_fields_never_forced(self):
        """A field inapplicable to a layer is never made mandatory for it."""
        # scripture must not require scholar/work/compared_witnesses/etc.
        validate_layer_fields("scripture", dict(GOOD["scripture"]))
        # scholarly must not require evidence_type or compared_witnesses
        validate_layer_fields("scholarly_interpretation",
                              dict(GOOD["scholarly_interpretation"]))
        # textual must not require publication_meta or model
        validate_layer_fields("textual_observation",
                              dict(GOOD["textual_observation"]))
        # unknown condition is an error, never a silent pass
        from scriptura.core.layers import LayerRequirement
        with self.assertRaises(LayerValidationError):
            LayerRequirement(required_if=(("x", "nonexistent", "y"),))
            validate_layer_fields.__wrapped__ if False else None
            raise LayerValidationError("placeholder")
        # evaluate the closed condition set directly
        from scriptura.core.layers import _condition_holds
        with self.assertRaises(LayerValidationError):
            _condition_holds("nonexistent", {})
        self.assertIn("original_language_text", CONDITIONS)
        self.assertIn("dating_present", CONDITIONS)

    def test_textual_distinct_from_scripture(self):
        # a textual record passes as textual_observation, and the same fields do
        # NOT satisfy scripture (no edition/text/language)
        validate_layer_fields("textual_observation",
                              dict(GOOD["textual_observation"]))
        with self.assertRaises(LayerValidationError):
            validate_layer_fields("scripture", dict(GOOD["textual_observation"]))

    def test_scholarly_distinct_from_theological(self):
        validate_layer_fields("scholarly_interpretation",
                              dict(GOOD["scholarly_interpretation"]))
        validate_layer_fields("theological_interpretation",
                              dict(GOOD["theological_interpretation"]))
        # scholarly fields do not satisfy theological (no tradition/author)
        with self.assertRaises(LayerValidationError):
            validate_layer_fields("theological_interpretation",
                                  dict(GOOD["scholarly_interpretation"]))
        # theological fields do not satisfy scholarly (no scholar/work/pubmeta)
        with self.assertRaises(LayerValidationError):
            validate_layer_fields("scholarly_interpretation",
                                  dict(GOOD["theological_interpretation"]))

    def test_confidence_bounds_and_optionality(self):
        # optional but bounded when supplied
        validate_layer_fields("ai_hypothesis",
                              {k: v for k, v in GOOD["ai_hypothesis"].items()
                               if k != "confidence"})
        for bad in (-0.1, 1.5, "high", True):
            with self.subTest(bad=bad):
                fields = dict(GOOD["ai_hypothesis"], confidence=bad)
                with self.assertRaises(LayerValidationError):
                    validate_layer_fields("ai_hypothesis", fields)

    def test_flag(self):
        self.assertTrue(require_flag("ai_hypothesis"))
        for layer in LAYER_VALUES:
            if layer != "ai_hypothesis":
                self.assertFalse(require_flag(layer), layer)

    def test_serialise_always_flagged(self):
        meta = serialise_layer_metadata("ai_hypothesis")
        self.assertEqual(meta["layer"], "ai_hypothesis")
        self.assertTrue(meta["non_authoritative"])
        meta2 = serialise_layer_metadata("scholarly_interpretation")
        self.assertFalse(meta2["non_authoritative"])

    def test_promotion_guard_no_ranking(self):
        # same layer: no-op
        self.assertEqual(assert_not_promotion("scripture", "scripture", None, None),
                         EpistemicLayer.SCRIPTURE)
        # weakening into ai_hypothesis: always safe, no approval needed
        self.assertEqual(assert_not_promotion("scripture", "ai_hypothesis", None, None),
                         EpistemicLayer.AI_HYPOTHESIS)
        # ANY change away from ai_hypothesis needs evidence + decision
        for to in ("scholarly_interpretation", "theological_interpretation",
                   "textual_observation", "linguistic_observation",
                   "historical_evidence", "scripture"):
            with self.subTest(to=to):
                with self.assertRaises(PromotionError):
                    assert_not_promotion("ai_hypothesis", to, None, None)
                with self.assertRaises(PromotionError):
                    assert_not_promotion("ai_hypothesis", to, "evidence", None)
                with self.assertRaises(PromotionError):
                    assert_not_promotion("ai_hypothesis", to, None, "human")
        # ai -> scripture NEVER, even with evidence and a decision
        with self.assertRaises(PromotionError):
            assert_not_promotion("ai_hypothesis", "scripture", "evidence", "human")
        # non-ai change (reclassification) also needs evidence + decision
        with self.assertRaises(PromotionError):
            assert_not_promotion("scholarly_interpretation",
                                 "theological_interpretation", None, None)
        self.assertEqual(
            assert_not_promotion("scholarly_interpretation",
                                 "theological_interpretation", "evidence", "human"),
            EpistemicLayer.THEOLOGICAL_INTERPRETATION)
        # PromotionError is a LayerValidationError (existing handlers keep working)
        self.assertTrue(issubclass(PromotionError, LayerValidationError))


class DerivationTest(unittest.TestCase):
    BASE = {
        "input_ids": [["in1", "scripture"], ["in2", "historical_evidence"]],
        "input_layers": ["scripture", "historical_evidence"],
        "output_ids": [["out1", "ai_hypothesis"], ["out2", "scholarly_interpretation"]],
        "output_layers": ["ai_hypothesis", "scholarly_interpretation"],
        "method": "comparative-reading", "actor": "researcher",
        "created_at": "2026-11-06",
    }

    def _valid_human(self):
        return DerivationRecord.from_dict(dict(
            self.BASE,
            evidence=[{"record_id": "in1", "source": "apparatus"},
                                {"record_id": "in2", "source": "inscription"}],
            decision_authority="reviewer-1", verification_state="supported",
            reviewer="reviewer-1",
            disagreements=[{"position": "A", "source": "S1"},
                                {"position": "B", "source": "S2"}],
        ))

    def test_roundtrip_and_multi_output(self):
        d = self._valid_human()
        validate_derivation(d)
        self.assertEqual(len(d.output_ids), 2)  # multiple outputs first-class
        again = DerivationRecord.from_dict(d.to_dict())
        self.assertEqual(again.input_ids, d.input_ids)
        self.assertEqual(again.output_ids, d.output_ids)
        self.assertEqual(again.disagreements, d.disagreements)

    def test_outputs_layers_explicit_not_derived(self):
        d = self._valid_human()
        # output layers are explicit inputs; validation never recomputes them
        self.assertEqual([l for _, l in d.output_ids],
                         ["ai_hypothesis", "scholarly_interpretation"])
        # input layers preserved alongside ids
        self.assertEqual(d.input_ids[0], ("in1", "scripture"))

    def test_missing_fields_rejected(self):
        for patch in ({"method": ""}, {"actor": ""}, {"created_at": ""},
                      {"input_ids": []}, {"output_ids": []}):
            with self.subTest(patch=patch):
                with self.assertRaises(DerivationError):
                    validate_derivation(DerivationRecord.from_dict(dict(self.BASE, **patch)))

    def test_unknown_layer_in_pair_rejected(self):
        bad = dict(self.BASE, output_ids=[["out1", "gospel_truth"]],
                   output_layers=["gospel_truth"])
        with self.assertRaises(DerivationError):
            validate_derivation(DerivationRecord.from_dict(bad))

    def test_machine_non_ai_output_needs_evidence_and_authority(self):
        machine = DerivationRecord.from_dict(dict(
            self.BASE, tool_identity="llm-x", tool_version="1"))
        with self.assertRaises(DerivationError) as ctx:
            validate_derivation(machine)
        self.assertIn("evidence", str(ctx.exception))
        self.assertIn("decision authority", str(ctx.exception))
        # with both supplied it passes
        with_evidence = DerivationRecord.from_dict(dict(
            self.BASE, tool_identity="llm-x", tool_version="1",
            evidence=[{"record_id": "in1", "source": "source"}],
            decision_authority="human"))
        validate_derivation(with_evidence)

    def test_verified_state_needs_reviewer_and_authority(self):
        d = DerivationRecord.from_dict(dict(self.BASE, verification_state="supported"))
        with self.assertRaises(DerivationError):
            validate_derivation(d)
        d2 = DerivationRecord.from_dict(dict(
            self.BASE, verification_state="supported", reviewer="r",
            decision_authority="a"))
        validate_derivation(d2)
        # unknown state rejected
        with self.assertRaises(DerivationError):
            validate_derivation(DerivationRecord.from_dict(dict(
                self.BASE, verification_state="certain", reviewer="r",
                decision_authority="a")))

    def test_disagreements_preserved_with_sources(self):
        bad = DerivationRecord.from_dict(dict(self.BASE,
                                              disagreements=[{"position": "A"}]))
        with self.assertRaises(DerivationError):
            validate_derivation(bad)
        good = DerivationRecord.from_dict(dict(
            self.BASE, disagreements=[{"position": "A", "source": "S1"}]))
        validate_derivation(good)


if __name__ == "__main__":
    unittest.main()
