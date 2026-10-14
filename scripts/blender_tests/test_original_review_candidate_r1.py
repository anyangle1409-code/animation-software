"""Native checks of the ORIGINAL_v1 consolidated review candidate R1, re-measured from the saved blends (review only)."""
import hashlib
import json
import math
import sys
import unittest
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

CAND = ROOT / "ORIGINAL_V1_WORK/anatomy/candidates"
C5 = CAND / "claude_foot_20261013/c5/HGPT_ORIGINAL_V1_FOOT_C5_CLAUDE.blend"
R1 = CAND / "claude_review_r1_20261014/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R1_CLAUDE.blend"
REPORT = CAND / "claude_review_r1_20261014/r1_build.json"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def scene(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    import build_functional_shoulder_correction_blender as correction
    res = correction.build_corrected_scene()
    for kb in res["body"].data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    return correction, res


def evaluated(body):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    me = ev.to_mesh()
    out = [body.matrix_world @ v.co for v in me.vertices]
    ev.to_mesh_clear()
    return out


class ReviewCandidateR1NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_text())
        bpy.ops.wm.open_mainfile(filepath=str(C5))
        body = [o for o in bpy.data.objects if o.type == "MESH" and o.data.shape_keys
                and o.find_armature() is not None][0]
        cls.c5_name = body.name
        cls.c5_basis = [v.co.copy() for v in body.data.vertices]
        cls.c5_faces = [tuple(p.vertices) for p in body.data.polygons]
        bpy.ops.wm.open_mainfile(filepath=str(R1))
        cls.saved_body = bpy.data.objects[cls.c5_name]
        cls.saved_rig = cls.saved_body.find_armature()
        cls.saved = {
            "deform": sum(b.use_deform for b in cls.saved_rig.data.bones),
            "helper_bones": [b.name for b in cls.saved_rig.data.bones if b.name.startswith("deltoid_helper")],
            "groups": sorted(g.name for g in cls.saved_body.vertex_groups if g.name.startswith("deltoid_helper")),
            "refs": {s: list(cls.saved_rig.get(f"hgpt_w3a_ref_{s}", [])) for s in ("l", "r")},
            "k1": sorted(kb.name for kb in cls.saved_body.data.shape_keys.key_blocks if kb.name.startswith("HGPT_K1_")),
            "approved": bpy.context.scene.get("hgpt_review_candidate_approved"),
            "basis": [v.co.copy() for v in cls.saved_body.data.vertices],
            "faces": [tuple(p.vertices) for p in cls.saved_body.data.polygons],
        }

    def test_identity_and_build_verdict(self):
        self.assertEqual(sha(C5), self.report["parent"]["sha256"])
        self.assertEqual(sha(R1), self.report["output"]["sha256"])
        self.assertEqual(self.report["checks"]["verdict"], "PASS")
        self.assertEqual(self.report["status"], "REVIEW_CANDIDATE_NOT_ACCEPTED")

    def test_saved_file_is_a_67_joint_rig_with_helper_data(self):
        self.assertEqual(self.saved["deform"], 67)
        self.assertEqual(self.saved["helper_bones"], [])
        self.assertEqual(self.saved["groups"], ["deltoid_helper_l", "deltoid_helper_r"])
        for s in ("l", "r"):
            self.assertEqual(len(self.saved["refs"][s]), 3, s)
        self.assertEqual(len(self.saved["k1"]), 10)
        self.assertFalse(any("ELBOW" in k and k.endswith(("_120", "_140")) for k in self.saved["k1"]))
        self.assertIs(self.saved["approved"], False)

    def test_rest_mesh_is_c5(self):
        self.assertEqual(self.saved["faces"], self.c5_faces)
        self.assertLess(max((a - b).length for a, b in zip(self.saved["basis"], self.c5_basis)), 1e-7)

    def test_drives_are_identity_at_rest(self):
        import original_v1_review_candidate_drives as drives
        _, res = scene(R1)
        rig, body = res["runtime"], res["body"]
        V0 = evaluated(body)
        drives.drive(rig, body)
        self.assertEqual(sum(b.use_deform for b in rig.data.bones), 69)
        for s in ("l", "r"):
            self.assertLess(rig.pose.bones[f"deltoid_helper_{s}"].rotation_quaternion.angle, 1e-5, s)
        self.assertTrue(all(kb.value == 0.0 for kb in body.data.shape_keys.key_blocks if kb.name.startswith("HGPT_K1_")))
        self.assertLess(max((a - b).length for a, b in zip(V0, evaluated(body))), 1e-6)

    def test_helper_takes_half_the_arm_rotation_without_flips(self):
        import original_v1_review_candidate_drives as drives
        correction, res = scene(R1)
        rig, body = res["runtime"], res["body"]
        drives.install_helpers(rig)
        prev, track = None, {s: Vector() for s in ("l", "r")}
        for ht in range(0, 161, 5):
            correction.apply_corrected_pose(res, ht)
            drives.drive(rig, body)
            ang = {}
            for s in ("l", "r"):
                # independent stateful reference: the arm's rotation vector tracked continuously through the sweep
                q = drives._rel_quat(rig, f"upperarm_{s}", f"scapula_{s}")
                if q.w < 0:
                    q.negate()
                n = q.axis if q.angle > 1e-9 else Vector((1.0, 0.0, 0.0))
                track[s] = min((n * q.angle, n * (q.angle - 2 * math.pi)), key=lambda c: (c - track[s]).length)
                ang[s] = rig.pose.bones[f"deltoid_helper_{s}"].rotation_quaternion.angle
                self.assertLess(abs(ang[s] - drives.FRACTION * track[s].length), 1e-4, (ht, s))
            self.assertLess(abs(ang["l"] - ang["r"]), 1e-4, ht)          # bilateral symmetry
            if prev is not None:
                self.assertLess(abs(ang["r"] - prev), math.radians(8.0), ht)    # continuous: no branch flip
            prev = ang["r"]

    def test_k1_keys_follow_the_hinge(self):
        import build_original_knee_contact_corrective_blender as k1
        import original_v1_review_candidate_drives as drives
        _, res = scene(R1)
        rig, body = res["runtime"], res["body"]
        keys = body.data.shape_keys.key_blocks
        k1._pose_pure(rig, "knee", 110)
        drives.drive(rig, body)
        for s in ("l", "r"):
            self.assertAlmostEqual(keys[f"HGPT_K1_KNEE_{s}_110"].value, 1.0, places=2)
            self.assertAlmostEqual(keys[f"HGPT_K1_KNEE_{s}_90"].value, 0.0, places=2)
        k1._pose_pure(rig, "elbow", 100)
        drives.drive(rig, body)
        for s in ("l", "r"):
            self.assertAlmostEqual(keys[f"HGPT_K1_ELBOW_{s}_90"].value + keys[f"HGPT_K1_ELBOW_{s}_110"].value, 1.0,
                                   places=2)


if __name__ == "__main__":
    unittest.main(argv=[__file__])
