"""Third-party-free STL byte inspection and external geometry quarantine tests."""
import copy
import hashlib
import json
import math
import struct
import sys
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/"anatomy_fit"))
import stl_bone_mesh_intake as intake

MANIFEST=HERE.parent/"ORIGINAL_V1_WORK/anatomy/audit/nih3d_male_pelvis_mesh_source_manifest_20261009.json"
TETRA=[
    [[0,0,0],[0,1,0],[1,0,0]],
    [[0,0,0],[1,0,0],[0,0,1]],
    [[0,0,0],[0,0,1],[0,1,0]],
    [[1,0,0],[0,1,0],[0,0,1]],
]


def binary_triangles(tris,header=b"generated binary STL"):
    raw=header.ljust(80,b" ")[:80]+struct.pack("<I",len(tris))
    for tri in tris:
        floats=[0,0,1]+[v for p in tri for v in p]
        raw+=struct.pack("<12fH",*floats,0)
    return raw


def ascii_triangles(tris):
    text="solid synthetic\n"
    for tri in tris:
        text+=" facet normal 0 0 1\n  outer loop\n"
        for xyz in tri:
            text+="   vertex "+" ".join(str(x) for x in xyz)+"\n"
        text+="  endloop\n endfacet\n"
    return (text+"endsolid synthetic\n").encode("ascii")


class STLReadOnly(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.path=self.root/"Os_L_Male_Final.STL"
        self.manifest=json.loads(MANIFEST.read_text())
        self.path.write_bytes(binary_triangles(TETRA))

    def test_valid_binary_geometry_from_actual_file(self):
        r=intake.scan(self.path)
        self.assertEqual(r["format"],"binary")
        self.assertEqual(r["triangle_count"],4)
        self.assertEqual(r["bounding_box_native_units"]["min"],[0,0,0])
        self.assertEqual(r["bounding_box_native_units"]["max"],[1,1,1])
        self.assertFalse(r["STL_native_units_identified"])

    def test_valid_ascii_file(self):
        self.path.write_bytes(ascii_triangles(TETRA))
        r=intake.scan(self.path)
        self.assertEqual(r["format"],"ascii")
        self.assertEqual(r["triangle_count"],4)

    def test_binary_with_ascii_prefix_is_still_binary(self):
        self.path.write_bytes(binary_triangles(TETRA,header=b"solid not ascii really"))
        self.assertEqual(intake.scan(self.path)["format"],"binary")

    def test_sha256_matches_real_file_bytes(self):
        raw=self.path.read_bytes()
        result=intake.scan(self.path)
        self.assertEqual(result["content_sha256"],hashlib.sha256(raw).hexdigest())
        self.assertEqual(result["file_size_bytes"],len(raw))

    def test_strict_independently_pinned_sha(self):
        digest=hashlib.sha256(self.path.read_bytes()).hexdigest()
        r=intake.audit(self.path,self.manifest,"hip_bone_left",expected_sha256=digest)
        self.assertTrue(r["bytes_match_independently_provided_sha256"])
        self.assertFalse(r["canonical_promotion_allowed"])

    def test_sha_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError,"does not match pinned"):
            intake.audit(self.path,self.manifest,"hip_bone_left",expected_sha256="b"*64)

    def test_no_sha_does_not_claim_independent_byte_verification(self):
        r=intake.audit(self.path,self.manifest,"hip_bone_left")
        self.assertFalse(r["bytes_match_independently_provided_sha256"])
        self.assertFalse(r["bone_surface_reconstruction_permitted"])
        self.assertFalse(r["entry_licence_verified"])

    def test_vertex_on_actual_mesh_detected(self):
        r=intake.scan(self.path,{"selected_asis":[1,0,0]})
        self.assertEqual(r["nearest_actual_vertex_native_units"]["selected_asis"],0)

    def test_arbitrary_nonmesh_vertex_has_positive_distance(self):
        r=intake.scan(self.path,{"invented_ASIS":[1,1,1]})
        self.assertGreater(r["nearest_actual_vertex_native_units"]["invented_ASIS"],.9)

    def test_no_arbitrary_source_world_or_unit_transform(self):
        r=intake.audit(self.path,self.manifest,"hip_bone_left")
        self.assertFalse(r["source_mesh_scale_verified"])
        self.assertFalse(r["world_transform_verified"])
        self.assertEqual(self.manifest["original_unit_to_m"],None)

    def test_source_class_is_teaching_sculpt_not_raw_CT(self):
        r=intake.audit(self.path,self.manifest,"hip_bone_left")
        self.assertIn("sculpted_print_prepared",r["source_asset_class"])
        self.assertFalse(r["actual_original_CT_voxels_inspected"])
        self.assertFalse(r["bone_anatomical_geometry_verified"])

    def test_wrong_bone_file_identity_rejected(self):
        with self.assertRaisesRegex(ValueError,"file name does not match"):
            intake.audit(self.path,self.manifest,"femur_left")

    def test_unknown_bone_name_rejected(self):
        with self.assertRaisesRegex(ValueError,"unrecognised skeletal"):
            intake.audit(self.path,self.manifest,"upperarm_left")

    def test_manifest_invented_unit_is_rejected(self):
        m=copy.deepcopy(self.manifest)
        m["files"][0]["unit_to_m"]=.001
        with self.assertRaisesRegex(ValueError,"unverified print scale"):
            intake.audit(self.path,m,"hip_bone_left")

    def test_license_not_automatically_assumed_public_domain(self):
        self.assertEqual(self.manifest["license_status"],"UNVERIFIED_ENTRY_SPECIFIC_LICENSE")
        self.assertIsNone(self.manifest["commercial_app_reuse_allowed"])
        with self.assertRaisesRegex(ValueError,"review entry-specific"):
            m=copy.deepcopy(self.manifest)
            m["license_status"]="PUBLIC_DOMAIN"
            intake.audit(self.path,m,"hip_bone_left")

    def test_truncated_binary_stl_rejected(self):
        self.path.write_bytes(self.path.read_bytes()[:-1])
        with self.assertRaisesRegex(ValueError,"length/count mismatch"):
            intake.scan(self.path)

    def test_corrupt_binary_zero_area_triangle_rejected(self):
        self.path.write_bytes(binary_triangles([[[0,0,0],[0,0,0],[0,0,0]]]))
        with self.assertRaisesRegex(ValueError,"degenerate triangle"):
            intake.scan(self.path)

    def test_binary_nan_rejected(self):
        b=bytearray(self.path.read_bytes())
        struct.pack_into("<f",b,84+12,float("nan"))
        self.path.write_bytes(b)
        with self.assertRaisesRegex(ValueError,"nonfinite binary"):
            intake.scan(self.path)

    def test_ascii_invalid_vertex_rejected(self):
        s=ascii_triangles(TETRA).replace(b"vertex 1 0 0",b"vertex 1 nan 0")
        self.path.write_bytes(s)
        with self.assertRaisesRegex(ValueError,"nonfinite or invalid"):
            intake.scan(self.path)

    def test_ascii_incomplete_triangle_rejected(self):
        self.path.write_bytes(b"solid x\nfacet normal 0 0 1\nouter loop\nvertex 0 0 0\nendloop\nendsolid x\n")
        with self.assertRaisesRegex(ValueError,"incomplete ASCII"):
            intake.scan(self.path)

    def test_ascii_overfull_triangle_rejected(self):
        t=ascii_triangles(TETRA)
        t=t.replace(b"  endloop",b"   vertex 1 1 1\n  endloop",1)
        self.path.write_bytes(t)
        with self.assertRaisesRegex(ValueError,"more than three"):
            intake.scan(self.path)

    def test_manifest_promotion_rejected(self):
        m=copy.deepcopy(self.manifest)
        m["canonical_promotion_allowed"]=True
        with self.assertRaisesRegex(ValueError,"manifest identity/status changed"):
            intake.audit(self.path,m,"hip_bone_left")

    def test_input_mesh_bytes_and_manifest_never_modified(self):
        original=self.path.read_bytes()
        m=json.dumps(self.manifest,sort_keys=True)
        intake.audit(self.path,self.manifest,"hip_bone_left")
        self.assertEqual(self.path.read_bytes(),original)
        self.assertEqual(json.dumps(self.manifest,sort_keys=True),m)

    def test_no_license_reuse_claim_after_successful_sha_match(self):
        digest=hashlib.sha256(self.path.read_bytes()).hexdigest()
        r=intake.audit(self.path,self.manifest,"hip_bone_left",digest)
        for flag in ("entry_licence_verified","commercial_reuse_permitted",
                     "canonical_promotion_allowed","world_transform_verified",
                     "physical_landmark_identity_verified"):
            self.assertFalse(r[flag])


if __name__=="__main__":
    unittest.main()
