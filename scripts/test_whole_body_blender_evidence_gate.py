#!/usr/bin/env python3
"""Whole-body source/Blender measurement contract adversarial tests."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"/"anatomy_fit"))
from whole_body_blender_evidence_gate import (
    audit_measurements, read_source_and_audit, source_context
)

ANATOMY=ROOT/"ORIGINAL_V1_WORK"/"anatomy"
BONES=json.loads((ANATOMY/"adult_bone_inventory_206.json").read_text())
JOINTS=json.loads((ANATOMY/"adult_articulation_inventory.json").read_text())
FREEZE=json.loads((ANATOMY/"canonical_freeze_readiness_v1.json").read_text())
BLOCKERS=json.loads((ANATOMY/"audit"/"claude_anatomical_development_20261009"/"blocker_matrix_v1.json").read_text())


def digest(source):
    return hashlib.sha256(
        json.dumps(source,sort_keys=True,separators=(",",":")).encode()).hexdigest()


def bone(bone_id, *, kind="blender_evaluated_mesh",watertight=True):
    return {
        "bone_id":bone_id,
        "object_name":"QA_"+bone_id,
        "surface_kind":kind,
        "evaluated_vertex_buffer_sha256":"c"*64,
        "vertex_count":12,
        "triangle_count":20,
        "world_bounds_m":{"min":[-.1,0,1],"max":[.1,.05,1.1]},
        "watertight_mesh":watertight,
        "bone_anatomy_expert_verified":False,
    }


def pose(joint="skull_ethmoid_frontal",margin=-0.25,method="mesh_bvh_signed"):
    return {
        "pose_id":"neutral_rest","movement_family":"neutral","frame":0,
        "joint_surface_measurements":[{
            "articulation_id":joint,
            "separation_mm":margin,
            "method":method,
            "bone_contact_anatomically_approved":False,
        }]
    }


def sample():
    return {
        "schema_version":1,"kind":"HGPT_BLENDER_206_BONE_QA_EXPORT",
        "provenance":{
            "git_commit_sha":"a"*40,
            "blender_scene_sha256":"b"*64,
            "bone_inventory_sha256":digest(BONES),
            "joint_inventory_sha256":digest(JOINTS),
            "world_unit":"metres",
            "anatomical_label_basis":"source_anatomical_bone_id",
            "scene_was_evaluated_by_bpy":True,
        },
        "anatomical_identity_approved":False,
        "canonical_promotion_allowed":False,
        "bone_surfaces":[bone("ethmoid"),bone("frontal")],
        "poses":[pose()],
    }


class WholeBodyBpyEvidenceGate(unittest.TestCase):
    def test_exact_adult_206_bone_427_joint_46_ancillary_sources(self):
        b,j,regions=source_context(BONES,JOINTS,FREEZE,BLOCKERS)
        self.assertEqual(len(b),206)
        self.assertEqual(len(j),427)
        self.assertEqual(len(JOINTS["additional_structures"]),46)
        self.assertEqual(len(regions),206)
        self.assertIn("costochondral_01_left",j)
        self.assertIn("skull_ethmoid_frontal",j)

    def test_valid_bpy_intake_reports_actual_coverage_without_freezing(self):
        q=audit_measurements(sample(),BONES,JOINTS,FREEZE,BLOCKERS)
        self.assertEqual(q["observed_source_bones"],2)
        self.assertEqual(len(q["missing_source_bones"]),204)
        self.assertEqual(q["observed_distinct_articulations"],1)
        self.assertEqual(len(q["missing_articulation_ids"]),426)
        self.assertEqual(q["movement_families_observed"],{"neutral":1})
        self.assertEqual(len(q["qualified_signed_negative_bone_clearances_review_required"]),1)
        self.assertEqual(q["qualified_signed_negative_bone_clearances_review_required"][0]["signed_separation_mm"],-.25)
        self.assertEqual(q["actual_readiness_counts_unchanged"],
                         {"READY":0,"PARTIAL":9,"BLOCKED":3})
        self.assertEqual(len(q["remaining_11_source_blocker_ids"]),11)
        self.assertFalse(q["source_mesh_refitting_authorized"])
        self.assertFalse(q["production_or_canonical_promotion_allowed"])
        self.assertFalse(q["bone_identity_independently_verified"])

    def test_nonbone_cartilage_contact_never_certified_by_only_two_bones(self):
        r=sample()
        r["bone_surfaces"]=[bone("rib_01_left"),bone("sternum")]
        r["poses"]=[pose("sternocostal_01_left",-.3)]
        result=audit_measurements(r,BONES,JOINTS,FREEZE,BLOCKERS)
        self.assertEqual(len(result["qualified_signed_negative_bone_clearances_review_required"]),0)
        self.assertEqual(len(result["unqualified_negative_distance_claims"]),1)
        self.assertEqual(len(result["joint_measurements_without_qualified_closed_bone_surfaces"]),1)
        self.assertIn("costal_cartilage_01_left",
                      JOINTS["articulations"][next(i for i,x in enumerate(JOINTS["articulations"])
                           if x["id"]=="sternocostal_01_left")]["participants"])

    def test_unsigned_and_control_stick_negative_not_bone_interpenetration(self):
        for method in ("mesh_bvh_unsigned","control_stick_distance"):
            r=sample()
            r["poses"][0]["joint_surface_measurements"][0]["method"]=method
            with self.subTest(method=method):
                q=audit_measurements(r,BONES,JOINTS,FREEZE,BLOCKERS)
                self.assertFalse(q["qualified_signed_negative_bone_clearances_review_required"])
                self.assertEqual(len(q["unqualified_negative_distance_claims"]),1)
        r=sample()
        r["bone_surfaces"][0]["watertight_mesh"]=False
        result=audit_measurements(r,BONES,JOINTS,FREEZE,BLOCKERS)
        self.assertFalse(result["qualified_signed_negative_bone_clearances_review_required"])

    def test_forbidden_auto_approval_and_mesh_refit_claims_rejected(self):
        for key in ("anatomical_identity_approved","canonical_promotion_allowed"):
            p=sample()
            p[key]=True
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,"approve"):
                audit_measurements(p,BONES,JOINTS,FREEZE,BLOCKERS)
        p=sample();p["bone_surfaces"][0]["bone_anatomy_expert_verified"]=True
        with self.assertRaisesRegex(ValueError,"expert"):
            audit_measurements(p,BONES,JOINTS,FREEZE,BLOCKERS)
        p=sample();p["poses"][0]["joint_surface_measurements"][0]["bone_contact_anatomically_approved"]=True
        with self.assertRaisesRegex(ValueError,"self-approve"):
            audit_measurements(p,BONES,JOINTS,FREEZE,BLOCKERS)

    def test_source_sha_provenance_and_legacy_side_mapping_guard(self):
        for key,wrong in (("bone_inventory_sha256","0"*64),
                          ("joint_inventory_sha256","0"*64),
                          ("world_unit","millimetres"),
                          ("anatomical_label_basis","runtime_suffix_left"),
                          ("scene_was_evaluated_by_bpy",False)):
            p=sample()
            p["provenance"][key]=wrong
            with self.subTest(key=key),self.assertRaises(ValueError):
                audit_measurements(p,BONES,JOINTS,FREEZE,BLOCKERS)
        p=sample()
        p["provenance"]["git_commit_sha"]="bad-ref"
        with self.assertRaisesRegex(ValueError,"git commit"):
            audit_measurements(p,BONES,JOINTS,FREEZE,BLOCKERS)

    def test_malformed_bone_identity_duplicate_missing_geometry_and_nan_fail(self):
        variants=[]
        q=sample();q["bone_surfaces"][0]["bone_id"]="unknown_bone";variants.append(q)
        q=sample();q["bone_surfaces"][1]["bone_id"]="ethmoid";variants.append(q)
        q=sample();q["bone_surfaces"][0]["vertex_count"]=2;variants.append(q)
        q=sample();q["bone_surfaces"][0]["world_bounds_m"]["min"][0]=.3;variants.append(q)
        q=sample();q["bone_surfaces"][0]["world_bounds_m"]["max"][2]=float("nan");variants.append(q)
        q=sample();q["bone_surfaces"][0]["surface_kind"]="mesh_approved";variants.append(q)
        for q in variants:
            with self.subTest(sample=str(q["bone_surfaces"][0])[:90]),self.assertRaises(ValueError):
                audit_measurements(q,BONES,JOINTS,FREEZE,BLOCKERS)

    def test_pose_unknown_joint_duplicate_invalid_method_nan_and_unknown_family(self):
        variants=[]
        q=sample();q["poses"][0]["joint_surface_measurements"][0]["articulation_id"]="not_in_inventory";variants.append(q)
        q=sample();q["poses"].append(copy.deepcopy(q["poses"][0]));variants.append(q)
        q=sample();q["poses"][0]["movement_family"]="unproven_exercise";variants.append(q)
        q=sample();q["poses"][0]["joint_surface_measurements"][0]["method"]="signed_guess";variants.append(q)
        q=sample();q["poses"][0]["joint_surface_measurements"][0]["separation_mm"]=float("nan");variants.append(q)
        q=sample();q["poses"][0]["frame"]=-1;variants.append(q)
        for q in variants:
            with self.subTest(kind=str(q["poses"][0])[:100]),self.assertRaises(ValueError):
                audit_measurements(q,BONES,JOINTS,FREEZE,BLOCKERS)

    def test_partial_reporting_must_not_claim_full_3d_anatomical_coverage(self):
        q=sample()
        q["poses"][0]["joint_surface_measurements"]=[]
        result=read_source_and_audit(q)
        self.assertEqual(result["observed_distinct_articulations"],0)
        self.assertEqual(len(result["missing_articulation_ids"]),427)
        self.assertEqual(result["total_joint_measurements"],0)
        self.assertFalse(result["bone_identity_independently_verified"])
        self.assertIn("overhead_push",result["not_sampled_movement_families"])

    def test_unknown_source_and_blocker_changes_fail_closed(self):
        alternate=copy.deepcopy(BONES)
        alternate["bones"][0]["id"]="unknown_bone_from_vendor"
        with self.assertRaises(ValueError):
            audit_measurements(sample(),alternate,JOINTS,FREEZE,BLOCKERS)
        alternate=copy.deepcopy(JOINTS)
        alternate["articulations"][0]["participants"][0]="unknown_joint_participant"
        with self.assertRaisesRegex(ValueError,"unknown bone"):
            audit_measurements(sample(),BONES,alternate,FREEZE,BLOCKERS)
        alternate=copy.deepcopy(FREEZE)
        alternate["region_counts"]["READY"]=1
        with self.assertRaisesRegex(ValueError,"readiness"):
            audit_measurements(sample(),BONES,JOINTS,alternate,BLOCKERS)
        alternate=copy.deepcopy(BLOCKERS)
        alternate["blockers"]=alternate["blockers"][:-1]
        with self.assertRaisesRegex(ValueError,"blocker"):
            audit_measurements(sample(),BONES,JOINTS,FREEZE,alternate)


if __name__ == "__main__":
    unittest.main()
