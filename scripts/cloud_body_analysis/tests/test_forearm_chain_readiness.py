import copy
import json
import math
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "cloud_body_analysis"))

import forearm_chain_readiness as mod


def bone(name, parent, head, tail, *, mode="XYZ"):
    return {
        "name": name,
        "parent": parent,
        "rest_head_body_local_m": head,
        "rest_tail_body_local_m": tail,
        "rest_local_X_Y_Z_unit_in_body_coordinates": [
            [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]
        ],
        "axis_noncircularity_dot_max": 0.0,
        "roll_radians_stored": None,
        "use_deform": True,
        "connected_to_parent": False,
        "pose_rotation_mode": mode,
        "pose_constraint_metadata": [],
    }


def model_doc(model):
    bones = [bone("root", None, [0, 0, 0], [0, 0, 1])]
    for suffix, x in (("l", -0.2), ("r", 0.2)):
        bones += [
            bone(f"scapula_{suffix}", "root", [x, 0, 1.5], [x, 0, 1.4]),
            bone(f"upperarm_{suffix}", f"scapula_{suffix}", [x, 0, 1.4], [x, 0, 1.1]),
            bone(f"forearm_{suffix}", f"upperarm_{suffix}", [x, 0, 1.1], [x, 0, 0.8]),
            bone(f"forearm_tw0_{suffix}", f"forearm_{suffix}", [x, 0, 1.1], [x, 0, 0.8], mode="QUATERNION"),
            bone(f"forearm_tw1_{suffix}", f"forearm_{suffix}", [x, 0, 0.8], [x, 0, 0.5], mode="QUATERNION"),
            bone(f"hand_{suffix}", f"forearm_{suffix}", [x, 0, 0.5], [x, 0, 0.4]),
        ]
    return {"model": model, "bones": bones}


class ForearmChainReadinessTests(unittest.TestCase):
    def docs(self):
        return {m: model_doc(m) for m in mod.MODELS}

    def test_reports_single_forearm_chain_without_radius_ulna_approval(self):
        report = mod.audit_loaded(self.docs(), {m: "a" * 64 for m in mod.MODELS})
        self.assertEqual(report["status"], "BLOCKED_NO_INDEPENDENT_RADIUS_ULNA_CONTROL_EVIDENCE")
        self.assertFalse(report["separate_radius_ulna_skeletal_controls_observed"])
        self.assertFalse(report["forearm_pronation_supination_tested"])
        for model in mod.MODELS:
            for side in ("l", "r"):
                row = report["models"][model]["authored_suffix_chains"][side]
                self.assertEqual(row["hand_parent"], f"forearm_{side}")
                self.assertEqual(row["twist_helpers"], [f"forearm_tw0_{side}", f"forearm_tw1_{side}"])
                self.assertFalse(row["radius_ulna_anatomical_binding_verified"])

    def test_rejects_changed_hand_parent_or_twist_hierarchy(self):
        for name, parent in (("hand_l", "forearm_tw1_l"), ("forearm_tw0_l", "upperarm_l")):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "chain"):
                docs = self.docs()
                next(b for b in docs["W8"]["bones"] if b["name"] == name)["parent"] = parent
                mod.audit_loaded(docs, {m: "a" * 64 for m in mod.MODELS})

    def test_rejects_missing_or_duplicate_required_controls(self):
        docs = self.docs()
        docs["V14"]["bones"] = [b for b in docs["V14"]["bones"] if b["name"] != "forearm_tw1_r"]
        with self.assertRaisesRegex(ValueError, "required"):
            mod.audit_loaded(docs, {m: "a" * 64 for m in mod.MODELS})
        docs = self.docs()
        docs["R120"]["bones"].append(copy.deepcopy(docs["R120"]["bones"][-1]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            mod.audit_loaded(docs, {m: "a" * 64 for m in mod.MODELS})

    def test_rejects_nonfinite_coordinates_or_constraints(self):
        docs = self.docs()
        next(b for b in docs["W8"]["bones"] if b["name"] == "forearm_l")["rest_head_body_local_m"][0] = math.nan
        with self.assertRaisesRegex(ValueError, "finite"):
            mod.audit_loaded(docs, {m: "a" * 64 for m in mod.MODELS})
        docs = self.docs()
        next(b for b in docs["W8"]["bones"] if b["name"] == "forearm_tw0_l")["pose_constraint_metadata"] = [{"type": "COPY_ROTATION"}]
        with self.assertRaisesRegex(ValueError, "constraint"):
            mod.audit_loaded(docs, {m: "a" * 64 for m in mod.MODELS})

    def test_rejects_radius_ulna_named_controls_instead_of_false_not_observed(self):
        for name in ("radius.L", "ulna-r"):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "radius/ulna"):
                docs = self.docs()
                docs["W8"]["bones"].append(bone(name, "forearm_l", [0, 0, 1], [0, 0, 0]))
                mod.audit_loaded(docs, {m: "a" * 64 for m in mod.MODELS})

    def test_rejects_helper_semantic_or_cross_model_drift(self):
        mutations = (
            ("forearm_tw0_l", "use_deform", False),
            ("forearm_tw1_l", "pose_rotation_mode", "XYZ"),
            ("forearm_l", "rest_tail_body_local_m", [0.0, 0.0, 0.7]),
        )
        for name, field, value in mutations:
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "helper|cross-model"):
                docs = self.docs()
                next(b for b in docs["V14"]["bones"] if b["name"] == name)[field] = value
                mod.audit_loaded(docs, {m: "a" * 64 for m in mod.MODELS})
        docs = self.docs()
        docs["R120"]["bones"].append(bone("forearm_tw2_l", "forearm_l", [0, 0, 1], [0, 0, 0], mode="QUATERNION"))
        with self.assertRaisesRegex(ValueError, "helper"):
            mod.audit_loaded(docs, {m: "a" * 64 for m in mod.MODELS})

    def test_requires_valid_sha256_input_hashes(self):
        hashes = {"W8": "a" * 64, "V14": "b" * 64, "R120": "not-a-hash"}
        with self.assertRaisesRegex(ValueError, "SHA256"):
            mod.audit_loaded(self.docs(), hashes)

    def test_audit_hashes_and_parses_each_member_from_one_read(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for model in mod.MODELS:
                target = root / model / "rig_rest_axes_metadata.json"
                target.parent.mkdir()
                doc = model_doc(model)
                doc.update({
                    "source_sha256": mod.EXPECTED[model],
                    "original_source_unchanged": True,
                    "status": "BLENDER_LOCAL_BONE_AXIS_INVENTORY_ONLY_ANATOMICAL_MAPPING_NOT_APPROVED",
                    "bone_count": len(doc["bones"]),
                    "body_modifier_metadata": [],
                })
                for key in mod.NOT_GRANTED:
                    doc[key] = False
                target.write_text(json.dumps(doc))
            original = Path.read_bytes
            reads = []
            def tracked(path):
                reads.append(str(path))
                return original(path)
            with mock.patch.object(Path, "read_bytes", tracked):
                report = mod.audit(root)
            self.assertEqual(len(reads), 3)
            self.assertEqual(report["status"], "BLOCKED_NO_INDEPENDENT_RADIUS_ULNA_CONTROL_EVIDENCE")

    def test_writer_rejects_input_tree_and_aliases_and_writes_atomically(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence = root / "evidence"
            evidence.mkdir()
            member = evidence / "rig.json"
            member.write_text("evidence")
            report = mod.audit_loaded(self.docs(), {m: "a" * 64 for m in mod.MODELS})
            for out in (evidence, root / "alias"):
                if out.name == "alias":
                    out.mkdir()
                    (out / mod.JSON_NAME).hardlink_to(member)
                with self.subTest(out=out), self.assertRaisesRegex(ValueError, "evidence|alias"):
                    mod.write_report(report, out, [evidence])
            out = root / "safe"
            mod.write_report(report, out, [evidence])
            self.assertEqual(json.loads((out / mod.JSON_NAME).read_text()), report)
            self.assertIn("BLOCKED", (out / mod.MD_NAME).read_text())


if __name__ == "__main__":
    unittest.main()
