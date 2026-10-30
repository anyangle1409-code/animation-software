"""Pure-Python guards for the read-only W8 authored squat pose report."""
import copy
import hashlib
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
        envelope_sides = {}
        for side, ids, x in (("l", [0], -0.1), ("r", [2], 0.1)):
            all_ids = [0, 1] if side == "l" else [2, 3]
            envelope_sides[side] = {
                "evaluated_mesh_vertex_count": 4,
                "selected_vertex_count": 2,
                "selected_vertex_ids_sha256": hashlib.sha256(
                    json_bytes(all_ids)).hexdigest(),
                "dominant_group_names": [f"foot_{side}", f"toe_{side}"],
                "lower_fraction": 0.01,
                "lower_vertex_count": 1,
                "lower_vertex_ids": ids,
                "minimum_world_z_m": 0.0,
                "lower_centroid_world_m": [x, 0.0, 0.0],
                "lower_bounds_world_m": {"min": [x, 0.0, 0.0], "max": [x, 0.0, 0.0]},
                "foot_control_head_minus_lower_centroid_world_m": [-x, 0.0, 1.0],
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
            "foot_skin_lower_envelope": {
                "status": "DESCRIPTIVE_EVALUATED_FOOT_SKIN_LOWER_ENVELOPE_NOT_CONTACT",
                "contact_claimed": False,
                "sides": envelope_sides,
            },
            "centreline": {"pelvis": bone(), "spine_01": bone()},
            "sides": {
                side: {
                    "thigh": bone(), "shin": bone(),
                    "foot": bone("XYZ"), "toe": bone("XYZ", 0.0),
                } for side in ("l", "r")
            },
        })
    data = {
        "status": "READ_ONLY_AUTHORED_SQUAT_CONTROL_STATE_ANATOMY_NOT_APPROVED",
        "model": "W8", "source_sha256": probe.W8_SHA256,
        "pinned_r57_source_commit": probe.R57_SHA,
        "source_unchanged": True, "saved_blend": False,
        "rest_bone_signature_unchanged": True,
        "anatomical_approval": "NOT_GRANTED", "ground_contact_approval": "NOT_GRANTED",
        "samples": samples,
    }
    data["skin_control_relative_motion"] = probe.skin_control_relative_motion(samples)
    baseline_keys = probe.shape_key_state([
        NS(name="Basis", value=0.0), NS(name="HGPT_K1_KNEE_l_110", value=0.0)])
    stale_keys = probe.shape_key_state([
        NS(name="Basis", value=0.0), NS(name="HGPT_K1_KNEE_l_110", value=1.0)])
    reference_geometry = [(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0)]
    neutral_geometry = probe.geometry_delta_summary(
        reference_geometry, reference_geometry)
    stale_geometry = probe.geometry_delta_summary(
        reference_geometry, [(0, 0, 0), (1.001, 0, 0), (2, 0, 0), (3, 0, 0)])
    neutral_skeleton = {
        "pose_bone_count": 77,
        "max_matrix_basis_rotation_deg_not_anatomical": 0.0,
        "max_matrix_basis_translation_mm": 0.0,
        "all_matrix_basis_identity_within_tolerance": True,
    }
    data["corrective_return_to_neutral"] = {
        "status": "DESCRIPTIVE_SKELETAL_RESET_CORRECTIVE_LIFECYCLE_NOT_ANATOMY",
        "anatomical_approval": "NOT_GRANTED",
        "tissue_safety_claimed": False,
        "sample0_reference": {
            "sample": 0,
            "shape_keys": baseline_keys,
        },
        "stages": [
            {
                "stage": "AFTER_BENCHMARK_SKELETAL_RESET_BEFORE_NEUTRAL_DRIVER_REFRESH",
                "neutral_driver_refresh_applied": False,
                "skeletal_basis": copy.deepcopy(neutral_skeleton),
                "shape_keys": stale_keys,
                "evaluated_geometry_vs_sample0": stale_geometry,
            },
            {
                "stage": "AFTER_NEUTRAL_DRIVER_REFRESH",
                "neutral_driver_refresh_applied": True,
                "skeletal_basis": copy.deepcopy(neutral_skeleton),
                "shape_keys": baseline_keys,
                "evaluated_geometry_vs_sample0": neutral_geometry,
            },
        ],
    }
    data["limitations"] = [probe.CORRECTIVE_RETURN_LIMITATION]
    return data


def json_bytes(value):
    import json
    return json.dumps(value, separators=(",", ":")).encode()


class SquatPoseStateProbeTests(unittest.TestCase):
    def test_geometry_delta_summary_zero_and_nonzero(self):
        zero = probe.geometry_delta_summary(
            [(0, 0, 0), (1, 0, 0)], [(0, 0, 0), (1, 0, 0)])
        self.assertEqual(zero["vertex_count"], 2)
        self.assertEqual(zero["changed_vertex_count_over_1e-6_mm"], 0)
        self.assertEqual(zero["max_displacement_mm"], 0.0)
        moved = probe.geometry_delta_summary(
            [(0, 0, 0), (1, 0, 0)], [(0, 0, 0), (1.003, 0, 0)])
        self.assertEqual(moved["changed_vertex_count_over_1e-6_mm"], 1)
        self.assertAlmostEqual(moved["max_displacement_mm"], 3.0)
        self.assertAlmostEqual(moved["rms_displacement_mm"], 3 / math.sqrt(2))

    def test_geometry_delta_summary_rejects_bad_inputs(self):
        with self.assertRaisesRegex(ValueError, "topology"):
            probe.geometry_delta_summary([(0, 0, 0)], [])
        with self.assertRaisesRegex(ValueError, "numerical|vector|3D"):
            probe.geometry_delta_summary([(0, 0, 0)], [(False, 0, 0)])
        with self.assertRaisesRegex(ValueError, "Nonfinite"):
            probe.geometry_delta_summary([(0, 0, 0)], [(float("nan"), 0, 0)])

    def test_shape_key_state_is_deterministic_and_strict(self):
        state = probe.shape_key_state([
            NS(name="B", value=0.5), NS(name="A", value=0.0)])
        self.assertEqual(state["key_count"], 2)
        self.assertEqual(state["nonzero_keys"], [{"name": "B", "value": 0.5}])
        reversed_state = probe.shape_key_state([
            NS(name="A", value=0.0), NS(name="B", value=0.5)])
        self.assertEqual(state["all_values_sha256"], reversed_state["all_values_sha256"])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            probe.shape_key_state([NS(name="A", value=0), NS(name="A", value=1)])
        with self.assertRaisesRegex(ValueError, "shape-key value"):
            probe.shape_key_state([NS(name="A", value=False)])

    def test_report_rejects_tampered_corrective_return_lifecycle(self):
        data = report()
        self.assertEqual(probe.validate_report(data), [])
        data["corrective_return_to_neutral"]["stages"].reverse()
        self.assertIn("invalid corrective return-to-neutral evidence", probe.validate_report(data))
        data = report()
        data["corrective_return_to_neutral"]["stages"][0][
            "neutral_driver_refresh_applied"] = 0
        self.assertIn("invalid corrective return-to-neutral evidence", probe.validate_report(data))
        data = report()
        data["corrective_return_to_neutral"]["stages"][1]["shape_keys"][
            "nonzero_keys"] = [{"name": "X", "value": 1.0}]
        self.assertIn("invalid corrective return-to-neutral evidence", probe.validate_report(data))
        data = report()
        data["corrective_return_to_neutral"]["tissue_safety_claimed"] = True
        self.assertIn("invalid corrective return-to-neutral evidence", probe.validate_report(data))
        data = report()
        data["corrective_return_to_neutral"]["stages"][0]["shape_keys"][
            "key_count"] += 1
        self.assertIn("invalid corrective return-to-neutral evidence", probe.validate_report(data))
        data = report()
        data["corrective_return_to_neutral"]["stages"][0][
            "evaluated_geometry_vs_sample0"]["vertex_count"] = 3
        data["corrective_return_to_neutral"]["stages"][1][
            "evaluated_geometry_vs_sample0"]["vertex_count"] = 3
        self.assertIn("invalid corrective return-to-neutral evidence", probe.validate_report(data))
        data = report()
        data["limitations"] = []
        self.assertIn("missing corrective return-to-neutral limitation", probe.validate_report(data))

    def test_markdown_separates_skeletal_reset_and_driver_refresh(self):
        text = probe.markdown(report())
        self.assertIn("Corrective return-to-neutral lifecycle", text)
        self.assertIn("before neutral driver refresh", text.lower())
        self.assertIn("tissue safety", text.lower())

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
        self.assertIn("Evaluated foot-skin lower envelope (not contact)", text)

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

    def test_foot_skin_envelope_selects_exact_dominant_suffix_and_lowest_percent(self):
        vertices = [(0, 0, 0.3), (1, 0, 0.1), (2, 0, 0.2),
                    (10, 0, 0.0), (11, 0, 0.4)]
        groups = ["foot_l", "toe_l", "shin_l", "foot_r", "toe_r"]
        left = probe.foot_skin_lower_envelope(vertices, groups, "l", (0, 0, 1))
        right = probe.foot_skin_lower_envelope(vertices, groups, "r", (10, 0, 1))
        self.assertEqual(left["selected_vertex_count"], 2)
        self.assertEqual(left["lower_vertex_ids"], [1])
        self.assertEqual(left["dominant_group_names"], ["foot_l", "toe_l"])
        self.assertEqual(right["lower_vertex_ids"], [3])
        self.assertEqual(right["foot_control_head_minus_lower_centroid_world_m"], [0.0, 0.0, 1.0])

    def test_foot_skin_envelope_rejects_bad_topology_or_missing_side(self):
        with self.assertRaisesRegex(ValueError, "vertex/group count"):
            probe.foot_skin_lower_envelope([(0, 0, 0)], [], "l", (0, 0, 0))
        with self.assertRaisesRegex(ValueError, "no foot/toe-dominant"):
            probe.foot_skin_lower_envelope([(0, 0, 0)], ["shin_l"], "l", (0, 0, 0))

    def test_report_rejects_false_skin_contact_or_tampered_lower_ids(self):
        data = report(); data["samples"][0]["foot_skin_lower_envelope"]["contact_claimed"] = True
        self.assertIn("invalid foot-skin lower envelope", probe.validate_report(data))
        data = report(); data["samples"][0]["foot_skin_lower_envelope"]["sides"]["l"]["lower_vertex_ids"] = [1, 1]
        self.assertIn("invalid foot-skin lower envelope", probe.validate_report(data))
        data = report(); data["samples"][0]["foot_skin_lower_envelope"]["sides"]["l"]["lower_vertex_ids"] = [4]
        self.assertIn("invalid foot-skin lower envelope", probe.validate_report(data))
        data = report(); data["samples"][4]["foot_skin_lower_envelope"]["sides"]["l"]["selected_vertex_ids_sha256"] = "a" * 64
        self.assertIn("foot-skin selection changed across samples", probe.validate_report(data))
        data = report(); data["samples"][0]["foot_skin_lower_envelope"]["sides"]["l"]["foot_control_head_minus_lower_centroid_world_m"][0] += 0.01
        self.assertIn("foot-skin/control cross-reference mismatch", probe.validate_report(data))
        data = report(); data["samples"][3]["foot_plant_solve"]["root_matrix_basis_translation_delta_m"][2] += 0.001
        self.assertIn("invalid foot-plant solve evidence", probe.validate_report(data))

    def test_skin_control_relative_motion_uses_sample_zero_reference(self):
        samples = report()["samples"]
        samples[8]["sides"]["l"]["foot"][
            "head_world_m_not_anatomical_joint_centre"][0] = 0.01
        result = probe.skin_control_relative_motion(samples)
        self.assertEqual(
            result["status"],
            "DESCRIPTIVE_FOOT_CONTROL_TO_SKIN_LOWER_CENTROID_RELATIVE_MOTION_NOT_CONTACT")
        self.assertIs(result["contact_claimed"], False)
        self.assertEqual(result["reference_sample"], 0)
        self.assertEqual(
            result["samples"][0]["sides"]["l"]["change_from_sample0_world_m"],
            [0.0, 0.0, 0.0])
        self.assertAlmostEqual(
            result["samples"][8]["sides"]["l"][
                "foot_control_head_minus_lower_centroid_world_m"][0], 0.11)
        self.assertAlmostEqual(
            result["samples"][8]["sides"]["l"]["change_from_sample0_world_m"][0],
            0.01)

    def test_skin_control_relative_motion_rejects_missing_or_nonfinite_inputs(self):
        samples = report()["samples"]
        del samples[2]["foot_skin_lower_envelope"]["sides"]["r"][
            "lower_centroid_world_m"]
        with self.assertRaisesRegex((KeyError, ValueError, TypeError), "centroid|3D|vector"):
            probe.skin_control_relative_motion(samples)
        samples = report()["samples"]
        samples[4]["sides"]["l"]["foot"][
            "head_world_m_not_anatomical_joint_centre"][1] = float("nan")
        with self.assertRaisesRegex(ValueError, "Nonfinite"):
            probe.skin_control_relative_motion(samples)

    def test_report_rejects_tampered_skin_control_relative_motion(self):
        data = report()
        self.assertEqual(probe.validate_report(data), [])
        data["skin_control_relative_motion"]["samples"][5]["sides"]["r"][
            "change_from_sample0_world_m"][2] += 0.001
        self.assertIn("invalid skin/control relative motion", probe.validate_report(data))
        data = report()
        data["skin_control_relative_motion"]["contact_claimed"] = 0
        self.assertIn("invalid skin/control relative motion", probe.validate_report(data))
        data = report()
        data["skin_control_relative_motion"]["samples"][0]["sides"]["l"][
            "change_from_sample0_world_m"][0] = False
        self.assertIn("invalid skin/control relative motion", probe.validate_report(data))
        text = probe.markdown(report())
        self.assertIn("Authored foot control relative to skin lower centroid", text)
        self.assertIn("not contact", text.lower())
        self.assertIn("tissue safety", text.lower())

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

