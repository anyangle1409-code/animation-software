"""Tests for the read-only skeleton-versus-source pelvis report."""
import contextlib
import copy
import io
import json
import math
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE / "anatomy_fit"))
import ct_pelvis_skeleton_vs_source_report as r  # noqa: E402

AUDIT = ROOT / "ORIGINAL_V1_WORK/anatomy/audit/claude_pelvis_ct_review_20261009"
COMMITTED_JSON = AUDIT / "skeleton_vs_source_inspection.json"
COMMITTED_MD = AUDIT / "skeleton_vs_source_inspection.md"
REGISTER = AUDIT / "landmark_candidate_register.json"


def load(key):
    return json.loads((ROOT / r.INPUTS[key]).read_text())


class SkeletonRecords(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs, cls.hashes = r.load_inputs(ROOT)
        cls.a, cls.c = cls.docs["a003"], cls.docs["c004"]
        cls.d = r.derive(cls.a)

    def test_c004_does_not_change_any_pelvic_lumbar_or_hip_entry(self):
        self.assertEqual(r.pelvic_set_differences(self.a, self.c), [])
        self.assertEqual(r.derive(self.c), self.d)

    def test_c004_does_differ_elsewhere_so_the_comparison_is_not_vacuous(self):
        other = sum(1 for k in self.a["bones"] if self.a["bones"][k] != self.c["bones"][k])
        self.assertGreater(other, 50)

    def test_every_requested_entry_exists_in_both_records(self):
        for rec in (self.a, self.c):
            s = r.extract_pelvic_set(rec)
            self.assertEqual(set(s["bones"]), set(r.BONES))
            self.assertEqual(set(s["markers"]), set(r.MARKERS))

    def test_inter_hjc_matches_the_independent_targets_record(self):
        stored = self.docs["pelvis_targets"]["current_a003"]["inter_HJC_mm"]
        self.assertAlmostEqual(self.d["inter_HJC_mm"], stored, places=9)
        self.assertLess(self.d["HJC_mirror_error_mm"], 1e-9)
        self.assertAlmostEqual(self.d["HJC_midpoint_mm"][0], 0.0, places=9)

    def test_sacrum_length_matches_the_independent_audit_record(self):
        stored = self.docs["pelvis_audit"]["current_a003_mm"]["sacrum_reference_span"]
        self.assertAlmostEqual(self.d["sacrum_length_mm"], stored, places=9)

    def test_s1_offset_reproduces_the_p1_records_own_difference_vector(self):
        p1 = self.docs["s1_frame_p1"]
        p1_off = p1["derived_S1_superior_endplate"]["HA_to_S1_offset_mm"]
        ours = self.d["HA_to_S1_via_sacrum_tail"]["vector_mm"]
        stored = p1["comparison_to_a003_diagnostic_only"]["a003_sacrum_tail_minus_P1_S1_mm"]
        for i in range(3):
            self.assertAlmostEqual(ours[i] - p1_off[i], stored[i], places=6)
        ours_disc = self.d["HA_to_S1_via_disc_l5_sacrum"]["vector_mm"]
        stored_disc = p1["comparison_to_a003_diagnostic_only"]["a003_disc_marker_minus_P1_S1_mm"]
        for i in range(3):
            self.assertAlmostEqual(ours_disc[i] - p1_off[i], stored_disc[i], places=6)

    def test_published_numbers_for_the_report(self):
        s1 = self.d["HA_to_S1_via_sacrum_tail"]
        self.assertAlmostEqual(s1["distance_mm"], 130.571480812, places=6)
        self.assertAlmostEqual(s1["posterior_tilt_from_vertical_deg"], 26.9949861, places=5)
        self.assertGreater(s1["vertical_mm"], 0)
        self.assertGreater(s1["posterior_mm"], 0)          # S1 is posterior to the hip axis
        sym = self.d["HA_to_pubic_symphysis"]
        self.assertLess(sym["posterior_mm"], 0)            # symphysis is anterior
        self.assertLess(sym["vertical_mm"], 0)             # and below the hip axis
        self.assertGreater(self.d["disc_l4_l5_above_HA_mm"], self.d["disc_l5_sacrum_above_HA_mm"])

    def test_low_confidence_sticks_are_reported_as_low(self):
        rep = r.build_report(ROOT)
        conf = rep["skeleton"]["bone_confidence"]
        for k in ("sacrum", "l5", "l4", "hip_bone_left", "hip_bone_right"):
            self.assertEqual(conf[k], "low")
        self.assertEqual(conf["femur_left"], "moderate")


class CorridorsAndTestability(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs, _ = r.load_inputs(ROOT)
        cls.d = r.derive(cls.docs["a003"])
        cls.rows = {x["quantity"]: x for x in r.corridor_checks(cls.docs, cls.d)}

    def test_inter_hjc_z_matches_the_stored_record_value(self):
        row = self.rows["inter-HJC distance"]
        stored = self.docs["pelvis_targets"]["evidence_convergence"]["interacetabular_HJC"]["z_vs_Tannenbaum"]
        self.assertAlmostEqual(row["z"], stored, places=9)
        self.assertTrue(row["inside_source_range"])
        self.assertIn("PMC3018214", row["citation"])

    def test_sacral_length_z_matches_the_stored_record_value(self):
        row = next(v for k, v in self.rows.items() if k.startswith("sacral length"))
        stored = self.docs["pelvis_audit"]["sacrum_length_crosscheck"]["z"]
        self.assertAlmostEqual(row["z"], stored, places=9)

    def test_pelvic_thickness_diagnostic_is_computed_not_asserted(self):
        row = next(v for k, v in self.rows.items() if k.startswith("HJC-midpoint to S1"))
        self.assertAlmostEqual(row["z"], (row["skeleton_mm"] - 107) / 8, places=9)
        self.assertGreater(row["z"], 2.5)

    def test_p1_comparison_states_the_posture_caveat(self):
        c = r.s1_p1_comparison(self.docs, self.d)
        self.assertEqual(c["P1_distance_HA_to_S1_mm"], 107)
        self.assertGreater(c["distance_difference_a003_minus_P1_mm"], 20)
        self.assertIn("supine", c["posture_note"])
        self.assertIn("pelvic incidence", c["posture_note"])

    def test_no_ct_comparison_is_ever_computable_yet(self):
        rows = r.ct_testability(self.d, self.docs)
        self.assertEqual(len(rows), 7)
        for row in rows:
            self.assertIsNone(row["ct_value"])
            self.assertEqual(row["comparison_status"], "NOT_COMPUTABLE_CT_UNVERIFIED")
            self.assertNotEqual(row["pinned_windows_suffice"], "YES")
        needs = {row["pinned_windows_suffice"] for row in rows}
        self.assertIn("NEEDS_ADDITIONAL_RANGES", needs)
        self.assertTrue(any(n.startswith("TESTABLE_ONLY_IF") for n in needs))


class ReportBehaviour(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="skelrep_"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_inputs_are_not_modified_and_output_is_deterministic(self):
        before = {p.as_posix(): r.sha256_file(ROOT / p) for p in r.INPUTS.values()}
        one = json.dumps(r.build_report(ROOT), sort_keys=True)
        two = json.dumps(r.build_report(ROOT), sort_keys=True)
        after = {p.as_posix(): r.sha256_file(ROOT / p) for p in r.INPUTS.values()}
        self.assertEqual(one, two)
        self.assertEqual(before, after)
        self.assertEqual(json.loads(one)["inputs_sha256"], before)

    def test_statements_preserve_the_governing_constraints(self):
        text = " ".join(r.STATEMENTS)
        for needle in ("source skeleton governs", "no c005", "182 cm", "not the Home Gym PT"):
            self.assertIn(needle, text)

    def test_report_flags_a_c004_change_in_the_pelvic_set(self):
        root = self.tmp / "tree"
        for rel in r.INPUTS.values():
            dst = root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / rel, dst)
        path = root / r.INPUTS["c004"]
        rec = json.loads(path.read_text())
        rec["joint_markers"]["hip_left"]["centre_m"][2] += 0.001
        path.write_text(json.dumps(rec))
        rep = r.build_report(root)
        self.assertFalse(rep["skeleton"]["c004_pelvic_set_identical_to_a003"])
        self.assertEqual(rep["skeleton"]["c004_pelvic_set_differences_from_a003"], ["marker:hip_left"])
        self.assertFalse(rep["derived_c004_equals_a003"])

    def test_outputs_are_create_only(self):
        out = self.tmp / "x.json"
        out.write_text("keep")
        with self.assertRaises(FileExistsError):
            r.write_create_only(out, "overwrite")
        self.assertEqual(out.read_text(), "keep")

    def test_check_mode_detects_drift(self):
        js, md = self.tmp / "a.json", self.tmp / "a.md"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(r.main(["--out-json", str(js), "--out-md", str(md)]), 0)
            self.assertEqual(r.main(["--check", "--out-json", str(js), "--out-md", str(md)]), 0)
            js.write_text(js.read_text().replace("166.6", "166.7"))
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(r.main(["--check", "--out-json", str(js), "--out-md", str(md)]), 1)
        self.assertIn("DRIFT", err.getvalue())

    def test_register_counts_are_read_when_provided(self):
        reg = {"image_review_performed": False,
               "landmarks": [{"status": "UNVERIFIED"}, {"status": "UNVERIFIED"},
                             {"status": "CANDIDATE"}]}
        p = self.tmp / "reg.json"
        p.write_text(json.dumps(reg))
        ct = r.build_report(ROOT, p)["ct_side"]
        self.assertEqual((ct["landmarks_VERIFIED"], ct["landmarks_CANDIDATE"],
                          ct["landmarks_UNVERIFIED"]), (0, 1, 2))

    def test_markdown_carries_the_key_findings(self):
        md = r.render_markdown(r.build_report(ROOT))
        for needle in ("c004 pelvic/lumbar/hip set identical to a003: **True**",
                       "Inter-HJC distance | 166.61 mm", "130.57 mm", "NOT_COMPUTABLE_CT_UNVERIFIED",
                       "NEEDS_ADDITIONAL_RANGES", "not a canonical 182 cm male"):
            self.assertIn(needle, md)


class CommittedEvidenceMatchesRegeneration(unittest.TestCase):
    def test_committed_report_equals_a_fresh_regeneration(self):
        rep = r.build_report(ROOT, REGISTER)
        self.assertEqual(COMMITTED_JSON.read_text(encoding="utf-8"),
                         json.dumps(rep, indent=2, sort_keys=True) + "\n")
        self.assertEqual(COMMITTED_MD.read_text(encoding="utf-8"),
                         r.render_markdown(rep) + "\n")


if __name__ == "__main__":
    unittest.main()
