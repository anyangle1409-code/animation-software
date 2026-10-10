#!/usr/bin/env python3
"""Regression tests for explicit legacy runtime side inversion preflight."""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))
import runtime_side_binding_preflight as m


class RuntimeSideBindingPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fit = m.load(m.FIT)
        cls.aliases = m.load(m.ALIASES)
        cls.runtime = m.load(m.RUNTIME)

    def report(self):
        return m.build_report(self.fit, self.aliases, self.runtime)

    def test_production_inventory_and_all_sided_aliases_mismatch(self):
        report = self.report()
        summary = report["summary"]
        self.assertEqual(len(self.aliases["aliases"]), 206)
        self.assertEqual(len(self.runtime["bones"]), 67)
        self.assertEqual(summary["named_sided_aliases"], 122)
        self.assertEqual(summary["name_only_wrong_side"], 122)
        self.assertEqual(summary["named_side_consistent"], 0)
        self.assertEqual(len(report["sided_alias_evidence"]), 122)
        self.assertFalse(report["safe_to_use_name_only_mapping"])
        self.assertFalse(report["rig_export_approved"])
        self.assertFalse(report["verified_full_3d_transform"])

    def test_original_anatomical_left_humerus_is_runtime_upperarm_r(self):
        rows = self.report()["sided_alias_evidence"]
        hit = next(row for row in rows if row["anatomical_id"] == "humerus_left")
        self.assertEqual(hit["stored_alias"], "upperarm_l")
        self.assertEqual(hit["inverse_name_candidate"], "upperarm_r")
        self.assertGreater(hit["independent_anatomical_x_m"], 0.20)
        self.assertLess(hit["stored_alias_x_m"], -0.20)
        self.assertGreater(hit["candidate_x_m"], 0.20)

    def test_both_sides_of_three_anchors_are_verified(self):
        rows = self.report()["independent_six_anchor_checks"]
        self.assertEqual(len(rows), 6)
        self.assertEqual(len({row["anatomical_id"] for row in rows}), 6)
        self.assertTrue(all(x["status"] == "SIDE_SIGNS_AGREE_ONLY" for x in rows))

    def test_both_sides_are_mirrored_for_the_three_anchor_chains(self):
        rows = self.report()["independent_six_anchor_checks"]
        for anatomical_id in m.ANCHORS:
            l = next(x for x in rows if x["anatomical_id"] == anatomical_id + "_left")
            r = next(x for x in rows if x["anatomical_id"] == anatomical_id + "_right")
            self.assertGreater(l["anatomical_x_m"], 0)
            self.assertLess(r["anatomical_x_m"], 0)
            self.assertGreater(l["runtime_x_m"], 0)
            self.assertLess(r["runtime_x_m"], 0)
            self.assertTrue(l["resolved_runtime_name"].endswith("_r"))
            self.assertTrue(r["resolved_runtime_name"].endswith("_l"))

    def test_declared_convention_must_match_observed(self):
        altered = copy.deepcopy(self.fit)
        altered["conventions"]["runtime_side_binding"] = {"left": "_l", "right": "_r"}
        with self.assertRaisesRegex(ValueError, "side binding changed"):
            m.build_report(altered, self.aliases, self.runtime)

    def test_moved_anchor_rejected_even_if_names_look_correct(self):
        altered = copy.deepcopy(self.runtime)
        bone = next(x for x in altered["bones"] if x["name"] == "upperarm_r")
        bone["head"][0] = -abs(bone["head"][0])
        bone["tail"][0] = -abs(bone["tail"][0])
        with self.assertRaisesRegex(ValueError, "Runtime anchor chirality changed"):
            m.build_report(self.fit, self.aliases, altered)

    def test_misnamed_runtime_target_rejected(self):
        altered = copy.deepcopy(self.aliases)
        row = next(x for x in altered["aliases"] if x["anatomical_id"] == "humerus_left")
        row["current_rig"] = ["upperarm_unknown"]
        with self.assertRaisesRegex(ValueError, "Unknown current rig"):
            m.build_report(self.fit, altered, self.runtime)

    def test_destroyed_bilateral_pair_rejected(self):
        altered = copy.deepcopy(self.aliases)
        row = next(x for x in altered["aliases"] if x["anatomical_id"] == "humerus_right")
        row["current_rig"] = ["forearm_r"]
        with self.assertRaisesRegex(ValueError, "Stored bilateral alias names"):
            m.build_report(self.fit, altered, self.runtime)

    def test_missing_anatomy_id_rejected(self):
        altered = copy.deepcopy(self.aliases)
        altered["aliases"].pop()
        with self.assertRaisesRegex(ValueError, "206 unique IDs"):
            m.build_report(self.fit, altered, self.runtime)

    def test_cli_writes_only_report_and_unsafe_exit_is_two(self):
        before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in (m.FIT, m.RUNTIME, m.ALIASES)}
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "report.json"
            base = [sys.executable, str(m.ROOT / "scripts/anatomy_fit/runtime_side_binding_preflight.py"),
                    "--out", str(out)]
            ok = subprocess.run(base, capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0, ok.stderr)
            data = json.loads(out.read_text())
            self.assertFalse(data["safe_to_use_name_only_mapping"])
            blocked = subprocess.run(base + ["--require-name-safe"], capture_output=True, text=True)
            self.assertEqual(blocked.returncode, 2, blocked.stderr)
            self.assertEqual(before, {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                                      for p in (m.FIT, m.RUNTIME, m.ALIASES)})


if __name__ == "__main__":
    unittest.main()
