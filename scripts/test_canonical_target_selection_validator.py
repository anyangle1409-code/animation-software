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
