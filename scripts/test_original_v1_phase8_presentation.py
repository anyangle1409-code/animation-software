"""Phase 8 numeric material/presentation verifier tests."""
from __future__ import annotations
from pathlib import Path
import tempfile
import unittest

import original_v1_phase8_presentation as p


class Phase8PresentationTests(unittest.TestCase):
    def ref(self,root:Path,path:Path):
        return {"path":path.relative_to(root).as_posix(),"sha256":p.digest(path)}

    def material(self,name):
        return {"name":name,"library":None,"use_nodes":True,"diffuse_color":[0.5,0.5,0.5,1],
                "metallic":0.0,"roughness":0.5,
                "node_tree":{"nodes":[{"name":"Principled","type":"BSDF_PRINCIPLED",
                                      "inputs":[{"name":"Roughness","default":{"available":True,"value":0.5}}]}],
                             "links":[],"images":[]}}

    def fixture(self,root:Path):
        sha="a"*64
        scene={"status":"EVIDENCE_ONLY","phase_complete":False,"production_approved":False,
               "candidate_sha256":sha,"scene_linked_libraries":[],
               "materials":{
                   "body":[{"slot_index":0,"slot_name":"Skin","material":self.material("Skin")}],
                   "garment":[{"slot_index":0,"slot_name":"Shorts","material":self.material("Shorts")}]
               },
               "world":{"name":"World","library":None,"node_tree":{"nodes":[],"links":[],"images":[]}},
               "lights":[{"object":"Key","library":None,"data_library":None}],
               "cameras":[{"object":"Camera","library":None,"data_library":None}],
               "active_camera":"Camera",
               "render":{"engine":"BLENDER_EEVEE_NEXT","resolution_x":1000,"resolution_y":1000},
               "colour_management":{"display_device":"sRGB","view_transform":"AgX","look":"Medium High Contrast"}}
        ev1=root/"skin.txt";ev1.write_text("skin authoring evidence",encoding="utf-8")
        ev2=root/"shorts.txt";ev2.write_text("shorts authoring evidence",encoding="utf-8")
        provenance={"schema_version":1,"status":"MATERIAL_PROVENANCE_COMPLETE","phase":8,
                    "phase_complete":False,"production_approved":False,"candidate_sha256":sha,
                    "policy":{"numeric_materials_only":True,"third_party_textures_allowed":False,
                              "external_hdri_allowed":False,"linked_material_libraries_allowed":False,
                              "geometry_or_weight_changes_allowed":False},
                    "materials":[
                        {"name":"Skin","assigned_scope":["body"],"independent_authorship":True,"numeric_only":True,
                         "third_party_content":False,"external_image_sources":False,"operation_evidence":[self.ref(root,ev1)]},
                        {"name":"Shorts","assigned_scope":["garment"],"independent_authorship":True,"numeric_only":True,
                         "third_party_content":False,"external_image_sources":False,"operation_evidence":[self.ref(root,ev2)]}
                    ]}
        return scene,provenance,{"candidate_sha256":sha}

    def test_numeric_owned_fixture_is_complete(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);scene,prov,manifest=self.fixture(root)
            result=p.verify_scene(root,scene,prov,manifest)
            self.assertEqual(result["material_scene_status"],"EVIDENCE_COMPLETE")
            self.assertFalse(result["phase_complete"])

    def test_image_texture_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);scene,prov,manifest=self.fixture(root)
            scene["materials"]["body"][0]["material"]["node_tree"]["nodes"].append(
                {"name":"Image Texture","type":"TEX_IMAGE","image":{"filepath":"skin.png"},"inputs":[]})
            result=p.verify_scene(root,scene,prov,manifest)
            self.assertTrue(any("image/unserialized shader input" in x for x in result["blockers"]))

    def test_hdri_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);scene,prov,manifest=self.fixture(root)
            scene["world"]["node_tree"]["images"]=[{"name":"HDRI","filepath":"studio.hdr"}]
            result=p.verify_scene(root,scene,prov,manifest)
            self.assertTrue(any("HDRI" in x for x in result["blockers"]))

    def test_linked_material_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);scene,prov,manifest=self.fixture(root)
            scene["materials"]["garment"][0]["material"]["library"]="/foreign/material.blend"
            result=p.verify_scene(root,scene,prov,manifest)
            self.assertTrue(any("linked material" in x for x in result["blockers"]))

    def test_provenance_scope_must_match_scene(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);scene,prov,manifest=self.fixture(root)
            prov["materials"][0]["assigned_scope"]=["garment"]
            result=p.verify_scene(root,scene,prov,manifest)
            self.assertTrue(any("assigned scope differs" in x for x in result["blockers"]))

    def test_active_camera_required(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);scene,prov,manifest=self.fixture(root)
            scene["active_camera"]=None
            result=p.verify_scene(root,scene,prov,manifest)
            self.assertTrue(any("active presentation camera" in x for x in result["blockers"]))


if __name__=="__main__":
    unittest.main()
