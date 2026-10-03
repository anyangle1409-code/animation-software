"""Shared rev2c locked-rig identity remains exact and fail-closed."""
from __future__ import annotations
import types
import unittest

import original_v1_locked_rig as r


class LockedRigTests(unittest.TestCase):
    def fake_armature(self, contract):
        by_name={}
        for row in contract["bones"]:
            bone=types.SimpleNamespace(name=row["name"],parent=None,use_deform=True)
            by_name[row["name"]]=bone
        for row in contract["bones"]:
            if row["parent"] is not None:
                by_name[row["name"]].parent=by_name[row["parent"]]
        # Lock declares 66 deform of 67. The helper tests count semantics; Blender
        # capture proves the real per-bone flags when run on the candidate.
        by_name[contract["bones"][0]["name"]].use_deform=False
        return types.SimpleNamespace(
            name=contract["object_name"],
            type="ARMATURE",
            data=types.SimpleNamespace(bones=list(by_name.values())),
        )

    def test_committed_lock_and_payload_agree(self):
        contract=r.load_locked_rig(r.ROOT)
        self.assertEqual(contract["identity"],"hgpt_canonical_v4_original")
        self.assertEqual(contract["revision"],"rev2_forearm_twist_only")
        self.assertEqual(contract["bone_count"],67)
        self.assertEqual(contract["deform_bone_count"],66)
        self.assertEqual(len(contract["bones"]),67)

    def test_matching_armature_has_no_identity_issues(self):
        contract=r.load_locked_rig(r.ROOT)
        self.assertEqual(r.blender_armature_issues(self.fake_armature(contract),contract),[])

    def test_stale_63_bone_armature_is_refused(self):
        contract=r.load_locked_rig(r.ROOT)
        armature=self.fake_armature(contract)
        armature.data.bones=armature.data.bones[:63]
        self.assertTrue(any("bone count differs" in x for x in r.blender_armature_issues(armature,contract)))

    def test_parent_drift_is_refused(self):
        contract=r.load_locked_rig(r.ROOT)
        armature=self.fake_armature(contract)
        target=next(b for b in armature.data.bones if b.parent is not None)
        target.parent=None
        self.assertIn("locked rev2c bone hierarchy differs",r.blender_armature_issues(armature,contract))


    def test_live_later_phase_scripts_do_not_reintroduce_63_bone_guard(self):
        live=[
            "scripts/original_v1_garment_evidence.py",
            "scripts/audit_original_v1_changes.py",
            "scripts/capture_original_v1_dressed_evidence_blender.py",
            "scripts/capture_original_v1_dressed_range_blender.py",
        ]
        for rel in live:
            with self.subTest(rel=rel):
                text=(r.ROOT/rel).read_text(encoding="utf-8")
                self.assertNotIn("canonical 63-bone rig required",text)
                self.assertNotIn("len(rig.data.bones) != 63",text)
                self.assertIn("original_v1_locked_rig",text)



if __name__=="__main__":
    unittest.main()
