"""Native checks of the ORIGINAL_v1 review candidate R11 = R10 with the shoulder/armpit region re-meshed (Loop subdivision,
edges ~20 -> ~9 mm; every weight and corrective key carried by the same stencils).  Review only; a different body vertex
count is a runtime-contract change."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

CAND = ROOT / "ORIGINAL_V1_WORK/anatomy/candidates"
R10 = CAND / "claude_review_r10_20261014/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R10_CLAUDE.blend"
R11 = CAND / "claude_review_r11_20261014/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R11_CLAUDE.blend"
REPORT = CAND / "claude_review_r11_20261014/r11_remesh.json"
VALIDATION = CAND / "claude_review_r11_20261014/r11_validation.json"
R10_VALIDATION = CAND / "claude_review_r10_20261014/r10_validation.json"
N_OLD = 17946


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
    rig = body.find_armature()
    names = {g.index: g.name for g in body.vertex_groups}
    edges = {}
    for p in body.data.polygons:
        vs = list(p.vertices)
        for i in range(len(vs)):
            e = tuple(sorted((vs[i], vs[(i + 1) % len(vs)])))
            edges[e] = edges.get(e, 0) + 1
    return {"co": [v.co.copy() for v in body.data.vertices],
            "keys": {kb.name: [d.co.copy() for d in kb.data] for kb in body.data.shape_keys.key_blocks[1:]},
            "groups": [g.name for g in body.vertex_groups],
            "wsum": [sum(g.weight for g in v.groups) for v in body.data.vertices],
            "edge_use": set(edges.values()), "tris": all(len(p.vertices) == 3 for p in body.data.polygons),
            "bones": {b.name: (b.head_local.copy(), b.tail_local.copy()) for b in rig.data.bones},
            "declared": bpy.context.scene.get("hgpt_review_body_vertices"),
            "approved": bpy.context.scene.get("hgpt_review_candidate_approved")}


class ReviewCandidateR11NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_text())
        cls.r10 = snapshot(R10)
        cls.r11 = snapshot(R11)

    def test_identity_and_declared_count(self):
        self.assertEqual(sha(R10), self.report["parent"]["sha256"])
        self.assertEqual(sha(R11), self.report["output"]["sha256"])
        self.assertIs(self.r11["approved"], False)
        self.assertEqual(self.r11["declared"], len(self.r11["co"]))
        self.assertEqual(len(self.r10["co"]), N_OLD)
        self.assertEqual(len(self.r11["co"]), self.report["remesh"]["vertices"])

    def test_watertight_triangle_mesh_rig_unchanged(self):
        self.assertTrue(self.r11["tris"])
        self.assertEqual(self.r11["edge_use"], {2})                       # every edge shared by exactly two faces
        self.assertEqual(self.r11["bones"].keys(), self.r10["bones"].keys())
        for n, (h, t) in self.r10["bones"].items():
            self.assertLess((h - self.r11["bones"][n][0]).length + (t - self.r11["bones"][n][1]).length, 1e-9, n)
        self.assertEqual(self.r11["groups"], self.r10["groups"])
        self.assertEqual(sorted(self.r11["keys"]), sorted(self.r10["keys"]))

    def test_shoulder_region_finer_and_rest_of_body_untouched(self):
        a = self.report["remesh"]
        self.assertLess(a["after"]["median_edge_mm"], 10.0)
        self.assertGreater(a["edge_stats_within_12cm_of_pivots_before"]["median_edge_mm"], 18.0)
        moved = [i for i in range(N_OLD) if (self.r10["co"][i] - self.r11["co"][i]).length > 1e-7]
        self.assertEqual(len(moved), a["repositioned_original_vertices"])  # only Loop-repositioned region vertices
        for name in self.r10["keys"]:                                      # keys equal outside the region, too
            k10, k11 = self.r10["keys"][name], self.r11["keys"][name]
            far = [i for i in range(0, N_OLD, 7) if i not in set(moved)]
            self.assertLess(max((k10[i] - k11[i]).length for i in far[:2000]), 1e-6, name)

    def test_weights_normalised(self):
        self.assertLess(max(abs(x - 1.0) for x in self.r11["wsum"]), 1e-3)

    def test_guard_accepts_only_the_declared_count(self):
        import original_v1_functional_fullbody as ff
        import original_v1_review_candidate_drives  # noqa: F401  (installs the declared-count wrapper)
        bpy.ops.wm.open_mainfile(filepath=str(R11))
        ok = ff.validate_inventory(set(), set(), len(self.r11["co"]))["errors"]
        self.assertFalse(any("vertex count" in e for e in ok), ok)
        errs = ff.validate_inventory(set(), set(), len(self.r11["co"]) + 1)["errors"]
        self.assertTrue(any("vertex count" in e for e in errs))

    def test_benchmarks_versus_r10(self):
        v1 = json.loads(R10_VALIDATION.read_text())["benchmarks"]
        v2 = json.loads(VALIDATION.read_text())["benchmarks"]
        self.assertEqual(sorted(v1), sorted(v2))
        for n in v1:
            a, b = v1[n]["r10_worst"], v2[n]["r11_worst"]
            self.assertLessEqual(b["self_intersecting_pairs"], a["self_intersecting_pairs"] + 2, n)   # (4x faces in region)
            self.assertLessEqual(b["collapse_lt_0_1"], a["collapse_lt_0_1"] + 2, n)
        self.assertEqual(v2["shoulder_press"]["r11_worst"]["self_intersecting_pairs"], 0)
        self.assertLess(v2["bent_over_row"]["r11_worst"]["self_intersecting_pairs"], v1["bent_over_row"]["r10_worst"]["self_intersecting_pairs"])


if __name__ == "__main__":
    unittest.main(argv=[__file__])
