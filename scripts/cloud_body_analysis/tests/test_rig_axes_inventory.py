"""Pure-Python fail-closed tests for read-only Blender bone-axis metadata."""
import ast
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[2] / "phone_blender" / "rig_axes_inventory.py"
SPEC = importlib.util.spec_from_file_location("rig_axes_inventory", MODULE)
axes = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(axes)

def sample():
    return {
        "status": "BLENDER_LOCAL_BONE_AXIS_INVENTORY_ONLY_ANATOMICAL_MAPPING_NOT_APPROVED",
        "bone_count": 2,
        "bones": [
            {"name": "pelvis", "parent": None,
             "rest_head_body_local_m": [0, 0, 1],
             "rest_tail_body_local_m": [0, 0, 1.15],
             "rest_local_X_Y_Z_unit_in_body_coordinates": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
             "pose_rotation_mode": "QUATERNION"},
            {"name": "upperarm_l", "parent": "pelvis",
             "rest_head_body_local_m": [-0.21, 0, 1.45],
             "rest_tail_body_local_m": [-0.40, 0, 1.40],
             "rest_local_X_Y_Z_unit_in_body_coordinates": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
             "pose_rotation_mode": "XYZ"},
        ],
        "model_motion_axes_calibrated_to_ISB": False,
        "actual_anatomical_joint_centres_verified": False,
        "anatomical_side_mapped": False,
        "native_human_ROM_limits_validated": False,
        "any_bones_rotated_or_keyframed": False,
    }

class RestAxisMetadataTests(unittest.TestCase):
    def test_valid_metadata_not_anatomical_approval(self):
        data = sample()
        self.assertEqual(axes.validate(data), [])
        self.assertFalse(data["native_human_ROM_limits_validated"])

    def test_bone_axis_must_be_unit(self):
        data = sample()
        data["bones"][0]["rest_local_X_Y_Z_unit_in_body_coordinates"][0] = [2, 0, 0]
        self.assertIn("axis was not unit length", axes.validate(data))

    def test_duplicate_bones_fail(self):
        data = sample()
        data["bones"][1]["name"] = "pelvis"
        self.assertIn("duplicate or invalid bone names", axes.validate(data))

    def test_invalid_parent_fails(self):
        data = sample()
        data["bones"][1]["parent"] = "unknown"
        self.assertTrue(any("unknown rig parent" in e for e in axes.validate(data)))

    def test_nonnumeric_coordinate_fails(self):
        data = sample()
        data["bones"][0]["rest_head_body_local_m"][0] = float("nan")
        self.assertTrue(any("bad rest coordinate" in e for e in axes.validate(data)))

    def test_no_unearned_joint_axes(self):
        data = sample()
        data["actual_anatomical_joint_centres_verified"] = True
        self.assertTrue(any("unearned calibration" in e for e in axes.validate(data)))

    def test_no_pose_edit_claim(self):
        data = sample()
        data["any_bones_rotated_or_keyframed"] = True
        self.assertTrue(any("unearned calibration" in e for e in axes.validate(data)))

    def test_only_metadata_no_save_or_ops(self):
        content = MODULE.read_text()
        tree = ast.parse(content)
        forbidden_calls = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            parts = []
            while isinstance(fn, ast.Attribute):
                parts.append(fn.attr)
                fn = fn.value
            if isinstance(fn, ast.Name):
                parts.append(fn.id)
            qualified = ".".join(reversed(parts))
            if (qualified.startswith("bpy.ops.") or qualified.endswith(".save_as_mainfile")
                or qualified.endswith(".mode_set")):
                forbidden_calls.append(qualified)
        self.assertEqual(forbidden_calls, [], "unexpected model-editing operator calls")
        self.assertNotIn("EditBone.roll", content.split("def inspect", 1)[0])

if __name__ == "__main__":
    unittest.main()
