"""Tests for unified parent->candidate comparison builder."""
import hashlib,importlib.util,json,tempfile
from pathlib import Path
import unittest

MODULE=Path(__file__).with_name("build_original_v1_candidate_comparison_report.py")
SPEC=importlib.util.spec_from_file_location("candidate_compare",MODULE)
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)


class CandidateComparisonTests(unittest.TestCase):
    def write(self,root,name,obj):
        p=root/name; p.write_text(json.dumps(obj),encoding="utf-8"); return name

    def accepted_sweep_fixture(self,root,sweep,csha):
        plan=mod.json.loads((mod.SWEEP_PLAN).read_text(encoding="utf-8"))["sweeps"][sweep]
        raw=self.write(root,f"{sweep}_raw.json",{"candidate_sha256":csha,"source_saved_or_modified":False,"sweeps":{sweep:{}}})
        cal_template=json.loads((mod.ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_RUNNER_CALIBRATION_TEMPLATE.json").read_text(encoding="utf-8"))
        cal_template["calibration_candidate_revision"]="r95"
        cal_template["calibration_candidate_sha256"]="f"*64
        cal_template["runner_sha256"]=hashlib.sha256((mod.ROOT/"scripts/audit_original_v1_human_movement_sweeps_blender.py").read_bytes()).hexdigest()
        cal_template["execution_spec_sha256"]=hashlib.sha256((mod.ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_EXECUTION_SPEC.json").read_bytes()).hexdigest()
        cal_template["frozen_pose_source_sha256"]=hashlib.sha256((mod.ROOT/"scripts/pose_test_original_v1_o4_candidate_blender.py").read_bytes()).hexdigest()
        for adapter in cal_template["adapters"]:
            adapter["state"]="CALIBRATED"
            adapter["skeleton_joint_state_manifest"]="joint.json"
            adapter["outbound_return_evidence"]="return.json"
            adapter["sample_order_evidence"]="order.json"
            adapter["source_hash_evidence"]="hash.json"
            adapter["human_evidence_review_refs"]=["review"]
            if adapter["id"]=="hip_abduction_adduction":
                adapter["mirrored_input_evidence"]="mirror.json"
        cal_template["overall_state"]="CALIBRATED"
        cal_template["engineering_review"]="PASS"
        cal=self.write(root,f"{sweep}_cal.json",cal_template)
        vis=self.write(root,f"{sweep}_vis.json",{"candidate_sha256":csha,"sweep_id":sweep,"samples":[{"label":x,"views":plan["cameras"]} for x in plan["samples"]]})
        cont=self.write(root,f"{sweep}_cont.json",{"candidate_sha256":csha,"sweep_id":sweep})
        rev=self.write(root,f"{sweep}_rev.json",{"candidate_sha256":csha,"sweep_id":sweep})
        record={
          "schema_version":1,"status":"HUMAN_MOVEMENT_SWEEP_ACCEPTANCE","production_approved":False,
          "candidate_revision":"r96","candidate_sha256":csha,"sweep_id":sweep,
          "raw_sweep_report_path":raw,"runner_calibration_record_path":cal,
          "visual_capture_manifest_path":vis,"contact_report_path":None,
          "motion_continuity_evidence_path":cont,"motion_reversibility_evidence_path":rev,
          "human_evidence_review_refs":plan["evidence_ids"],
          "continuity_review_status":"PASS","reversibility_review_status":"PASS",
          "visual_review_status":"PASS","contact_review_status":"NOT_APPLICABLE",
          "engineering_review":"PASS","owner_review":"PENDING"
        }
        return self.write(root,f"{sweep}_accept.json",record)

    def base_fixture(self,root,candidate_issues=None):
        psha="a"*64; csha="b"*64
        parent=self.write(root,"parent.json",{"candidate_under_review":{"sha256":psha},"issues":[]})
        candidate=self.write(root,"candidate.json",{"candidate_under_review":{"sha256":csha},"issues":candidate_issues or []})
        wo=self.write(root,"wo.json",{"candidate_sha256":csha,"regions":[]})
        ce=self.write(root,"ce.json",{"candidate_sha256":csha,"systems":[]})
        me=self.write(root,"me.json",{"candidate_sha256":csha,"samples":[]})
        rev=self.write(root,"rev.json",{"candidate_sha256":csha,"overall_status":"CLEAN"})
        cont=self.write(root,"cont.json",{"candidate_sha256":csha})
        pose=self.write(root,"pose.json",{"candidate_sha256":csha,"poses":{}})
        regression=self.write(root,"regression.json",{"candidate_sha256":csha,"status":"PASS"})
        change=self.write(root,"change.json",{"candidate_sha256":csha,"status":"PASS"})
        manifest={
          "parent":{"revision":"r95","sha256":psha,"issue_ledger_path":parent},
          "candidate":{"revision":"r96","sha256":csha,"source_branch":"fixture","issue_ledger_path":candidate},
          "scope":{"repair_package_ids":[],"region_ids":[],"coupling_system_ids":[],"defect_ids":[]},
          "evidence":{
            "weights_only_acceptance_path":wo,
            "anatomical_coupling_evidence_path":ce,
            "movement_coupling_evidence_path":me,
            "motion_reversibility_path":rev,
            "motion_continuity_path":cont,
            "continuity_engineering_review_status":"PASS",
            "repair_declaration_paths":[],
            "repair_execution_record_paths":[],
            "pose_capture_plan_path":pose,
            "regression_report_path":regression,
            "regression_status":"PASS",
            "contact_report_path":None,
            "contact_status":"NOT_APPLICABLE",
            "surface_visual_review_path":None,
            "visual_capture_manifest_paths":[],
            "visual_engineering_review_status":"NOT_APPLICABLE",
            "change_audit_path":change,
            "change_audit_status":"PASS",
            "human_movement_sweep_acceptance_paths":[]
          }
        }
        return manifest

    def test_fully_bound_empty_scope_fixture_is_eligible(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); report=mod.build(self.base_fixture(root),root)
            self.assertTrue(report["engineering_clear_eligible"])
            self.assertEqual(report["failed_checks"],[])

    def test_missing_required_evidence_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); manifest=self.base_fixture(root)
            manifest["evidence"]["weights_only_acceptance_path"]=None
            report=mod.build(manifest,root)
            self.assertFalse(report["engineering_clear_eligible"])
            self.assertIn("weights_only_present",report["failed_checks"])

    def test_new_critical_high_blocker_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            manifest=self.base_fixture(root,[{"id":"NEW","severity":"High","state":"Open","closure_evidence":[]}])
            report=mod.build(manifest,root)
            self.assertIn("NEW",report["new_open_critical_high"])
            self.assertFalse(report["engineering_clear_eligible"])

    def test_pass_status_without_backing_file_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); manifest=self.base_fixture(root)
            manifest["evidence"]["regression_report_path"]=None
            report=mod.build(manifest,root)
            self.assertIn("regression_report_path_present",report["failed_checks"])
            self.assertFalse(report["engineering_clear_eligible"])

    def test_wrong_candidate_sha_in_backing_file_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); manifest=self.base_fixture(root)
            manifest["evidence"]["change_audit_path"]=self.write(root,"wrong_change.json",{"candidate_sha256":"c"*64})
            report=mod.build(manifest,root)
            self.assertIn("change_audit_path_candidate_sha",report["failed_checks"])

    def test_scoped_repair_requires_post_edit_execution_record(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); manifest=self.base_fixture(root)
            csha=manifest["candidate"]["sha256"]
            manifest["scope"]["repair_package_ids"]=["RP-PEC-AX-002"]
            manifest["scope"]["coupling_system_ids"]=["CP-PEC-AX-002"]
            manifest["evidence"]["anatomical_coupling_evidence_path"]=self.write(
                root,"ce_scope.json",
                {"candidate_sha256":csha,"systems":[{"coupling_system_id":"CP-PEC-AX-002","engineering_disposition":"CLEAR"}]}
            )
            declaration={
              "candidate_revision":"r96","candidate_sha256":"d"*64,"pre_edit_candidate_sha256":"d"*64,
              "repair_package_id":"RP-PEC-AX-002","coupling_system_id":"CP-PEC-AX-002"
            }
            manifest["evidence"]["repair_declaration_paths"]=[self.write(root,"declaration.json",declaration)]
            report=mod.build(manifest,root)
            self.assertIn("repair_execution_package:RP-PEC-AX-002",report["failed_checks"])
            self.assertFalse(report["engineering_clear_eligible"])

    def test_coupling_scope_cannot_omit_connected_body_regions(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); manifest=self.base_fixture(root)
            manifest["scope"]["coupling_system_ids"]=["CP-PEC-AX-002"]
            report=mod.build(manifest,root)
            self.assertIn("scope_regions_cover_coupling:CP-PEC-AX-002",report["failed_checks"])

    def test_visual_not_applicable_is_invalid_for_scoped_region(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); manifest=self.base_fixture(root)
            manifest["scope"]["region_ids"]=["chest_anterior_axilla"]
            report=mod.build(manifest,root)
            self.assertIn("visual_engineering_review_status",report["failed_checks"])

    def test_contact_not_applicable_is_invalid_for_contact_region(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); manifest=self.base_fixture(root)
            manifest["scope"]["region_ids"]=["forearm_wrist"]
            report=mod.build(manifest,root)
            self.assertIn("contact_status",report["failed_checks"])

    def test_shoulder_package_requires_both_sweep_only_acceptance_records(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); manifest=self.base_fixture(root)
            manifest["scope"]["repair_package_ids"]=["RP-PEC-AX-002"]
            report=mod.build(manifest,root)
            self.assertIn("shoulder_abduction_elevation",report["required_sweep_only_movements"])
            self.assertIn("humeral_internal_external_rotation",report["required_sweep_only_movements"])
            self.assertIn("sweep_acceptance:shoulder_abduction_elevation",report["failed_checks"])
            self.assertIn("sweep_acceptance:humeral_internal_external_rotation",report["failed_checks"])

    def test_one_shoulder_sweep_acceptance_does_not_hide_the_other(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); manifest=self.base_fixture(root)
            csha=manifest["candidate"]["sha256"]
            manifest["scope"]["repair_package_ids"]=["RP-PEC-AX-002"]
            manifest["evidence"]["human_movement_sweep_acceptance_paths"]=[
                self.accepted_sweep_fixture(root,"shoulder_abduction_elevation",csha)
            ]
            report=mod.build(manifest,root)
            self.assertNotIn("sweep_acceptance:shoulder_abduction_elevation",report["failed_checks"])
            self.assertIn("sweep_acceptance:humeral_internal_external_rotation",report["failed_checks"])

    def test_raw_sweep_report_path_is_not_an_acceptance_substitute(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); manifest=self.base_fixture(root)
            csha=manifest["candidate"]["sha256"]
            manifest["scope"]["repair_package_ids"]=["RP-PEC-AX-002"]
            raw=self.write(root,"raw_only.json",{
              "candidate_sha256":csha,"source_saved_or_modified":False,
              "sweeps":{"shoulder_abduction_elevation":{}}
            })
            manifest["evidence"]["human_movement_sweep_acceptance_paths"]=[raw]
            report=mod.build(manifest,root)
            self.assertIn("sweep_acceptance_record:raw_only.json",report["failed_checks"])
            self.assertIn("sweep_acceptance:shoulder_abduction_elevation",report["failed_checks"])

    def test_empty_scope_requires_no_sweep_acceptance(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); report=mod.build(self.base_fixture(root),root)
            self.assertEqual(report["required_sweep_only_movements"],[])
            self.assertEqual(report["accepted_sweep_only_movements"],[])


if __name__=="__main__": unittest.main()
