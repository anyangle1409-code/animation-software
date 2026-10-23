"""Regression tests for native three-model rest-axis metadata comparison."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / "compare_rig_axes.py"
SPEC = importlib.util.spec_from_file_location("compare_rig_axes", MODULE)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

def bone(name, x):
    return {
        "name": name, "parent": None,
        "rest_head_body_local_m": [x, 0, 1],
        "rest_tail_body_local_m": [x, 0, 0.8],
        "rest_local_X_Y_Z_unit_in_body_coordinates": [[1,0,0],[0,1,0],[0,0,1]],
        "axis_noncircularity_dot_max": 0.0, "roll_radians_stored": None,
        "use_deform": True, "connected_to_parent": False,
        "pose_rotation_mode": "XYZ", "pose_constraint_metadata": [],
    }

def fixture(root, model):
    d = {
        "model": model, "source_sha256": mod.EXPECTED[model],
        "original_source_unchanged": True,
        "status": "BLENDER_LOCAL_BONE_AXIS_INVENTORY_ONLY_ANATOMICAL_MAPPING_NOT_APPROVED",
        "bone_count": 2, "bones": [bone("upperarm_l", -0.1), bone("upperarm_r", 0.1)],
        "rig_object": "rig", "body_object": "body",
        "body_modifier_metadata": [], "run": "unit-test",
    }
    d.update({k: False for k in mod.NOT_GRANTED})
    folder = root / model
    folder.mkdir()
    (folder / "rig_rest_axes_metadata.json").write_text(json.dumps(d))

class RigAxesComparatorTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        for m in mod.MODELS:
            fixture(self.root, m)

    def edit(self, model, fn):
        path = self.root / model / "rig_rest_axes_metadata.json"
        d = json.loads(path.read_text())
        fn(d)
        path.write_text(json.dumps(d))

    def test_matching_axes_do_not_certify_human_anatomy(self):
        result = mod.compare(self.root)
        self.assertTrue(result["all_three_identical"])
        self.assertEqual(len(set(result["metadata_fingerprints_sha256"].values())), 1)
        self.assertEqual(result["w8_max_head_reflection_residual_mm"], 0)
        self.assertEqual(result["w8_max_tail_reflection_residual_mm"], 0)
        self.assertFalse(result["anatomical_side_verified"])
        self.assertFalse(result["isb_joint_axes_calibrated"])
        self.assertFalse(result["skin_deformation_approved"])
        self.assertIn("NOT certified human anatomical axes", mod.markdown(result))

    def test_source_hash_mismatch_rejected(self):
        self.edit("V14", lambda d: d.update(source_sha256="wrong"))
        with self.assertRaisesRegex(ValueError, "pinned source"):
            mod.compare(self.root)

    def test_source_mutation_rejected(self):
        self.edit("W8", lambda d: d.update(original_source_unchanged=False))
        with self.assertRaisesRegex(ValueError, "preservation"):
            mod.compare(self.root)

    def test_fake_anatomy_approval_rejected(self):
        self.edit("R120", lambda d: d.update(isb_joint_axes_calibrated=True))
        self.edit("R120", lambda d: d.update(model_motion_axes_calibrated_to_ISB=True))
        with self.assertRaisesRegex(ValueError, "unearned anatomy"):
            mod.compare(self.root)

    def test_duplicate_names_rejected(self):
        self.edit("V14", lambda d: d["bones"][1].update(name="upperarm_l"))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            mod.compare(self.root)

    def test_invalid_parent_rejected(self):
        self.edit("W8", lambda d: d["bones"][1].update(parent="missing"))
        with self.assertRaisesRegex(ValueError, "parent"):
            mod.compare(self.root)

    def test_nonfinite_position_rejected(self):
        self.edit("W8", lambda d: d["bones"][0]["rest_head_body_local_m"].__setitem__(0, float("nan")))
        with self.assertRaisesRegex(ValueError, "coordinates"):
            mod.compare(self.root)

    def test_nonunit_basis_rejected(self):
        self.edit("R120", lambda d: d["bones"][0]["rest_local_X_Y_Z_unit_in_body_coordinates"][0].__setitem__(0, 3))
        with self.assertRaisesRegex(ValueError, "non-unit"):
            mod.compare(self.root)

    def test_nonorthogonal_basis_rejected(self):
        self.edit("V14", lambda d: d["bones"][0]["rest_local_X_Y_Z_unit_in_body_coordinates"][0].__setitem__(1, 0.0015))
        with self.assertRaisesRegex(ValueError, "nonorthogonal"):
            mod.compare(self.root)

    def test_actual_bone_difference_not_silent_success(self):
        self.edit("R120", lambda d: d["bones"][0]["rest_tail_body_local_m"].__setitem__(2, 0.7))
        result = mod.compare(self.root)
        self.assertFalse(result["all_three_identical"])
        self.assertIn("upperarm_l", result["differences_vs_W8"]["R120"])
        self.assertFalse(result["human_joint_rom_limits_approved"])

    def test_mirror_not_anatomical_side(self):
        self.edit("W8", lambda d: d["bones"][1]["rest_head_body_local_m"].__setitem__(0, 0.12))
        result = mod.compare(self.root)
        self.assertGreater(result["w8_max_head_reflection_residual_mm"], 0)
        self.assertFalse(result["anatomical_side_verified"])

    def test_no_blender_model_write(self):
        source = MODULE.read_text()
        self.assertNotIn("import bpy", source)
        self.assertNotIn("save_as_mainfile(", source)

if __name__ == "__main__":
    unittest.main()
