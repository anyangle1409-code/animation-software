"""Phase 7 garment scene/provenance evidence stays fail-closed."""
from __future__ import annotations
import copy
from pathlib import Path
import tempfile
import unittest

import original_v1_phase7_garment_scene as g


class Phase7GarmentSceneTests(unittest.TestCase):
    def ref(self, root: Path, p: Path):
        return {"path": p.relative_to(root).as_posix(), "sha256": g.digest(p)}

    def fixture(self, root: Path):
        sha="a"*64
        obj=lambda name: {
            "name":name,"object_library":None,"data_library":None,
            "vertex_count":100,"edge_count":200,"face_count":120,"loop_count":360,
            "vertex_groups":["pelvis"],"attributes":[],"uv_layers":[],
            "has_custom_normals":False,
            "modifiers":[{"name":"Armature","type":"ARMATURE","properties":{"show_viewport":True},"unsupported_properties":[]}],
            "shape_keys":{"present":False,"key_blocks":[],"drivers":[]},
            "materials":[],"images":[],"armature":g.EXPECTED_RIG
        }
        scene={
            "status":"EVIDENCE_ONLY","phase_complete":False,"production_approved":False,
            "candidate_sha256":sha,"rig_id":"hgpt_canonical_v4_original",
            "rig":{"name":g.EXPECTED_RIG,"bone_count":63},
            "body":obj(g.EXPECTED_BODY),"garment":obj(g.EXPECTED_GARMENT),
            "scene_linked_libraries":[]
        }
        ev=root/"op.txt";ev.write_text("synthetic operation evidence",encoding="utf-8");eref=self.ref(root,ev)
        authoring={
            "schema_version":1,"status":"AUTHORING_EVIDENCE_COMPLETE","phase":7,
            "phase_complete":False,"production_approved":False,"candidate_sha256":sha,
            "garment_object":g.EXPECTED_GARMENT,
            "provenance":{"independent_authorship":True,"starting_source":"blank project-authored garment",
                          "legacy_geometry_imported":False,"third_party_geometry_imported":False,
                          "transferred_weights_or_bind_data":False,"external_texture_or_material_content":False},
            "operation_history":[{
                "id":"op1","description":"fixture garment operation","tool_or_method":"Blender native",
                "scope":"garment","input_candidate_sha256":"b"*64,"output_candidate_sha256":sha,
                "topology_changed":True,"weights_changed":True,"evidence":[eref]
            }]
        }
        raw={"status":"EVIDENCE_ONLY","phase_complete":False,"production_approved":False,"candidate_sha256":sha}
        manifest={"candidate_sha256":sha}
        return scene,authoring,raw,manifest

    def test_complete_fixture_is_evidence_complete(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);scene,auth,raw,man=self.fixture(root)
            result=g.verify_scene(root,scene,auth,raw,man)
            self.assertEqual(result["garment_scene_status"],"EVIDENCE_COMPLETE")
            self.assertFalse(result["phase_complete"])

    def test_linked_library_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);scene,auth,raw,man=self.fixture(root)
            scene["scene_linked_libraries"]=["/foreign/library.blend"]
            result=g.verify_scene(root,scene,auth,raw,man)
            self.assertTrue(any("linked external libraries" in x for x in result["blockers"]))

    def test_modifier_property_gap_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);scene,auth,raw,man=self.fixture(root)
            scene["garment"]["modifiers"][0]["unsupported_properties"]=[{"property":"x"}]
            result=g.verify_scene(root,scene,auth,raw,man)
            self.assertTrue(any("modifier properties unresolved" in x for x in result["blockers"]))

    def test_false_clean_room_claim_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);scene,auth,raw,man=self.fixture(root)
            auth["provenance"]["third_party_geometry_imported"]=True
            result=g.verify_scene(root,scene,auth,raw,man)
            self.assertTrue(any("third_party_geometry_imported" in x for x in result["blockers"]))

    def test_operation_chain_must_end_at_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);scene,auth,raw,man=self.fixture(root)
            auth["operation_history"][0]["output_candidate_sha256"]="c"*64
            result=g.verify_scene(root,scene,auth,raw,man)
            self.assertTrue(any("final garment operation output" in x for x in result["blockers"]))

    def test_scene_candidate_mismatch_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);scene,auth,raw,man=self.fixture(root)
            scene["candidate_sha256"]="f"*64
            with self.assertRaisesRegex(ValueError,"scene candidate differs"):
                g.verify_scene(root,scene,auth,raw,man)


if __name__=="__main__":
    unittest.main()
