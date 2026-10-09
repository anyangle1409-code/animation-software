"""Tests for the CT landmark candidate register and its fail-closed validator."""
import contextlib
import copy
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE / "anatomy_fit"))
sys.path.insert(0, str(HERE))
import ct_landmark_register as reg  # noqa: E402
import ct_pelvis_window_geometry as g  # noqa: E402
from test_ct_pelvis_window_geometry import header_text, S_BY_ID  # noqa: E402

AUDIT = ROOT / "ORIGINAL_V1_WORK/anatomy/audit/claude_pelvis_ct_review_20261009"
PINNED = AUDIT / "pinned_six_frames_from_pr15_4680b49.json"
COMMITTED = AUDIT / "landmark_candidate_register.json"
MAN = g.load_pinned_manifest(PINNED)


def geoms():
    return {sid: g.parse_scanner_header(header_text(S_BY_ID[sid]).encode()) for sid in g.ALL_IDS}


def observed(lm_id="ACETABULUM_L", sid=1752, row=100, col=200, status="CANDIDATE"):
    r = copy.deepcopy(json.loads(COMMITTED.read_text()))
    lm = next(x for x in r["landmarks"] if x["id"] == lm_id)
    pin = {**MAN["by_id"][sid], "source_id": sid}
    rej = [c.split(":")[0] for c in lm["rejection_conditions"]]
    lm["observation"] = reg.build_observation(geoms()[sid], pin, row, col, "outer_edge", 2.0, "rev-A",
                                              "2026-10-10", "liver on image left", [{"source": "atlas", "figure": "3"}],
                                              rej, 0, 4000)
    lm["status"], lm["confidence"] = status, "LOW"
    r["image_review_performed"] = True
    return r, lm


class Register(unittest.TestCase):
    def test_committed_register_valid_and_all_unverified(self):
        r = json.loads(COMMITTED.read_text())
        self.assertTrue(reg.validate_register(r, MAN))
        self.assertEqual({x["status"] for x in r["landmarks"]}, {"UNVERIFIED"})
        self.assertIs(r["image_review_performed"], False)
        for f in reg.FORBIDDEN_TRUE:
            self.assertIs(r[f], False)

    def test_committed_equals_fresh_blank(self):
        fresh = reg.build_blank_register(str(AUDIT / "pinned_six_frames_from_pr15_4680b49.json"),
                                         "x", "2026-10-09")
        old = json.loads(COMMITTED.read_text())
        self.assertEqual(fresh["landmarks"], old["landmarks"])

    def test_classes_covered_and_every_landmark_has_rejections_and_citations(self):
        r = json.loads(COMMITTED.read_text())
        self.assertEqual({x["structure_class"] for x in r["landmarks"]},
                         {"iliac_blade", "sacrum", "acetabulum", "femoral_head", "pubic_region"})
        for x in r["landmarks"]:
            self.assertGreaterEqual(len(x["rejection_conditions"]), 3)
            self.assertTrue(x["anatomical_citations"])

    def test_candidate_with_full_evidence_validates_with_and_without_geometry(self):
        r, _ = observed()
        self.assertTrue(reg.validate_register(r, MAN))
        self.assertTrue(reg.validate_register(r, MAN, geoms()))

    def test_candidate_without_observation_rejected(self):
        r, lm = observed()
        lm["observation"] = None
        with self.assertRaises(reg.RegisterError):
            reg.validate_register(r, MAN)

    def test_each_missing_observation_field_rejected(self):
        for k in reg.OBS_REQUIRED:
            r, lm = observed()
            del lm["observation"][k]
            with self.assertRaises(reg.RegisterError, msg=k):
                reg.validate_register(r, MAN)

    def test_sha_mismatch_and_wrong_filename_rejected(self):
        for k, v in (("png_sha256", "0" * 64), ("header_sha256", "1" * 64), ("png_filename", "cvm1800f.png")):
            r, lm = observed()
            lm["observation"][k] = v
            with self.assertRaises(reg.RegisterError, msg=k):
                reg.validate_register(r, MAN)

    def test_unpinned_source_and_bad_pixel_rejected(self):
        for k, v in (("source_id", 1758), ("row", 512), ("col", -1), ("row", 1.5), ("slice_thickness_mm", 5.0)):
            r, lm = observed()
            lm["observation"][k] = v
            with self.assertRaises(reg.RegisterError, msg=k):
                reg.validate_register(r, MAN)

    def test_triggered_or_unchecked_rejection_condition_blocks(self):
        r, lm = observed()
        key = next(iter(lm["observation"]["rejection_conditions_checked"]))
        lm["observation"]["rejection_conditions_checked"][key] = "triggered"
        with self.assertRaises(reg.RegisterError):
            reg.validate_register(r, MAN)
        r, lm = observed()
        lm["observation"]["rejection_conditions_checked"].pop(key)
        with self.assertRaises(reg.RegisterError):
            reg.validate_register(r, MAN)

    def test_narrow_envelope_or_wrong_slab_rejected(self):
        r, lm = observed()
        lm["observation"]["uncertainty_envelope"]["in_plane_half_width_mm"] = 0.1
        with self.assertRaises(reg.RegisterError):
            reg.validate_register(r, MAN)
        r, lm = observed()
        lm["observation"]["uncertainty_envelope"]["scanner_S_range_mm"] = [-361, -359]
        with self.assertRaises(reg.RegisterError):
            reg.validate_register(r, MAN)

    def test_geometry_recomputation_catches_tampered_coordinates(self):
        r, lm = observed()
        lm["observation"]["scanner_RAS_candidate_mm"][0] += 5.0
        self.assertTrue(reg.validate_register(r, MAN))
        with self.assertRaises(reg.RegisterError):
            reg.validate_register(r, MAN, geoms())

    def test_status_confidence_consistency(self):
        r, lm = observed()
        lm["confidence"] = "NONE"
        with self.assertRaises(reg.RegisterError):
            reg.validate_register(r, MAN)
        r = json.loads(COMMITTED.read_text())
        r["landmarks"][0]["confidence"] = "LOW"
        with self.assertRaises(reg.RegisterError):
            reg.validate_register(r, MAN)
        r = json.loads(COMMITTED.read_text())
        r["landmarks"][0]["status"] = "PROBABLE"
        with self.assertRaises(reg.RegisterError):
            reg.validate_register(r, MAN)

    def test_observations_require_image_review_flag(self):
        r, _ = observed()
        r["image_review_performed"] = False
        with self.assertRaises(reg.RegisterError):
            reg.validate_register(r, MAN)

    def test_promotion_flags_cannot_be_true(self):
        for f in reg.FORBIDDEN_TRUE:
            r = json.loads(COMMITTED.read_text())
            r[f] = True
            with self.assertRaises(reg.RegisterError, msg=f):
                reg.validate_register(r, MAN)

    def test_verified_requires_support_second_reviewer_and_confidence(self):
        r, lm = observed(status="VERIFIED")
        with self.assertRaises(reg.RegisterError):
            reg.validate_register(r, MAN)
        lm["confidence"] = "MODERATE"
        lm["supporting_frames"] = [{"source_id": 1752, "consistent": True}, {"source_id": 1755, "consistent": True}]
        with self.assertRaises(reg.RegisterError):
            reg.validate_register(r, MAN)
        lm["independent_second_review"] = {"reviewer": "rev-A", "agrees": True, "review_date": "2026-10-11"}
        with self.assertRaises(reg.RegisterError):      # same person
            reg.validate_register(r, MAN)
        lm["independent_second_review"]["reviewer"] = "rev-B"
        self.assertTrue(reg.validate_register(r, MAN))
        lm["supporting_frames"][1]["source_id"] = 1800  # other window
        with self.assertRaises(reg.RegisterError):
            reg.validate_register(r, MAN)

    def test_duplicate_id_rejected(self):
        r = json.loads(COMMITTED.read_text())
        r["landmarks"].append(copy.deepcopy(r["landmarks"][0]))
        with self.assertRaises(reg.RegisterError):
            reg.validate_register(r, MAN)

    def test_no_private_paths_or_pixels_in_register(self):
        text = COMMITTED.read_text()
        self.assertNotIn("/home/", text.replace("/home/claude/wt", ""))


class Cli(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="reg_"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_init_is_create_only_and_valid(self):
        out = self.tmp / "r.json"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(reg._cli(["init", "--manifest", str(PINNED), "--out", str(out)]), 0)
            with self.assertRaises(FileExistsError):
                reg._cli(["init", "--manifest", str(PINNED), "--out", str(out)])
            self.assertEqual(reg._cli(["validate", "--register", str(out), "--manifest", str(PINNED)]), 0)


if __name__ == "__main__":
    unittest.main()
