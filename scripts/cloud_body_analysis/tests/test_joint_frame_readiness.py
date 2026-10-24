"""Synthetic, read-only guards for joint-frame readiness and evidence claims."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts/cloud_body_analysis/joint_frame_readiness.py"
SPEC = importlib.util.spec_from_file_location("joint_frame_readiness", SCRIPT)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

def rig_fixture():
    return {
        "source_sha256": mod.PINNED_MODELS.copy(),
        "all_three_identical": True,
        "bone_counts": {"W8": 77, "V14": 77, "R120": 77},
        "metadata_fingerprints_sha256": {"W8": "a" * 64, "V14": "a" * 64, "R120": "a" * 64},
        "anatomical_side_verified": False,
        "isb_joint_axes_calibrated": False,
        "human_joint_rom_limits_approved": False,
        "skin_deformation_approved": False,
    }

class JointFrameReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = json.loads(mod.ROM.read_text())
        cls.landmarks = json.loads(mod.LANDMARKS.read_text())
        cls.ledger = json.loads(mod.LEDGER.read_text())

    def build(self, rom=None, landmarks=None, ledger=None, rig=None):
        return mod.audit(rom if rom is not None else self.rom,
                         landmarks if landmarks is not None else self.landmarks,
                         ledger if ledger is not None else self.ledger,
                         rig if rig is not None else rig_fixture())

    def test_19_scenarios_remain_blocked_with_unbound_points(self):
        report = self.build()
        self.assertEqual(report["planned_generic_motion_tests"], 19)
        self.assertEqual(report["generic_motion_tests_executed"], 0)
        self.assertEqual(report["generic_motion_tests_approved"], 0)
        self.assertEqual(report["bound_landmarks"], 0)
        self.assertEqual(report["landmark_count"], 46)
        self.assertFalse(report["joint_coordinate_frames_approved"])
        self.assertFalse(report["skin_deformation_approved"])
        self.assertFalse(report["clinical_rom_means_as_limits"])
        self.assertFalse(report["muscle_highlighting_implemented"])
        self.assertTrue(all(x["unbound_landmark_count"] > 0 or
                            x["unrepresented_segment_frames"] for x in report["scenarios"]))
        self.assertTrue(all(x["generic_motion_test_status"] == "NOT_RUN" for x in report["scenarios"]))
        self.assertIn("0/19", mod.markdown(report))

    def test_shoulder_dependency_includes_all_girdle_segments(self):
        rows = {r["id"].split(".")[-1]: r for r in self.build()["scenarios"]}
        press = rows["compound_overhead_press"]
        self.assertTrue({"thorax", "scapula", "clavicle", "humerus"}.issubset(press["checklist_segments"]))
        self.assertIn("hgpt.landmark.scapula.AI.L", press["required_unbound_landmark_ids"])
        self.assertIn("hgpt.landmark.clavicle.SC.R", press["required_unbound_landmark_ids"])
        self.assertIn("hgpt.landmark.humerus.GH_CENTER.L", press["required_unbound_landmark_ids"])
        self.assertIn("FAIL", press["existing_related_benchmark_status"])

    def test_elbow_forearm_requires_separate_radius_and_ulna(self):
        rows = {r["id"].split(".")[-1]: r for r in self.build()["scenarios"]}
        for name in ("forearm_rotation", "elbow_flexion_supinated", "compound_dumbbell_curl"):
            self.assertIn("radius_segment", rows[name]["unrepresented_segment_frames"])
            self.assertIn("ulna_segment", rows[name]["unrepresented_segment_frames"])
        self.assertIn("hgpt.landmark.humerus.EM.L",
                      rows["elbow_flexion_supinated"]["required_unbound_landmark_ids"])

    def test_lower_limb_coupling_exposes_missing_tibia_and_foot_frames(self):
        rows = {r["id"].split(".")[-1]: r for r in self.build()["scenarios"]}
        squat = rows["compound_squat"]
        self.assertIn("tibia_segment", squat["unrepresented_segment_frames"])
        self.assertIn("hindfoot_frame", squat["unrepresented_segment_frames"])
        self.assertIn("hgpt.landmark.pelvis.ASIS.R", squat["required_unbound_landmark_ids"])
        self.assertIn("FAIL", squat["existing_related_benchmark_status"])

    def test_midline_trunk_still_requires_bilateral_pelvis(self):
        rows = {r["id"].split(".")[-1]: r for r in self.build()["scenarios"]}
        row = rows["cervical_trunk_motion"]
        self.assertIn("hgpt.landmark.pelvis.PSIS.L", row["required_unbound_landmark_ids"])
        self.assertIn("hgpt.landmark.pelvis.PSIS.R", row["required_unbound_landmark_ids"])

    def test_refuses_missing_landmark(self):
        d = copy.deepcopy(self.landmarks)
        d["landmarks"] = [x for x in d["landmarks"] if x["id"] != "hgpt.landmark.scapula.TS.L"]
        d["landmark_count"] = len(d["landmarks"])
        with self.assertRaisesRegex(ValueError, "registry count mismatch"):
            self.build(landmarks=d)

    def test_refuses_guessed_bone_attachment(self):
        d = copy.deepcopy(self.landmarks)
        d["landmarks"][0]["model_bone_id"] = "spine_03"
        with self.assertRaisesRegex(ValueError, "unbound"):
            self.build(landmarks=d)

    def test_refuses_clinical_means_as_limits(self):
        d = copy.deepcopy(self.rom)
        d["rom_mean_is_a_hard_limit"] = True
        with self.assertRaisesRegex(ValueError, "hard limits"):
            self.build(rom=d)

    def test_refuses_unearned_native_approval(self):
        r = rig_fixture()
        r["isb_joint_axes_calibrated"] = True
        with self.assertRaisesRegex(ValueError, "pinned native"):
            self.build(rig=r)

    def test_refuses_unexecuted_scenario_marked_pass(self):
        d = copy.deepcopy(self.ledger)
        d["tests"][0]["generic_joint_suite_status"] = "PASS"
        with self.assertRaisesRegex(ValueError, "executed or approved"):
            self.build(ledger=d)

    def test_refuses_unknown_family_instead_of_silent_success(self):
        d = copy.deepcopy(self.rom)
        d["motion_test_program"][0]["required_joint_families"].append("invented_joint")
        with self.assertRaisesRegex(ValueError, "unknown joint family"):
            self.build(rom=d)

    def test_report_does_not_import_blender_or_save_models(self):
        source = SCRIPT.read_text()
        self.assertNotIn("import bpy", source)
        self.assertNotIn("save_as_mainfile", source)
        self.assertNotIn("write_bytes(", source)

if __name__ == "__main__":
    unittest.main()
