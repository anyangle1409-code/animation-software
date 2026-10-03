"""Bare/dressed underlying-body equivalence verifier tests."""
from __future__ import annotations
import copy
import unittest

import original_v1_bare_dressed_equivalence as e


class BareDressedEquivalenceTests(unittest.TestCase):
    def fixture(self):
        rows=[]
        for pose in sorted(e.POSES):
            common={"vertex_count":100,"face_count":200,"vertex_sha256_round9":"a"*64,
                    "pose_state_sha256":"b"*64,"metrics_sha256":"c"*64}
            rows.append({"pose":pose,"status":"IDENTICAL","body_mask":{"present":True,"active_in_either_state":False},
                         "bare":copy.deepcopy(common),"dressed_presence":copy.deepcopy(common),
                         "max_vertex_delta_mm":0.0,"mean_vertex_delta_mm":0.0,"changed_vertex_count_exact_float":0})
        locked=e.load_locked_rig(e.ROOT)
        report={"schema_version":1,"status":"EVIDENCE_ONLY","phase_complete":False,"production_approved":False,
                "candidate_revision":"r40","candidate":"x.blend","candidate_sha256":"d"*64,
                "rig_id":locked["identity"],"rig_revision":locked["revision"],
                "rig_structure_sha256":locked["rig_structure_sha256"],
                "rig_bone_count":locked["bone_count"],"rig_deform_bone_count":locked["deform_bone_count"],
                "rig_lock":locked["lock"],"rig_payload":locked["payload"],
                "pose_count":len(rows),"poses":rows}
        manifest={"candidate":"x.blend","candidate_sha256":"d"*64}
        return report,manifest

    def test_identical_fixture_passes_identity_contract(self):
        report,manifest=self.fixture();result=e.verify(report,manifest)
        self.assertEqual(result["equivalence_status"],"IDENTICAL_UNDER_GARMENT_PRESENCE")
        self.assertFalse(result["phase_complete"])

    def test_stale_63_bone_rig_receipt_is_refused(self):
        report,manifest=self.fixture();report["rig_bone_count"]=63
        with self.assertRaisesRegex(ValueError,"locked rev2c rig identity differs"):
            e.verify(report,manifest)

    def test_vertex_hash_difference_blocks(self):
        report,manifest=self.fixture();report["poses"][0]["dressed_presence"]["vertex_sha256_round9"]="f"*64
        result=e.verify(report,manifest)
        self.assertEqual(result["equivalence_status"],"BLOCKED")

    def test_body_mask_active_blocks(self):
        report,manifest=self.fixture();report["poses"][0]["body_mask"]["active_in_either_state"]=True
        result=e.verify(report,manifest)
        self.assertTrue(any("hide-mask" in x for x in result["blockers"]))

    def test_nonzero_delta_blocks(self):
        report,manifest=self.fixture();report["poses"][0]["max_vertex_delta_mm"]=0.001
        result=e.verify(report,manifest)
        self.assertTrue(any("nonzero" in x for x in result["blockers"]))


if __name__=="__main__":
    unittest.main()
