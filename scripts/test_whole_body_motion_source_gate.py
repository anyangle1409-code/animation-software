#!/usr/bin/env python3
"""Whole-body original-test amplitude evidence: 78/49 must remain quarantined."""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(HERE/"anatomy_fit"))
sys.path.insert(0,str(HERE))
from whole_body_motion_source_gate import (
    ANATOMY, ATLAS, RECORD, SOURCE_QUEUE, digest, evidence_context,
    source_context_from_repo, source_only_summary, motion_report,
)
from whole_body_blender_evidence_gate import read_source_and_audit
from test_whole_body_blender_evidence_gate import sample


def inputs():
    return (json.loads(RECORD.read_text()),json.loads(ATLAS.read_text()),
            json.loads(SOURCE_QUEUE.read_text()))


def measured(source_id=None):
    v=sample()
    if source_id is not None:
        v["poses"][0]["source_isolated_test_id"]=source_id
    return v


class IndependentWholeBodyMotionEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx=source_context_from_repo()

    def test_real_135_278_and_78_49_source_evidence_is_in_sync(self):
        summary=source_only_summary(self.ctx)
        self.assertEqual(summary["source_test_count"],135)
        self.assertEqual(summary["commanded_peak_count"],278)
        self.assertEqual(summary["unsourced_test_count"],49)
        self.assertEqual(summary["unsourced_peak_count"],78)
        self.assertEqual(sum(summary["unverified_peak_count_by_family"].values()),78)
        self.assertEqual(len(summary["unverified_peak_count_by_family"]),12)
        self.assertEqual(summary["original_source_record_sha256"],digest(RECORD))
        self.assertEqual(summary["original_movement_atlas_sha256"],digest(ATLAS))
        self.assertEqual(sum(row["source_test_peaks"] for row in summary["source_tests"]),278)
        self.assertEqual(sum(row["unsourced_peak_count"] for row in summary["source_tests"]),78)
        self.assertFalse(summary["active_passive_or_loaded_ROM_certified"])
        self.assertFalse(summary["whole_body_motion_anatomically_verified"])
        self.assertFalse(summary["real_pose_execution_verified"])

    def test_gh_hip_ribs_tmj_and_finger_test_peaks_are_not_safe_rom(self):
        summary=source_only_summary(self.ctx)
        rows={x["source_isolated_test_id"]:x for x in summary["source_tests"]}
        checks=[
            "hip_abduction_adduction_left","gh_elevation_plane_0_left",
            "talocrural_dorsi_plantarflexion_left","digit2_flexion_left",
            "tmj_opening","cervical_c4_c5_internal",
        ]
        for key in checks:
            with self.subTest(test=key):
                self.assertGreater(rows[key]["unsourced_peak_count"],0)
                self.assertEqual(rows[key]["amplitude_classification"],
                                 "DIAGNOSTIC_ONLY_UNSOURCED_AMPLITUDES")
                self.assertFalse(rows[key]["human_anatomy_or_safe_ROM_verified"])
        self.assertEqual(rows["tmj_opening"]["unsourced_peak_count"],2)
        self.assertTrue(any(x["units"]=="m" for x in rows["tmj_opening"]["unsourced_peaks"]))
        self.assertTrue(any(x["units"]=="deg" for x in rows["tmj_opening"]["unsourced_peaks"]))

    def test_valid_named_blender_pose_is_not_automatically_certified(self):
        for test_id,expected in [
            ("gh_elevation_plane_0_left","DIAGNOSTIC_ONLY_UNSOURCED_AMPLITUDE"),
            ("hip_flexion_extension_left","TRACEABLE_BASIS_NOT_ANATOMICAL_ROM_CERTIFICATION"),
        ]:
            r=measured(test_id)
            q=read_source_and_audit(r)
            out=motion_report(r,self.ctx,q)
            self.assertEqual(out["measured_pose_count"],1)
            self.assertEqual(out["pose_amplitude_grades"][0]["motion_amplitude_grade"],expected)
            self.assertEqual(out["pose_amplitude_grades"][0]["reported_source_isolated_test_id"],test_id)
            self.assertFalse(out["pose_amplitude_grades"][0]["source_test_link_independently_verified"])
            self.assertFalse(out["pose_amplitude_grades"][0]["actual_joint_angles_and_load_match_source_test_verified"])
            self.assertTrue(out["no_movement_certified_as_human_ROM"])
            self.assertFalse(out["canonical_promotion_allowed"])

    def test_no_source_link_remains_unknown_not_sourced(self):
        r=measured()
        out=motion_report(r,self.ctx,read_source_and_audit(r))
        self.assertEqual(out["grades"],{"NO_TEST_AMPLITUDE_PROVENANCE":1})
        self.assertIsNone(out["pose_amplitude_grades"][0]["reported_source_isolated_test_id"])

    def test_invalid_source_id_and_fabricated_approval_fail(self):
        for value in ("invented_and_unproven","cvm1873f",12,True):
            r=measured()
            r["poses"][0]["source_isolated_test_id"]=value
            with self.subTest(value=value),self.assertRaisesRegex(ValueError,"unrecognized source"):
                motion_report(r,self.ctx,read_source_and_audit(r))
        for flag in ("physiological_ROM_certified","exercise_anatomy_approved",
                     "source_test_execution_independently_proven"):
            r=measured("gh_elevation_plane_0_left")
            r["poses"][0][flag]=True
            with self.subTest(flag=flag),self.assertRaisesRegex(ValueError,"self-certify"):
                motion_report(r,self.ctx,read_source_and_audit(r))

    def test_tampering_original_78_queue_is_rejected(self):
        rec,atlas,queue=inputs()
        for corrupt in ("drop_peak","reclassify","remove_family","unverify_sha","self_approve"):
            v=copy.deepcopy(queue)
            if corrupt=="drop_peak":
                v["peaks"].pop()
            elif corrupt=="reclassify":
                v["peaks"][0]["status"]="VERIFIED_HUMAN_ROM"
            elif corrupt=="remove_family":
                v["by_family"].pop("tmj")
            elif corrupt=="unverify_sha":
                v["atlas_sha256"]="0"*64
            else:
                v["anatomical_acceptance"]=True
            with self.subTest(corrupt=corrupt),self.assertRaises(ValueError):
                evidence_context(rec,atlas,v,digest(RECORD),digest(ATLAS))

    def test_unrecorded_motion_beyond_baseline_fails_closed(self):
        rec,atlas,queue=inputs()
        modified=copy.deepcopy(rec)
        # Any extra added isolated test, unexpected new commanded endpoint or
        # changed record SHA requires a fresh reviewed provenance computation.
        with self.assertRaisesRegex(ValueError,"record/atlas SHA"):
            evidence_context(modified,atlas,queue,"0"*64,digest(ATLAS))
        modified=copy.deepcopy(atlas)
        with self.assertRaisesRegex(ValueError,"record/atlas SHA"):
            evidence_context(rec,modified,queue,digest(RECORD),"0"*64)

    def test_source_report_cannot_self_certify_scene_or_readiness(self):
        q=read_source_and_audit(measured())
        r=measured("tmj_opening")
        q["production_or_canonical_promotion_allowed"]=True
        with self.assertRaisesRegex(ValueError,"prerequisite"):
            motion_report(r,self.ctx,q)
        q=read_source_and_audit(r)
        q["reported_scene_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"prerequisite"):
            motion_report(r,self.ctx,q)

    def test_two_poses_with_distinct_source_ids_preserve_order_and_status(self):
        r=measured("hip_flexion_extension_left")
        another=copy.deepcopy(r["poses"][0])
        another["pose_id"]="other_pose"
        another["movement_family"]="overhead_push"
        another["source_isolated_test_id"]="gh_elevation_plane_90_left"
        r["poses"].append(another)
        qa=read_source_and_audit(r)
        out=motion_report(r,self.ctx,qa)
        self.assertEqual(out["measured_pose_count"],2)
        self.assertEqual(out["grades"],{
            "DIAGNOSTIC_ONLY_UNSOURCED_AMPLITUDE":1,
            "TRACEABLE_BASIS_NOT_ANATOMICAL_ROM_CERTIFICATION":1,
        })

    def test_no_source_motion_can_override_preexisting_206_427_gate(self):
        r=measured("gh_elevation_plane_0_left")
        r["poses"][0]["joint_surface_measurements"][0]["articulation_id"]="new_anatomical_contact"
        with self.assertRaises(ValueError):
            read_source_and_audit(r)


if __name__=="__main__":
    unittest.main()
