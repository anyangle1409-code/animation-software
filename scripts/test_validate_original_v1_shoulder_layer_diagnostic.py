"""Tests for shoulder deformation-layer diagnostic output validation."""
import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).with_name("validate_original_v1_shoulder_layer_diagnostic.py")
SPEC = importlib.util.spec_from_file_location("shoulder_layer_validator", MODULE_PATH)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class ShoulderLayerDiagnosticValidatorTests(unittest.TestCase):
    def fixture(self):
        counts = {z: 4 for z in mod.REQUIRED_ZONES}
        ownership = {z: {"count": 4, "mean_total_trunk_weight": 0.5, "top_mean_bone_weights": []} for z in mod.REQUIRED_ZONES}
        families = {"abduction": ["A_L", "A_R"], "flexion": ["F_L", "F_R"], "scapular": ["S_L", "S_R"]}

        def row(f):
            zones = {}
            for z in mod.REQUIRED_ZONES:
                base = {"count": 4, "mean_m": 0.0, "p95_m": 0.0, "max_m": 0.0,
                        "n_over_5mm": 0, "n_over_10mm": 0, "n_over_20mm": 0}
                zones[z] = {
                    "weights_vs_trunk_proxy": dict(base),
                    "shoulder_combined_vs_weights": dict(base),
                    "all_active_shapes_vs_weights": dict(base),
                    "abduction_vs_weights": dict(base),
                    "flexion_vs_weights": dict(base),
                    "scapular_vs_weights": dict(base),
                }
            return {
                "fraction": f,
                "elevation_l_deg": 90.0 * f,
                "elevation_r_deg": 90.0 * f,
                "shape_key_values": {},
                "family_activation": {k: {} for k in families},
                "linear_decomposition_residual_max_m": 0.0,
                "zones": zones,
                "top_vertices_by_corrective_family": {},
                "top_vertices_weights_vs_trunk_proxy": [],
            }

        return {
            "schema_version": 1,
            "status": "READ_ONLY_SHOULDER_LAYER_DIAGNOSTIC",
            "candidate": "candidate.blend",
            "candidate_sha256": "a" * 64,
            "pose_definition_script": "pose.py",
            "pose_definition_script_sha256": "b" * 64,
            "flexion_driver_script_sha256": "c" * 64,
            "samples_per_pose": 3,
            "poses_requested": ["press_top"],
            "corrective_families": families,
            "scene_configs": {},
            "zone_contract": {
                "note": "fixture",
                "zone_vertex_counts": counts,
                "static_weight_ownership": ownership,
            },
            "poses": {"press_top": [row(0.0), row(0.5), row(1.0)]},
            "source_saved_or_modified": False,
        }

    def test_valid_fixture_passes(self):
        result = mod.validate(self.fixture())
        self.assertEqual(result["status"], "PASS")

    def test_missing_axilla_zone_fails(self):
        data = self.fixture()
        data["zone_contract"]["zone_vertex_counts"].pop("l_anterior_axilla")
        with self.assertRaisesRegex(ValueError, "required diagnostic zones missing"):
            mod.validate(data)

    def test_large_decomposition_residual_fails(self):
        data = self.fixture()
        data["poses"]["press_top"][1]["linear_decomposition_residual_max_m"] = 0.001
        with self.assertRaisesRegex(ValueError, "residual too large"):
            mod.validate(data)

    def test_source_must_be_read_only(self):
        data = self.fixture()
        data["source_saved_or_modified"] = True
        with self.assertRaisesRegex(ValueError, "source_saved_or_modified=false"):
            mod.validate(data)

    def test_pose_arc_must_include_zero_and_one(self):
        data = self.fixture()
        data["poses"]["press_top"][0]["fraction"] = 0.1
        with self.assertRaisesRegex(ValueError, "arc endpoints missing"):
            mod.validate(data)


if __name__ == "__main__":
    unittest.main()
