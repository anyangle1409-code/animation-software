"""Tests for the fail-closed grip/wrist recovery gate."""
import copy
import unittest

import original_v1_grip_wrist_gate as gate

SHA = "a" * 64
RENDER_SHA = "b" * 64
COMMIT_SHA = "c" * 40


def diagnostic():
    def side(handle=False):
        joints={}
        for digit in gate.DIGITS:
            joints[digit]={f"{digit}_0{k}_l":float(10*k) for k in (1,2,3)}
        contacts={}
        if handle:
            for digit in gate.DIGITS:
                contacts[digit]={
                    "owned_vertex_count":10,
                    "minimum_signed_distance_m":-0.001,
                    "median_signed_distance_m":0.001,
                    "maximum_signed_distance_m":0.01,
                    "within_2mm_surface_fraction":0.5,
                }
        return {
            "joint_basis_rotation_deg":joints,
            "contacts":contacts,
            "forearm_basis_rotation_deg":5.0,
            "hand_basis_rotation_deg":2.0,
            "forearm_to_hand_direction_deg":10.0,
            "forearm_direction":[0.0,1.0,0.0],
            "hand_direction":[0.0,1.0,0.0],
            "palm_normal":[0.0,0.0,1.0],
            "handle":{"radius_m":0.017} if handle else None,
        }
    poses={}
    for pose in gate.REQUIRED_POSES:
        row=side(pose in gate.HANDLE_POSES)
        right=copy.deepcopy(row)
        poses[pose]={"left":row,"right":right}
    return {
        "schema_version":1,
        "status":"GRIP_WRIST_DIAGNOSTIC",
        "production_approved":False,
        "source_candidate_sha256":SHA,
        "pose_definition_script_sha256":"d"*64,
        "saved_blend":False,
        "poses":poses,
    }


def visual():
    return {
        "schema_version":1,
        "status":"GRIP_WRIST_VISUAL_REVIEW",
        "production_approved":False,
        "candidate_sha256":SHA,
        "source_git_commit":COMMIT_SHA,
        "production_path_rendered":True,
        "visual_pass":True,
        "grip_contact_pass":True,
        "thumb_opposition_pass":True,
        "wrist_load_path_pass":True,
        "whole_body_regression_pass":True,
        "real_human_reference_checked":True,
        "required_issue_failures_remaining":0,
        "renders":[{"pose":"curl_handle","view":"palm_oblique","path":"review.png","sha256":RENDER_SHA}],
        "issue_reviews":[
            {"id":"WB-GRP-009","status":"PASS","evidence_paths":["review.png"],"human_evidence_ids":["HE-GRP-001"],"review_note":"Fixture grip review."},
            {"id":"WB-WRI-010","status":"PASS","evidence_paths":["review.png"],"human_evidence_ids":["HE-WRI-001"],"review_note":"Fixture wrist review."},
        ],
    }


class GripWristGateTests(unittest.TestCase):
    def comparison(self):
        return {"status":"IMPROVED","regression_count":0,"baseline_failed_checks":2,"candidate_failed_checks":1}

    def test_complete_fixture_passes(self):
        result=gate.evaluate_gate(self.comparison(),diagnostic(),visual(),expected_candidate_sha256=SHA)
        self.assertTrue(result["grip_wrist_gate_pass"],result["reasons"])
        self.assertFalse(result["production_approved"])

    def test_missing_required_diagnostic_pose_blocks(self):
        d=diagnostic(); del d["poses"]["pullup_bar"]
        errors="\n".join(gate.validate_diagnostic(d,SHA))
        self.assertIn("diagnostic pose missing: pullup_bar",errors)

    def test_missing_digit_contact_measurement_blocks_handle_pose(self):
        d=diagnostic(); del d["poses"]["curl_handle"]["left"]["contacts"]["thumb"]
        errors="\n".join(gate.validate_diagnostic(d,SHA))
        self.assertIn("contact stats missing for thumb",errors)

    def test_whole_candidate_regression_blocks(self):
        comp=self.comparison(); comp["status"]="REGRESSION"; comp["regression_count"]=1
        result=gate.evaluate_gate(comp,diagnostic(),visual(),expected_candidate_sha256=SHA)
        self.assertIn("whole-candidate numerical regression present",result["reasons"])

    def test_visual_issue_must_explicitly_pass(self):
        v=visual(); v["issue_reviews"][0]["status"]="FAIL"
        errors="\n".join(gate.validate_visual_review(v,SHA))
        self.assertIn("visual review issue not passed: WB-GRP-009",errors)

    def test_global_other_blockers_are_not_falsely_hidden_in_stage_gate(self):
        result=gate.evaluate_gate(self.comparison(),diagnostic(),visual(),expected_candidate_sha256=SHA)
        self.assertTrue(result["grip_wrist_gate_pass"])
        self.assertIn("WB-GRP-009/WB-WRI-010",result["rule"])


if __name__=="__main__":
    unittest.main()
