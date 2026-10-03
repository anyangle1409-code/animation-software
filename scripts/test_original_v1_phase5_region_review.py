"""Phase 5 regional capture plan matches anatomy execution coverage."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import original_v1_phase5_region_review as r

class Phase5RegionReviewTests(unittest.TestCase):
    def test_capture_plan_matches_every_region_required_view(self):
        plan=r.load_capture_plan(r.ROOT)
        self.assertEqual(set(plan["regions"]),{"5A","5B","5C","5D","5E","5F","5G"})
        self.assertTrue(all(plan["regions"][k]["captures"] for k in plan["regions"]))

    def test_capture_ids_are_unique_per_region(self):
        plan=r.load_capture_plan(r.ROOT)
        for region,row in plan["regions"].items():
            ids=[x["id"] for x in row["captures"]]
            self.assertEqual(len(ids),len(set(ids)),region)

    def test_exact_capture_metadata_contract(self):
        plan=r.load_capture_plan(r.ROOT)
        row=next(x for x in plan["regions"]["5D"]["captures"] if x["id"]=="palm_right")
        meta=r.expected_capture_metadata(plan,"5D",row)
        self.assertEqual(meta["camera"],row["camera"])
        self.assertEqual(meta["renderer"],"BLENDER_WORKBENCH")
        self.assertEqual(meta["resolution"],[900,900,100])
        self.assertFalse(meta["dressed"])
        self.assertFalse(meta["whole_body"])

    def source_fixture(self, root):
        row={
            "id":"palm_left",
            "pose":"neutral",
            "camera":{"mode":"hand_surface","side":"l","surface":"palm","oblique":False,
                      "anchors":[["hand_l","head"],["hand_l","tail"]],"orthographic_scale":0.24},
            "whole_body":False,"show_floor":False,"show_equipment":False,
        }
        plan={"renderer":"BLENDER_WORKBENCH","resolution":[900,900,100],
              "regions":{"5D":{"captures":[row]}}}
        (root/"scripts").mkdir()
        (root/r.CAPTURE_PLAN).write_text(json.dumps({"fixture":True}),encoding="utf-8")
        (root/r.CAPTURE_SCRIPT).write_text("capture fixture",encoding="utf-8")
        (root/r.POSE_SCRIPT).write_text("pose fixture",encoding="utf-8")
        candidate_sha="c"*64
        data={
            "schema_version":1,"status":"PHASE5_REGION_CAPTURE_COMPLETE","region":"5D",
            "candidate_sha256":candidate_sha,"production_approved":False,"phase_complete":False,
            "capture_plan_sha256":r.digest(root/r.CAPTURE_PLAN),
            "render_script_sha256":r.digest(root/r.CAPTURE_SCRIPT),
            "pose_definition_sha256":r.digest(root/r.POSE_SCRIPT),
            "blender_version":"fixture",
            "images":[{"capture_id":"palm_left","file":"phase5_5D_palm_left.png","sha256":"d"*64,
                       "capture":r.expected_capture_metadata(plan,"5D",row)}],
        }
        path=root/"source.json";path.write_text(json.dumps(data),encoding="utf-8")
        return plan,candidate_sha,path,data

    def test_source_manifest_exact_contract_accepts_matching_fixture(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);plan,sha,path,_=self.source_fixture(root)
            self.assertEqual(r.verify_source_metadata(root,path,"5D",sha,plan)["candidate_sha256"],sha)

    def test_source_manifest_rejects_camera_drift(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);plan,sha,path,data=self.source_fixture(root)
            data=copy.deepcopy(data)
            data["images"][0]["capture"]["camera"]["orthographic_scale"]=0.25
            path.write_text(json.dumps(data),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"metadata differs"):
                r.verify_source_metadata(root,path,"5D",sha,plan)

    def test_source_manifest_rejects_capture_script_drift(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);plan,sha,path,data=self.source_fixture(root)
            data["render_script_sha256"]="e"*64
            path.write_text(json.dumps(data),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"capture script identity differs"):
                r.verify_source_metadata(root,path,"5D",sha,plan)

    def test_source_manifest_rejects_pose_definition_drift(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);plan,sha,path,data=self.source_fixture(root)
            data["pose_definition_sha256"]="f"*64
            path.write_text(json.dumps(data),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"pose-definition identity differs"):
                r.verify_source_metadata(root,path,"5D",sha,plan)

    def test_high_detail_views_missing_from_generic_board_are_explicit(self):
        plan=r.load_capture_plan(r.ROOT)
        self.assertIn("wrist_close",{x["id"] for x in plan["regions"]["5C"]["captures"]})
        hands={x["id"] for x in plan["regions"]["5D"]["captures"]}
        self.assertTrue({"palm_left","palm_right","dorsal_left","dorsal_right"}.issubset(hands))
        self.assertIn("neutral_sole",{x["id"] for x in plan["regions"]["5F"]["captures"]})

if __name__=="__main__":
    unittest.main()
