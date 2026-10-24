"""Synthetic, Blender-free guards for read-only W8 pinned edge endpoint metadata."""
import ast
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "phone_blender"))
import elbow_edge_endpoint_audit as audit


def make_body():
    def v(x, y, groups):
        return NS(co=(x, y, 0), groups=[NS(group=g, weight=w) for g, w in groups])
    vertices = [
        v(0, 0, [(0, .8), (1, .2)]),
        v(1, 0, [(0, .5), (1, .5)]),
        v(0, 1, [(0, .8), (1, .2)]),
        v(1, 1, [(0, .2), (1, .8)]),
    ]
    def key(name, positions, relative=None):
        return NS(name=name, data=[NS(co=p) for p in positions],
                  relative_key=relative, value=0.0)
    basis = key("Basis", [v.co for v in vertices])
    deformation = key("TestKey", [(0, 0, 0), (1.5, 0, 0), (0, 1, 0), (1, 1, 0)], basis)
    mesh = NS(vertices=vertices, loop_triangles=[NS(vertices=(0, 1, 2)),
                                                 NS(vertices=(1, 3, 2))],
              shape_keys=NS(key_blocks=[basis, deformation]))
    body = NS(name="synthetic_body", data=mesh,
              vertex_groups=[NS(index=0, name="groupA"), NS(index=1, name="groupB")])
    return body


TARGETS = (("edge_a", (0, 1), 0, .2), ("edge_b", (1, 3), 6, 2.5))


class PinnedEdgeEndpointTests(unittest.TestCase):
    def run_audit(self, body=None, targets=TARGETS):
        return audit.analyze(body or make_body(), audit.W8_SHA256, targets)

    def test_known_provenance_and_pinned_ids(self):
        self.assertEqual(len(audit.TARGETS), 4)
        self.assertEqual(audit.TARGETS[0][1], (15645, 53019))
        self.assertEqual(audit.TARGETS[3][1], (32352, 71428))
        self.assertEqual(len(audit.W8_SHA256), 64)

    def test_synthetic_weights_and_shape_geometry(self):
        report = self.run_audit()
        self.assertEqual(report["target_edge_count"], 2)
        self.assertEqual(report["edges"][0]["rest_edge_length_mm"], 1000.)
        self.assertAlmostEqual(report["edges"][0]["group_weight_L1_difference_not_tissue_strain"], .6)
        self.assertEqual(report["edges"][0]["shared_positive_weight_group_count"], 2)
        self.assertEqual(report["edges"][0]["top_stored_shape_keys_by_absolute_edge_ratio_change"][0]
                         ["stored_edge_length_ratio_to_Basis"], 1.5)
        self.assertEqual(report["edges"][0]["endpoints"][0]["group_weights_descending"][0]["group"], "groupA")
        self.assertFalse(report["skin_deformation_validated"])
        self.assertFalse(report["joint_axes_ISB_calibrated"])

    def test_reject_wrong_source(self):
        with self.assertRaises(ValueError):
            audit.analyze(make_body(), "0" * 64, TARGETS)

    def test_reject_missing_triangle_edge(self):
        body = make_body()
        body.data.loop_triangles = [NS(vertices=(0, 1, 2))]
        with self.assertRaises(ValueError):
            self.run_audit(body)

    def test_reject_invalid_weights(self):
        for value in (-.2, float("nan")):
            body = make_body()
            body.data.vertices[0].groups[0].weight = value
            with self.assertRaises(ValueError):
                self.run_audit(body)

    def test_reject_unweighted_endpoint(self):
        body = make_body()
        body.data.vertices[0].groups = []
        with self.assertRaises(ValueError):
            self.run_audit(body)

    def test_reject_shape_key_mismatch(self):
        body = make_body()
        body.data.shape_keys.key_blocks[1].data.pop()
        with self.assertRaises(ValueError):
            self.run_audit(body)

    def test_reject_duplicate_and_invalid_edges(self):
        for targets in (
            (("same", (0, 0), 0, 1.),),
            (("outside", (0, 9), 0, 1.),),
            (("bad", (0, 1), 0, float("inf")),),
            (("same", (0, 1), 0, 1.), ("same", (1, 3), 6, 1.)),
        ):
            with self.subTest(targets=targets):
                with self.assertRaises(ValueError):
                    self.run_audit(targets=targets)

    def test_rest_translation_invariance_of_length_and_weights(self):
        a = self.run_audit()
        body = make_body()
        for v in body.data.vertices:
            v.co = (v.co[0] + 2, v.co[1] - 4, v.co[2] + 1)
        b = self.run_audit(body)
        for x, y in zip(a["edges"], b["edges"]):
            self.assertEqual(x["rest_edge_length_mm"], y["rest_edge_length_mm"])
            self.assertEqual(x["group_weight_L1_difference_not_tissue_strain"],
                             y["group_weight_L1_difference_not_tissue_strain"])

    def test_report_explicitly_refuses_anatomy_approval(self):
        report = self.run_audit()
        self.assertIn("ANATOMY AND SKIN NOT APPROVED", audit.markdown(report))
        for key in ("anatomical_side_verified", "joint_axes_ISB_calibrated",
                    "muscle_attachment_approved", "skin_deformation_validated"):
            self.assertIs(report[key], False)

    def test_no_bpy_or_model_write_operations(self):
        tree = ast.parse((ROOT / "phone_blender" / "elbow_edge_endpoint_audit.py").read_text())
        imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
        self.assertFalse(any(x.name == "bpy" for n in imports for x in n.names))
        forbidden = {"save_mainfile", "save_as_mainfile", "mode_set", "transform_apply"}
        self.assertFalse(any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                             and n.func.attr in forbidden for n in ast.walk(tree)))


if __name__ == "__main__":
    unittest.main()
