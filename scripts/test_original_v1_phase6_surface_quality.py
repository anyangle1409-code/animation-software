"""Phase 6 surface-quality evidence stays fail-closed."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

import original_v1_phase6_surface_quality as s


class Phase6SurfaceQualityTests(unittest.TestCase):
    def template(self):
        return json.loads((s.ROOT / s.JOINT_TEMPLATE).read_text(encoding="utf-8"))

    def ref(self, root: Path, p: Path):
        return {"path": p.relative_to(root).as_posix(), "sha256": s.digest(p)}

    def fixture(self, root: Path):
        sha="a"*64
        for rel in (s.RAW_AUDIT,s.CHANGE_AUDIT,s.EVAL_CAPTURE):
            p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text("fixture "+rel,encoding="utf-8")
        raw={
            "status":"EVIDENCE_ONLY","phase_complete":False,"production_approved":False,
            "candidate_sha256":sha,"vertex_count":100,"face_count":200,
            "boundary_edges":[],"nonmanifold_edges":[],"winding_conflict_edges":[],
            "nonmanifold_vertex_ids":[],"isolated_vertex_ids":[],"repeated_vertex_face_ids":[],
            "duplicate_face_groups":[],"exact_zero_area_face_ids":[],"near_degenerate_face_ids":[],
            "zero_area_fan_face_ids":[],"coincident_coordinate_groups":[],
            "symmetry":{"full_vertex_coverage":True,"unmatched_face_ids":[]},
            "source_git_commit":"b"*40,
            "source_evidence":[
                {"path":s.RAW_AUDIT,"sha256":s.digest(root/s.RAW_AUDIT)},
                {"path":s.CHANGE_AUDIT,"sha256":s.digest(root/s.CHANGE_AUDIT)}
            ]
        }
        evaluated={
            "status":"EVIDENCE_ONLY","phase_complete":False,"production_approved":False,
            "candidate_sha256":sha,
            "evaluated":{"vertex_count":100,"face_count":200},
            "normals":{"custom_normals_state":False,"invalid_polygon_normal_ids":[],"invalid_vertex_normal_ids":[]},
            "self_intersection":{"intersecting_face_pair_count":0,"intersecting_face_pairs":[]},
            "capture_script":{"path":s.EVAL_CAPTURE,"sha256":s.digest(root/s.EVAL_CAPTURE)},
            "source_git_commit":"b"*40
        }
        e=root/"joint_evidence.txt";e.write_text("synthetic joint evidence",encoding="utf-8");eref=self.ref(root,e)
        joint={"schema_version":1,"status":"JOINT_SUPPORT_EVIDENCE_COMPLETE","phase_complete":False,
               "production_approved":False,"candidate_sha256":sha,"joints":[]}
        for i,row in enumerate(self.template()["joints"]):
            joint["joints"].append({"id":row["id"],"support_vertex_ids":[i],"loaded_poses":row["loaded_poses"],"evidence":[eref]})
        manifest={"candidate_sha256":sha}
        return raw,evaluated,joint,manifest

    def test_complete_fixture_has_no_surface_blockers(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);raw,ev,joint,manifest=self.fixture(root)
            result=s.verify_packet(root,raw,ev,joint,manifest)
            self.assertEqual(result["surface_quality_status"],"EVIDENCE_COMPLETE")
            self.assertEqual(result["blockers"],[])
            self.assertFalse(result["phase_complete"])

    def test_changed_surface_producer_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);raw,ev,joint,manifest=self.fixture(root)
            (root/s.RAW_AUDIT).write_text("changed",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"producer identity"):
                s.verify_packet(root,raw,ev,joint,manifest)

    def test_mixed_source_commits_are_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);raw,ev,joint,manifest=self.fixture(root)
            ev["source_git_commit"]="c"*40
            with self.assertRaisesRegex(ValueError,"source Git commits differ"):
                s.verify_packet(root,raw,ev,joint,manifest)

    def test_self_intersection_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);raw,ev,joint,manifest=self.fixture(root)
            ev["self_intersection"]={"intersecting_face_pair_count":1,"intersecting_face_pairs":[[1,9]]}
            result=s.verify_packet(root,raw,ev,joint,manifest)
            self.assertTrue(any("self-intersection" in x for x in result["blockers"]))

    def test_unavailable_custom_normal_state_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);raw,ev,joint,manifest=self.fixture(root)
            ev["normals"]["custom_normals_state"]="UNAVAILABLE_IN_THIS_BLENDER_API"
            result=s.verify_packet(root,raw,ev,joint,manifest)
            self.assertTrue(any("custom/split-normal" in x for x in result["blockers"]))

    def test_raw_manifold_finding_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);raw,ev,joint,manifest=self.fixture(root)
            raw["nonmanifold_edges"]=[{"vertices":[1,2]}]
            result=s.verify_packet(root,raw,ev,joint,manifest)
            self.assertTrue(any("nonmanifold_edges" in x for x in result["blockers"]))

    def test_missing_joint_vertex_ids_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);raw,ev,joint,manifest=self.fixture(root)
            joint["joints"][0]["support_vertex_ids"]=None
            result=s.verify_packet(root,raw,ev,joint,manifest)
            self.assertTrue(any("support vertex IDs" in x for x in result["blockers"]))

    def test_joint_template_is_deliberately_unpopulated(self):
        template=self.template()
        self.assertEqual(template["status"],"INCOMPLETE_AUTHORED_JOINT_SUPPORT_PLAN")
        self.assertTrue(all(x["support_vertex_ids"] is None for x in template["joints"]))
        self.assertFalse(template["production_approved"])


if __name__=="__main__":
    unittest.main()
