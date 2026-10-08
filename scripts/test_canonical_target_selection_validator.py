import copy
import unittest

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_canonical_target_selection as v


class CanonicalTargetSelectionValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.selection = v.load(v.SEL)
        cls.convergence = v.load(v.CONV)
        cls.corridors = v.load(v.CORR)
        cls.shoulder_constraint = v.load(v.SHOULDER_CONSTRAINT)
        cls.shoulder_source = v.load(v.SHOULDER_SOURCE)

    def run_live(self, selection=None, convergence=None, corridors=None,
                 shoulder_constraint=None, shoulder_source=None):
        return v.validate(
            copy.deepcopy(selection if selection is not None else self.selection),
            copy.deepcopy(convergence if convergence is not None else self.convergence),
            copy.deepcopy(corridors if corridors is not None else self.corridors),
            copy.deepcopy(
                shoulder_constraint if shoulder_constraint is not None
                else self.shoulder_constraint
            ),
            copy.deepcopy(
                shoulder_source if shoulder_source is not None
                else self.shoulder_source
            ),
        )

    def test_live_not_freeze_ready_state_passes_preflight(self):
        report = self.run_live()
        self.assertEqual(report["result"], "PASS", report["errors"])
        self.assertFalse(report["freeze_ready"])

    def test_old_scapula_grade_is_rejected(self):
        conv = copy.deepcopy(self.convergence)
        conv["region_findings"]["scapula"]["grade"] = "C"
        conv["region_findings"]["scapula"]["state"] = "REOPEN_METHOD_CONFLICT"
        report = self.run_live(convergence=conv)
        self.assertEqual(report["result"], "FAIL")
        self.assertTrue(any("scapular" in e for e in report["errors"]))

    def test_direct_3d_measurement_requires_full_text_provenance(self):
        source = copy.deepcopy(self.shoulder_source)
        source["sources"].pop("SCAPULA_AC_LATERAL_2026", None)
        report = self.run_live(shoulder_source=source)
        self.assertTrue(any("full-text" in e for e in report["errors"]))

    def test_3d_distance_must_not_become_transverse_equality(self):
        sh = copy.deepcopy(self.shoulder_constraint)
        sh["derived_constraints"]["direct_AC_3D_constraint"]["valid_relation"] = (
            "required_transverse_AC_to_lateral_acromion_component_mm == measured_3D_distance_mm"
        )
        report = self.run_live(shoulder_constraint=sh)
        self.assertTrue(any("transverse" in e for e in report["errors"]))

    def test_direct_3d_value_mutation_is_rejected(self):
        sh = copy.deepcopy(self.shoulder_constraint)
        sh["inputs"]["direct_AC_to_lateral_acromion_3D_mm"]["mean"] = 77.0
        report = self.run_live(shoulder_constraint=sh)
        self.assertTrue(any("direct AC" in e for e in report["errors"]))

    def test_nan_shoulder_length_is_rejected(self):
        sel = copy.deepcopy(self.selection)
        sel["regions"]["shoulder_girdle"]["selected"]["clavicle_SC_AC_chord_mm"] = float("nan")
        report = self.run_live(selection=sel)
        self.assertTrue(any("finite positive" in e for e in report["errors"]))

    def test_malformed_measurements_report_failure_without_crashing(self):
        for key in ("bilateral_AC_breadth_mm", "clavicle_SC_AC_chord_mm"):
            with self.subTest(key=key):
                sel = copy.deepcopy(self.selection)
                selected = sel["regions"]["shoulder_girdle"]["selected"]
                selected[key] = "invalid"
                selected["clavicle_curved_length_mm"] = 166.8
                report = self.run_live(selection=sel)
                self.assertEqual(report["result"], "FAIL")
                self.assertTrue(any("finite positive" in e for e in report["errors"]))

    def test_freeze_flag_requires_actual_boolean(self):
        for value in (0, "", [], None):
            with self.subTest(value=value):
                sel = copy.deepcopy(self.selection)
                sel["freeze_ready"] = value
                self.assertEqual(self.run_live(selection=sel)["result"], "FAIL")

    def test_unknown_empty_or_missing_grades_cannot_freeze(self):
        # Synthetic input only: isolate the grading gate after clearing
        # other blockers. This fixture is not proposed anatomical data.
        def fill(obj):
            if isinstance(obj, dict):
                return {k: fill(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [fill(v) for v in obj]
            return 1.0 if obj is None else obj
        base = fill(copy.deepcopy(self.selection))
        base["freeze_ready"] = True
        for region in base["regions"].values():
            region["blockers"] = []
            for key in list(region):
                if key.startswith("evidence_grade"):
                    region[key] = "B"
        base["regions"]["shoulder_girdle"]["evidence_grade"] = {
            "clavicle": "A", "scapula": "A_TRANSVERSE_DEFECT_EXACT_3D_TARGET_OPEN"}
        base["regions"]["shoulder_girdle"]["selected"].update({
            "clavicle_SC_AC_chord_mm": 153.0,
            "clavicle_curved_length_mm": 167.0})
        self.assertEqual(self.run_live(selection=base)["result"], "PASS")
        for grade in ("E", "APPROVED", "", [], {}, None):
            with self.subTest(grade=grade):
                sel = copy.deepcopy(base)
                sel["regions"]["head_neck"]["evidence_grade"] = grade
                self.assertEqual(self.run_live(selection=sel)["result"], "FAIL")
        del base["regions"]["head_neck"]["evidence_grade"]
        self.assertEqual(self.run_live(selection=base)["result"], "FAIL")

    def test_premature_freeze_is_rejected(self):
        sel = copy.deepcopy(self.selection)
        sel["freeze_ready"] = True
        report = self.run_live(selection=sel)
        self.assertEqual(report["result"], "FAIL")
        self.assertTrue(any("blockers" in e or "unset targets" in e for e in report["errors"]))

    def test_metatarsal_conflict_must_remain_explicit(self):
        conv = copy.deepcopy(self.convergence)
        conv["region_findings"]["metatarsals"]["grade"] = "A"
        conv["region_findings"]["metatarsals"]["state"] = "CONFIRMED_LONG"
        report = self.run_live(convergence=conv)
        self.assertEqual(report["result"], "FAIL")
        self.assertTrue(any("metatarsal" in e for e in report["errors"]))

    def test_withdrawn_direct_ac_offset_cannot_return(self):
        sh = copy.deepcopy(self.shoulder_constraint)
        sh.setdefault("inputs", {})["lateral_acromion_to_AC_joint_mm"] = {
            "mean": 34.0,
            "sd": 8.0,
        }
        sh["derived_constraints"]["exact_AC_offset"] = 34.0
        report = self.run_live(shoulder_constraint=sh)
        self.assertEqual(report["result"], "FAIL")
        self.assertTrue(any("acromion-to-AC" in e or "AC offset" in e for e in report["errors"]))

    def test_sternum_reopen_state_cannot_disappear(self):
        conv = copy.deepcopy(self.convergence)
        del conv["region_findings"]["sternum"]
        report = self.run_live(convergence=conv)
        self.assertEqual(report["result"], "FAIL")
        self.assertTrue(any("sternum" in e for e in report["errors"]))


if __name__ == "__main__":
    unittest.main()
