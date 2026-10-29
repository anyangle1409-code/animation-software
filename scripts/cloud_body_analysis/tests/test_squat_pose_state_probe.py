"""Pure-Python guards for the read-only W8 authored squat pose report."""
import copy
import importlib.util
import math
from pathlib import Path
from types import SimpleNamespace as NS
import unittest

MODULE = Path(__file__).resolve().parents[2] / "phone_blender" / "squat_pose_state_probe.py"
SPEC = importlib.util.spec_from_file_location("squat_pose_state_probe", MODULE)
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


def bone(mode="XYZ", angle=12.0, head=(0.0, 0.0, 1.0), tail=(0.0, 0.0, 0.8)):
    return {
        "control_present": True,
        "pose_rotation_mode": mode,
        "local_delta_angle_deg_not_anatomical": angle,
        "head_world_m_not_anatomical_joint_centre": list(head),
        "tail_world_m": list(tail),
    }


def report():
    samples = []
    for i in range(9):
        k = probe.smooth(i / 8)
        pre_root = [0.0, 0.0, 0.0]
        post_root = [0.0, 0.01 * k, -0.02 * k]
        solve_sides = {}
        for side, sign in (("l", -1), ("r", 1)):
            target = [0.09 * sign, 0.0, 0.085]
            pre_head = [target[0] + 0.002 * sign * k, 0.03 * k, 0.04 * k]
            post_head = [target[0] + 0.002 * sign * k, 0.0, 0.085]
            solve_sides[side] = {
                "rest_target_head_world_m_not_verified_joint_centre": target,
                "pre_solve_foot_head_world_m": pre_head,
                "pre_solve_residual_world_m": [a - b for a, b in zip(pre_head, target)],
                "post_solve_foot_head_world_m": post_head,
                "post_solve_residual_world_m": [a - b for a, b in zip(post_head, target)],
                "pre_solve_foot_local_delta_deg_not_anatomical": 0.0,
                "post_solve_foot_local_delta_deg_not_anatomical": 5 * k,
            }
        samples.append({
            "sample": i,
            "t": i / 8,
            "authored_targets_deg_not_measured": {
                "pelvis_forward_tilt": 25 * k,
                "spine_extension": 10 * k,
                "hip_flexion": 110 * k,
                "knee_flexion": 110 * k,
            },
            "measured_authored_ankle_dorsiflexion_deg_not_isb": 15 * k,
            "evaluated_body_lowest_world_z_m_not_contact": 0.001,
            "root_matrix_basis_translation_m": post_root,
            "foot_plant_solve": {
                "pre_root_matrix_basis_translation_m": pre_root,
                "post_root_matrix_basis_translation_m": post_root,
                "root_matrix_basis_translation_delta_m": [b - a for a, b in zip(pre_root, post_root)],
                "mean_post_solve_residual_world_m": [0.0, 0.0, 0.0],
                "sides": solve_sides,
            },
            "centreline": {"pelvis": bone(), "spine_01": bone()},
            "sides": {
                side: {
                    "thigh": bone(), "shin": bone(),
                    "foot": bone("XYZ"), "toe": bone("XYZ", 0.0),
                } for side in ("l", "r")
            },
        })
    return {
        "status": "READ_ONLY_AUTHORED_SQUAT_CONTROL_STATE_ANATOMY_NOT_APPROVED",
        "model": "W8", "source_sha256": probe.W8_SHA256,
        "pinned_r57_source_commit": probe.R57_SHA,
        "source_unchanged": True, "saved_blend": False,
        "rest_bone_signature_unchanged": True,
        "anatomical_approval": "NOT_GRANTED", "ground_contact_approval": "NOT_GRANTED",
        "samples": samples,
    }


class SquatPoseStateProbeTests(unittest.TestCase):
    def test_smooth_endpoints_and_midpoint(self):
        self.assertEqual(probe.smooth(0), 0)
        self.assertEqual(probe.smooth(0.5), 0.5)
        self.assertEqual(probe.smooth(1), 1)

    def test_quaternion_angle_is_sign_canonical_and_finite(self):
        class Q:
            def __init__(self, angle): self.angle = angle
            def copy(self): return Q(self.angle)
            def normalize(self): pass
        self.assertAlmostEqual(probe.q_angle_deg(Q(math.radians(350))), 10)
        with self.assertRaisesRegex(ValueError, "Nonfinite"):
            probe.q_angle_deg(Q(float("nan")))

    def test_valid_report_and_markdown(self):
        data = report()
        self.assertEqual(probe.validate_report(data), [])
        text = probe.markdown(data)
        self.assertIn("authored squat-control observations", text)
        self.assertIn("not ISB", text)
        self.assertIn("NOT verified ground contact", text)
        self.assertIn("Foot-plant solve residuals", text)

    def test_requires_exact_nine_ordered_samples(self):
        data = report()
        data["samples"].pop()
        self.assertIn("samples 0 through 8 required", probe.validate_report(data))
        data = report()
        data["samples"][5]["sample"] = 4
        self.assertIn("samples 0 through 8 required", probe.validate_report(data))

    def test_rejects_false_approval_or_saved_source(self):
        data = report(); data["anatomical_approval"] = "APPROVED"
        self.assertIn("invalid evidence scope", probe.validate_report(data))
        data = report(); data["saved_blend"] = True
        self.assertIn("invalid evidence scope", probe.validate_report(data))
        data = report(); data["ground_contact_approval"] = "GRANTED"
        self.assertIn("invalid evidence scope", probe.validate_report(data))

    def test_rejects_missing_side_or_control(self):
        data = report(); del data["samples"][0]["sides"]["r"]
        self.assertIn("both runtime suffix sides required", probe.validate_report(data))
        data = report(); data["samples"][0]["sides"]["l"]["foot"]["control_present"] = False
        self.assertIn("missing authored lower-limb control", probe.validate_report(data))

    def test_rejects_wrong_pinned_rotation_mode(self):
        data = report(); data["samples"][0]["sides"]["l"]["thigh"]["pose_rotation_mode"] = "ZYX"
        self.assertIn("unexpected authored control rotation mode", probe.validate_report(data))
        data = report(); data["samples"][0]["sides"]["l"]["foot"]["pose_rotation_mode"] = "QUATERNION"
        self.assertIn("unexpected authored control rotation mode", probe.validate_report(data))

    def test_rejects_nonfinite_or_out_of_range_values(self):
        data = report(); data["samples"][0]["root_matrix_basis_translation_m"][0] = float("nan")
        self.assertIn("invalid root translation", probe.validate_report(data))
        data = report(); data["samples"][0]["sides"]["l"]["shin"]["local_delta_angle_deg_not_anatomical"] = 181
        self.assertIn("invalid local delta", probe.validate_report(data))
        data = report(); data["samples"][0]["sides"]["l"]["toe"]["head_world_m_not_anatomical_joint_centre"] = [0, 0]
        self.assertIn("invalid authored control trajectory point", probe.validate_report(data))

    def test_rejects_authored_target_drift(self):
        data = report(); data["samples"][4]["authored_targets_deg_not_measured"]["hip_flexion"] += 0.01
        self.assertIn("authored target drift", probe.validate_report(data))

    def test_plant_solve_summary_separates_average_from_bilateral_residual(self):
        pre = {
            "root_matrix_basis_translation_m": [0.0, 0.0, 0.0],
            "sides": {
                "l": {"foot_head_world_m": [-0.08, 0.03, 0.04], "rest_target_head_world_m": [-0.09, 0.0, 0.085], "foot_local_delta_deg": 0.0},
                "r": {"foot_head_world_m": [0.08, 0.03, 0.04], "rest_target_head_world_m": [0.09, 0.0, 0.085], "foot_local_delta_deg": 0.0},
            },
        }
        post = {
            "root_matrix_basis_translation_m": [0.0, -0.03, 0.045],
            "sides": {
                "l": {"foot_head_world_m": [-0.08, 0.0, 0.085], "rest_target_head_world_m": [-0.09, 0.0, 0.085], "foot_local_delta_deg": 10.0},
                "r": {"foot_head_world_m": [0.08, 0.0, 0.085], "rest_target_head_world_m": [0.09, 0.0, 0.085], "foot_local_delta_deg": 10.0},
            },
        }
        result = probe.plant_solve_summary(pre, post)
        self.assertEqual(result["root_matrix_basis_translation_delta_m"], [0.0, -0.03, 0.045])
        self.assertEqual(result["mean_post_solve_residual_world_m"], [0.0, 0.0, 0.0])
        self.assertAlmostEqual(result["sides"]["l"]["post_solve_residual_world_m"][0], 0.01)
        self.assertAlmostEqual(result["sides"]["r"]["post_solve_residual_world_m"][0], -0.01)

    def test_tracked_plant_capture_updates_before_pre_and_post_observation(self):
        events = []
        stages = iter(("pre", "post"))
        result = probe.run_tracked_plant_solve(
            "rig", "heads",
            update=lambda: events.append("update"),
            original_solve=lambda rig, heads: events.append(("solve", rig, heads)),
            stage=lambda rig, heads: (events.append(("stage", rig, heads)), next(stages))[1],
        )
        self.assertEqual(result, ("pre", "post"))
        self.assertEqual(events, [
            "update", ("stage", "rig", "heads"),
            ("solve", "rig", "heads"),
            "update", ("stage", "rig", "heads"),
        ])

    def test_report_rejects_tampered_solve_residual_or_root_delta(self):
        data = report(); data["samples"][3]["foot_plant_solve"]["sides"]["l"]["post_solve_residual_world_m"][0] += 0.001
        self.assertIn("invalid foot-plant solve evidence", probe.validate_report(data))
        data = report(); data["samples"][3]["foot_plant_solve"]["root_matrix_basis_translation_delta_m"][2] += 0.001
        self.assertIn("invalid foot-plant solve evidence", probe.validate_report(data))

    def test_bone_record_uses_matrix_basis_and_model_space(self):
        class Q:
            angle = math.radians(20)
            def copy(self): return self
            def normalize(self): pass
        pb = NS(rotation_mode="XYZ", matrix_basis=NS(to_quaternion=lambda: Q()),
                head=(1.0, 2.0, 3.0), tail=(4.0, 5.0, 6.0))
        identity = NS(__matmul__=lambda self, value: value)
        # Python special-method lookup ignores instance attributes; use a tiny class.
        class M:
            def __matmul__(self, value): return value
        row = probe.bone_record({"thigh_l": pb}, M(), "thigh_l")
        self.assertEqual(row["pose_rotation_mode"], "XYZ")
        self.assertAlmostEqual(row["local_delta_angle_deg_not_anatomical"], 20)
        self.assertEqual(row["head_world_m_not_anatomical_joint_centre"], [1.0, 2.0, 3.0])

    def test_probe_never_saves_or_rewrites_a_blend(self):
        source = MODULE.read_text(encoding="utf-8")
        self.assertNotIn("save_as_mainfile", source)
        self.assertNotIn("save_mainfile", source)
        self.assertNotIn("bpy.data.libraries.write", source)


if __name__ == "__main__":
    unittest.main()
