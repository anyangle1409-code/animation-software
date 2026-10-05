"""Tests for generated human movement sweep motion review."""
import hashlib,importlib.util,json,tempfile
from pathlib import Path
import unittest

B=Path(__file__).with_name("build_original_v1_human_movement_sweep_motion_review.py")
V=Path(__file__).with_name("validate_original_v1_human_movement_sweep_motion_review.py")
sp=importlib.util.spec_from_file_location("builder",B); builder=importlib.util.module_from_spec(sp); sp.loader.exec_module(builder)
sp2=importlib.util.spec_from_file_location("validator",V); validator=importlib.util.module_from_spec(sp2); sp2.loader.exec_module(validator)

class SweepMotionReviewTests(unittest.TestCase):
    def raw_report(self,root,sweep="trunk_flexion"):
        spec=json.loads((builder.ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_EXECUTION_SPEC.json").read_text())
        sr=spec["sweeps"][sweep]; csha="a"*64; samples=[]
        variants=["l","r"] if sweep=="hip_abduction_adduction" else [None]
        seen={}
        for variant in variants:
            for row in sr["samples"]:
                norm={k:v for k,v in row.items() if k not in {"label","return_leg"}}
                key=(variant,json.dumps(norm,sort_keys=True))
                if row.get("return_leg") and key in seen:
                    js,ss=seen[key]
                else:
                    js=hashlib.sha256(f"{variant}|{norm}|joint".encode()).hexdigest()
                    ss=hashlib.sha256(f"{variant}|{norm}|snapshot".encode()).hexdigest()
                    seen[key]=(js,ss)
                samples.append({
                  "label":row["label"],"return_leg":bool(row.get("return_leg",False)),
                  "input":{k:v for k,v in row.items() if k!="label"},"variant":variant,
                  "joint_state_sha256":js,"snapshot_sha256":ss,
                  "snapshot":{"final_surface":{},"weights_only_surface":{},"corrective_contribution":{},"shape_key_values":{},"joint_state":{}}
                })
        raw={
          "schema_version":1,"status":"READ_ONLY_GENERIC_HUMAN_MOVEMENT_SWEEP_AUDIT","production_approved":False,
          "candidate":"fixture.blend","candidate_sha256":csha,"candidate_sha256_before":csha,"candidate_sha256_after":csha,
          "runner_script_sha256":hashlib.sha256((builder.ROOT/"scripts/audit_original_v1_human_movement_sweeps_blender.py").read_bytes()).hexdigest(),
          "pose_definition_sha256":hashlib.sha256((builder.ROOT/"scripts/pose_test_original_v1_o4_candidate_blender.py").read_bytes()).hexdigest(),
          "flexion_driver_sha256":hashlib.sha256((builder.ROOT/"scripts/original_v1_flexion_driver.py").read_bytes()).hexdigest(),
          "movement_plan_sha256":hashlib.sha256((builder.ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_PLAN.json").read_bytes()).hexdigest(),
          "sweep_execution_spec_sha256":hashlib.sha256((builder.ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_EXECUTION_SPEC.json").read_bytes()).hexdigest(),
          "blender_version":"fixture","source_saved_or_modified":False,
          "calibration_state":"EXPERIMENTAL_UNCALIBRATED","evidence_readiness":"DIAGNOSTIC_ONLY_INCOMPLETE",
          "runner_capabilities":{
            "deterministic_joint_state_sampling":"IMPLEMENTED","per_sample_joint_state_hash":"IMPLEMENTED",
            "weights_only_surface_summary":"IMPLEMENTED","corrective_contribution_summary":"IMPLEMENTED",
            "runner_script_hash":"IMPLEMENTED","end_of_run_source_rehash":"IMPLEMENTED",
            "visual_capture_manifest":"NOT_IMPLEMENTED","required_regional_renders":"NOT_IMPLEMENTED","contact_load_state":"NOT_IMPLEMENTED"
          },
          "diagnostic_limitations":["fixture"],
          "sweeps":{sweep:{
            "implementation_status":sr["implementation_status"],"plan_evidence_ids":sr["evidence_ids"],
            "plan_regions":sr["regions"],"plan_cameras":sr["cameras"],"samples":samples,
            "visual_capture_status":"NOT_IMPLEMENTED","contact_load_required":bool(sr.get("contact_load_required")),
            "contact_load_status":"NOT_IMPLEMENTED" if sr.get("contact_load_required") else "NOT_APPLICABLE",
            "engineering_review":"PENDING","owner_review":"PENDING"
          }}
        }
        p=root/"raw.json"; p.write_text(json.dumps(raw),encoding="utf-8"); return p

    def test_builder_pairs_return_states_and_replay_hashes(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); raw=self.raw_report(root)
            d=builder.build(raw,"trunk_flexion","r96")
            self.assertEqual(d["deterministic_replay_status"],"PASS")
            self.assertTrue(d["return_pairs"])
            self.assertTrue(all(x["joint_state_match"] and x["snapshot_match"] for x in d["return_pairs"]))
            validator.validate(d,root,False)

    def test_full_pass_requires_adjacent_transition_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); raw=self.raw_report(root); d=builder.build(raw,"trunk_flexion","r96")
            d["continuity_review"]="PASS"; d["reversibility_review"]="PASS"; d["engineering_review"]="PASS"
            with self.assertRaisesRegex(ValueError,"adjacent transition"):
                validator.validate(d,root,True)
            for row in d["adjacent_pairs"]:
                row["engineering_disposition"]="PASS"; row["evidence_refs"]=["visual"]
            out=validator.validate(d,root,True); self.assertEqual(out["engineering_review"],"PASS")

    def test_return_snapshot_mismatch_blocks_reversibility(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); raw=self.raw_report(root)
            obj=json.loads(raw.read_text()); rows=obj["sweeps"]["trunk_flexion"]["samples"]
            ret=next(x for x in rows if x["return_leg"]); ret["snapshot_sha256"]="f"*64
            raw.write_text(json.dumps(obj),encoding="utf-8")
            d=builder.build(raw,"trunk_flexion","r96")
            self.assertEqual(d["deterministic_replay_status"],"FAIL")
            with self.assertRaisesRegex(ValueError,"deterministic replay failed"):
                d["continuity_review"]="PASS"; d["reversibility_review"]="PASS"; d["engineering_review"]="PASS"
                for row in d["adjacent_pairs"]: row["engineering_disposition"]="PASS"; row["evidence_refs"]=["visual"]
                validator.validate(d,root,True)

if __name__=="__main__": unittest.main()
