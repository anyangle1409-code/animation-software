"""Synthetic fail-closed guards for the real-artifact read-only timeline reader."""
import copy
import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "pose_failure_timeline.py"
spec = importlib.util.spec_from_file_location("pose_failure_timeline", SOURCE)
pf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pf)


def fixture():
    samples = []
    for i in range(9):
        target = 90 + 8*i
        sides = {}
        for suffix in ("l", "r"):
            sides[suffix] = {
                "humerothoracic_elevation_measured_by_pinned_driver_deg": target-2,
                "target_minus_driver_measurement_deg": 2,
                "cap_helper_present": True, "cap_local_delta_angle_deg_not_absolute": 30+i,
                "axilla_helper_present": False, "axilla_local_delta_angle_deg_not_absolute": None,
                "actual_shape_key_values": [
                    {"name": f"HGPT_{family}_{suffix}_{angle}", "actual_value": float(i/8)}
                    for family, angle in (("C1_ARMTRUNK", 0), ("S1_SHOULDER", 105),
                                          ("S3_SHAPE", 100), ("S5_BAKE", 110), ("S7_DELT", 120))],
            }
        samples.append({"sample": i, "t": i/8,
                        "authored_press_ht_target_deg_NOT_measured": target,
                        "sides": sides, "actual_native_deformation_metrics": {
                            "collapse_lt_0_1": i, "stretch_gt_2": 100+i*i,
                            "self_intersecting_pairs": i*2, "body_volume_change_pct": 0.2+i*0.01}})
    return {"status": "READ_ONLY_IN_MEMORY_POSE_STATE_ANATOMY_NOT_APPROVED",
            "model": "W8", "source_sha256": pf.W8_SOURCE_SHA256,
            "pinned_r57_source_commit": pf.PINNED_DRIVER_REV,
            "source_unchanged": True, "saved_blend": False, "rest_bone_signature_unchanged": True,
            "anatomical_approval": "NOT_GRANTED", "quality_approval": "NOT_GRANTED",
            "model_is_reconstruction_not_approved_original": True,
            "key_values_measured_after_actual_post_pose_driver_call": True,
            "samples": samples}


class PoseFailureTimelineTests(unittest.TestCase):
    def setUp(self):
        self.doc = fixture()

    def reject(self, change, message):
        doc = copy.deepcopy(self.doc)
        change(doc)
        with self.assertRaisesRegex(ValueError, message):
            pf.summarize(doc, input_sha256="synthetic")

    def test_synthetic_timeline_aggregates_counts_not_triangle_ids(self):
        report = pf.summarize(self.doc, input_sha256="synthetic")
        self.assertEqual(report["observed_sample_count"], 9)
        self.assertEqual(report["metrics"]["stretch_gt_2"]["peak"], 164)
        self.assertEqual(report["metrics"]["stretch_gt_2"]["peak_samples"], [8])
        self.assertFalse(report["isb_joint_frames_approved"])
        self.assertFalse(report["skin_deformation_approved"])
        self.assertEqual(report["generic_motion_tests_executed"], 0)
        self.assertIn("No causality", pf.markdown(report))

    def test_accepts_and_summarizes_new_observed_k1_without_requiring_old_reports(self):
        for sample in self.doc['samples']:
            for suffix in ('l', 'r'):
                sample['sides'][suffix]['actual_shape_key_values'].append(
                    {'name': f'HGPT_K1_ELBOW_{suffix}_90', 'actual_value': 0.75})
        report = pf.summarize(self.doc, input_sha256='synthetic')
        family = report['observed_frames'][0]['suffixes_NOT_anatomical_sides']['l']['families']['K1_ELBOW']
        self.assertEqual(family['largest_weight'], 0.75)
        self.assertEqual(family['active_key_count'], 1)
        old_report = pf.summarize(fixture(), input_sha256='old_synthetic')
        self.assertNotIn('K1_ELBOW', old_report['observed_frames'][0]['suffixes_NOT_anatomical_sides']['l']['families'])

    def test_new_k1_observations_still_reject_wrong_suffix_and_unknown_family(self):
        for name in ('HGPT_K1_ELBOW_r_90', 'HGPT_UNKNOWN_l_90'):
            with self.subTest(name=name):
                self.reject(lambda d: d['samples'][0]['sides']['l']['actual_shape_key_values'].append(
                    {'name': name, 'actual_value': 0.1}), 'invalid, wrong-suffix')

    def test_rejects_unpinned_source(self):
        self.reject(lambda d: d.update(source_sha256="0"*64), "provenance")

    def test_rejects_unpinned_driver(self):
        self.reject(lambda d: d.update(pinned_r57_source_commit="other"), "provenance")

    def test_rejects_saved_model(self):
        self.reject(lambda d: d.update(saved_blend=True), "provenance")

    def test_rejects_unearned_approval(self):
        self.reject(lambda d: d.update(anatomical_approval="APPROVED"), "provenance")

    def test_rejects_missing_sample(self):
        self.reject(lambda d: d["samples"].pop(), "nine")

    def test_rejects_reordered_sample(self):
        self.reject(lambda d: d["samples"].__setitem__(2, d["samples"][3]), "index")

    def test_rejects_bad_time(self):
        self.reject(lambda d: d["samples"][4].update(t=0.6), "time")

    def test_rejects_missing_side(self):
        self.reject(lambda d: d["samples"][4]["sides"].pop("r"), "suffixes")

    def test_rejects_inconsistent_driver_offset(self):
        self.reject(lambda d: d["samples"][4]["sides"]["l"].update(target_minus_driver_measurement_deg=4), "inconsistent")

    def test_rejects_bad_metric(self):
        self.reject(lambda d: d["samples"][4]["actual_native_deformation_metrics"].update(stretch_gt_2=-1), "nonnegative")

    def test_rejects_nonfinite_metric(self):
        self.reject(lambda d: d["samples"][4]["actual_native_deformation_metrics"].update(body_volume_change_pct=float('nan')), "finite")

    def test_rejects_duplicate_key(self):
        self.reject(lambda d: d["samples"][4]["sides"]["l"]["actual_shape_key_values"].append(
            d["samples"][4]["sides"]["l"]["actual_shape_key_values"][0].copy()), "duplicate")

    def test_rejects_out_of_range_key(self):
        self.reject(lambda d: d["samples"][4]["sides"]["l"]["actual_shape_key_values"][0].update(actual_value=1.5), "out-of-range")

    def test_rejects_shape_key_inventory_change(self):
        self.reject(lambda d: d["samples"][4]["sides"]["l"]["actual_shape_key_values"].append(
            {"name": "HGPT_S7_DELT_l_166", "actual_value": 0.0}), "inventory")

    def test_rejects_helper_without_angle(self):
        self.reject(lambda d: d["samples"][4]["sides"]["l"].update(cap_local_delta_angle_deg_not_absolute=None), "finite")

    def test_rejects_false_axilla_angle(self):
        self.reject(lambda d: d["samples"][4]["sides"]["l"].update(axilla_local_delta_angle_deg_not_absolute=42), "absent axilla")

    def test_readonly_no_blender_calls(self):
        source = SOURCE.read_text()
        self.assertNotIn("import bpy", source)
        self.assertNotIn("save_as_mainfile", source)
        self.assertNotIn(".blend", source)


if __name__ == "__main__":
    unittest.main()
