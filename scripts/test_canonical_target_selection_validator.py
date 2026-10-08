import copy
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_canonical_target_selection as v


class CanonicalTargetSelectionValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.selection = v.load(v.SEL)
        cls.convergence = v.load(v.CONV)
        cls.corridors = v.load(v.CORR)

    def test_live_not_freeze_ready_state_passes_preflight(self):
        report = v.validate(
            copy.deepcopy(self.selection),
            copy.deepcopy(self.convergence),
            copy.deepcopy(self.corridors),
        )
        self.assertEqual(report["result"], "PASS", report["errors"])
        self.assertFalse(report["freeze_ready"])

    def test_old_scapula_grade_is_rejected(self):
        conv = copy.deepcopy(self.convergence)
        conv["region_findings"]["scapula"]["grade"] = "C"
        conv["region_findings"]["scapula"]["state"] = "REOPEN_METHOD_CONFLICT"
        report = v.validate(copy.deepcopy(self.selection), conv, copy.deepcopy(self.corridors))
        self.assertEqual(report["result"], "FAIL")
        self.assertTrue(any("scapular" in e for e in report["errors"]))

    def test_premature_freeze_is_rejected(self):
        sel = copy.deepcopy(self.selection)
        sel["freeze_ready"] = True
        report = v.validate(sel, copy.deepcopy(self.convergence), copy.deepcopy(self.corridors))
        self.assertEqual(report["result"], "FAIL")
        self.assertTrue(any("blockers" in e or "unset targets" in e for e in report["errors"]))

    def test_metatarsal_conflict_must_remain_explicit(self):
        conv = copy.deepcopy(self.convergence)
        conv["region_findings"]["metatarsals"]["grade"] = "A"
        conv["region_findings"]["metatarsals"]["state"] = "CONFIRMED_LONG"
        report = v.validate(copy.deepcopy(self.selection), conv, copy.deepcopy(self.corridors))
        self.assertEqual(report["result"], "FAIL")
        self.assertTrue(any("metatarsal" in e for e in report["errors"]))


if __name__ == "__main__":
    unittest.main()
