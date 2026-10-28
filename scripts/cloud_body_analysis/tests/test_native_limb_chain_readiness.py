import copy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "cloud_body_analysis"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import native_limb_chain_readiness as mod
from test_forearm_chain_readiness import bone


def model_doc(model):
    bones = [
        bone("root", None, [0, 0, 0], [0, 0, 1]),
        bone("pelvis", "root", [0, 0, 1], [0, 0, 1.1]),
        bone("spine_03", "pelvis", [0, 0, 1.1], [0, 0, 1.5], mode="QUATERNION"),
    ]
    for suffix, x in (("l", -0.2), ("r", 0.2)):
        bones += [
            bone(f"clavicle_{suffix}", "spine_03", [0, 0, 1.5], [x, 0, 1.5], mode="QUATERNION"),
            bone(f"scapula_{suffix}", f"clavicle_{suffix}", [x, 0, 1.5], [x, 0, 1.4], mode="QUATERNION"),
            bone(f"upperarm_{suffix}", f"scapula_{suffix}", [x, 0, 1.4], [x, 0, 1.1]),
            bone(f"shoulder_cap_{suffix}", f"scapula_{suffix}", [x, 0, 1.4], [x, 0, 1.3], mode="QUATERNION"),
            bone(f"thigh_{suffix}", "pelvis", [x, 0, 1], [x, 0, 0.6], mode="QUATERNION"),
            bone(f"shin_{suffix}", f"thigh_{suffix}", [x, 0, 0.6], [x, 0, 0.2], mode="QUATERNION"),
            bone(f"foot_{suffix}", f"shin_{suffix}", [x, 0, 0.2], [x, -0.2, 0.1], mode="QUATERNION"),
            bone(f"toe_{suffix}", f"foot_{suffix}", [x, -0.2, 0.1], [x, -0.3, 0.1], mode="QUATERNION"),
            bone(f"hip_crease_{suffix}", "pelvis", [x, 0, 1], [x, 0, 0.9], mode="QUATERNION"),
        ]
    return {"model": model, "bones": bones}


class NativeLimbChainReadinessTests(unittest.TestCase):
    def docs(self):
        return {m: model_doc(m) for m in mod.MODELS}

    def hashes(self):
        return {m: ("abc" + str(i)) * 16 for i, m in enumerate(mod.MODELS)}

    def test_reports_authored_shoulder_and_lower_chains_without_anatomy_claims(self):
        report = mod.audit_loaded(self.docs(), self.hashes())
        self.assertEqual(report["status"], "AUTHORED_LIMB_CHAINS_PRESENT_ANATOMICAL_FRAMES_AND_COUPLING_BLOCKED")
        self.assertTrue(report["all_three_selected_chains_identical"])
        self.assertFalse(report["scapulohumeral_coordination_tested"])
        self.assertFalse(report["ground_contact_tested"])
        self.assertFalse(report["separately_named_patella_or_internal_foot_controls_observed"])
        self.assertNotIn("multisegment_foot_controls_observed", report)
        for model in mod.MODELS:
            self.assertEqual(report["models"][model]["suffix_chains"]["l"]["shoulder"],
                             ["spine_03", "clavicle_l", "scapula_l", "upperarm_l"])
            self.assertEqual(report["models"][model]["suffix_chains"]["r"]["lower_limb"],
                             ["pelvis", "thigh_r", "shin_r", "foot_r", "toe_r"])
            row = report["models"][model]["suffix_chains"]["l"]
            self.assertEqual(row["shoulder_cap_authored_control"], "shoulder_cap_l")
            self.assertEqual(row["hip_crease_authored_control"], "hip_crease_l")
            self.assertNotIn("shoulder_cap_helper", row)

    def test_rejects_parent_drift_in_each_chain(self):
        for name, parent in (("scapula_l", "spine_03"), ("upperarm_l", "clavicle_l"),
                             ("shin_r", "pelvis"), ("toe_r", "shin_r"),
                             ("shoulder_cap_l", "clavicle_l"), ("hip_crease_r", "thigh_r")):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "hierarchy"):
                docs = self.docs()
                next(b for b in docs["W8"]["bones"] if b["name"] == name)["parent"] = parent
                mod.audit_loaded(docs, self.hashes())

    def test_rejects_missing_or_duplicate_controls(self):
        docs = self.docs()
        docs["V14"]["bones"] = [b for b in docs["V14"]["bones"] if b["name"] != "toe_l"]
        with self.assertRaisesRegex(ValueError, "missing"):
            mod.audit_loaded(docs, self.hashes())
        docs = self.docs()
        docs["R120"]["bones"].append(copy.deepcopy(docs["R120"]["bones"][-1]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            mod.audit_loaded(docs, self.hashes())

    def test_rejects_named_segment_controls_that_contradict_absence_inventory(self):
        for name in ("patella.L", "hindfoot-r", "midfoot_l", "forefoot.r",
                     "leftPatella", "patellaBone", "hindfootControl"):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "segment-named"):
                docs = self.docs()
                docs["W8"]["bones"].append(bone(name, "foot_l", [0, 0, 0], [0, 0, 1]))
                mod.audit_loaded(docs, self.hashes())

    def test_rejects_cross_model_coordinate_or_mode_drift(self):
        for field, value in (("rest_tail_body_local_m", [0, 0, 9]), ("pose_rotation_mode", "XYZ")):
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "cross-model"):
                docs = self.docs()
                next(b for b in docs["V14"]["bones"] if b["name"] == "scapula_l")[field] = value
                mod.audit_loaded(docs, self.hashes())

    def test_rejects_invalid_hashes(self):
        hashes = self.hashes()
        hashes["W8"] = "bad"
        with self.assertRaisesRegex(ValueError, "SHA256"):
            mod.audit_loaded(self.docs(), hashes)

    def test_writer_rejects_evidence_tree_and_alias(self):
        report = mod.audit_loaded(self.docs(), self.hashes())
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence = root / "evidence"
            evidence.mkdir()
            member = evidence / "member.json"
            member.write_text("evidence")
            with self.assertRaisesRegex(ValueError, "evidence"):
                mod.write_report(report, evidence, [evidence])
            out = root / "out"
            out.mkdir()
            (out / mod.JSON_NAME).hardlink_to(member)
            with self.assertRaisesRegex(ValueError, "alias"):
                mod.write_report(report, out, [evidence])


if __name__ == "__main__":
    unittest.main()
