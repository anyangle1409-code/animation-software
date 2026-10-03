#!/usr/bin/env python3
"""Phase 9 candidate-bound production validation stays fail-closed."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import original_v1_phase9_production_validation as p9


class Phase9ValidationTests(unittest.TestCase):
    def write(self, root: Path, rel: str, data) -> Path:
        path=root/rel;path.parent.mkdir(parents=True,exist_ok=True)
        if isinstance(data,(dict,list)):
            path.write_text(json.dumps(data),encoding="utf-8")
        else:
            path.write_bytes(data)
        return path

    def fixture(self, root: Path):
        candidate="a"*64
        revision="r99"

        # Current shared contracts/tools copied into the isolated fixture root.
        for rel in (
            "ORIGINAL_V1_WORK/SKELETON_MOTION_LOCK_rev2_forearm_twist_only.json",
            "ORIGINAL_V1_WORK/hgpt_canonical_v4_original_rev2c.json",
            p9.ACCEPTANCE,p9.EVALUATOR,p9.HELPER,
        ):
            src=p9.ROOT/rel;dst=root/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
        lock=p9.expected_lock(root)

        spec=json.loads((root/p9.ACCEPTANCE).read_text())
        poses=sorted({x for rows in spec["required_pose_groups"].values() for x in rows}|{"neutral"})
        merged=[]
        for pose in poses:
            row={"pose":pose,"volume_ratio":1.0,"edge_ratio_p01":1.0,"edge_ratio_p99":1.0,
                 "self_intersecting_face_pairs":0,"lowest_z":0.0,
                 "by_region":{"torso":{"min_ratio":1.0,"max_ratio":1.0}}}
            if pose in ("grip","curl_handle","pullup_bar","curl_peak","pullup_top"):
                row["grip_l"]={"max_penetration_mm":0.0,"contact_vertices_within_2mm":50}
                row["grip_r"]={"max_penetration_mm":0.0,"contact_vertices_within_2mm":50}
            merged.append(row)
        merged_path=self.write(root,"evidence/merged.json",merged)
        full={"schema_version":1,"candidate_revision":revision,"candidate_sha256":candidate,
              "merged_pose_report_sha256":p9.digest(merged_path)}
        full_path=self.write(root,"evidence/full_manifest.json",full)

        body={"schema_version":2,"snapshot_scope":"body","candidate_sha256":candidate,"locked_rig":copy.deepcopy(lock)}
        garment={"schema_version":2,"snapshot_scope":"garment","candidate_sha256":candidate,"locked_rig":copy.deepcopy(lock)}
        body_path=self.write(root,"evidence/body_snapshot.json",body)
        garment_path=self.write(root,"evidence/garment_snapshot.json",garment)
        raw={"status":"EVIDENCE_ONLY","phase_complete":False,"production_approved":False,
             "candidate_sha256":candidate,"locked_rig":copy.deepcopy(lock),
             "source_evidence":[p9.ref(root,body_path),p9.ref(root,garment_path)]}
        raw_path=self.write(root,"evidence/raw_pair.json",raw)

        static={"status":"EVIDENCE_ONLY","phase_complete":False,"production_approved":False,
                "candidate_sha256":candidate,"locked_rig":copy.deepcopy(lock),
                "source_evidence":[p9.ref(root,raw_path)]}
        static_path=self.write(root,"evidence/static.json",static)

        range_data={"status":"EVIDENCE_ONLY","phase_complete":False,"production_approved":False,
                    "candidate_sha256":candidate,"locked_rig":copy.deepcopy(lock),
                    "classification":{"classification_complete":True,"unclassified_findings":0,
                                      "unexplained_defects":0,"legitimate_contacts":1,
                                      "production_pass_inferred":False},
                    "source_evidence":[p9.ref(root,static_path)]}
        range_path=self.write(root,"evidence/range.json",range_data)

        bridge={"schema_version":1,"status":"EVIDENCE_ONLY","production_approved":False,"phase_complete":False,
                "runtime_executed":False,"source_bridge_status":"VERIFIED_CURRENT_MODEL_BRANCH_SOURCE",
                "scenarios":{"push_up":{},"dumbbell_bicep_curl":{},"pull_up":{}}}
        bridge_path=self.write(root,"evidence/contact_bridge.json",bridge)

        equiv={"schema_version":1,"status":"EVIDENCE_ONLY","phase_complete":False,"production_approved":False,
               "candidate_sha256":candidate,"equivalence_status":"IDENTICAL_UNDER_GARMENT_PRESENCE",
               "blockers":[],"locked_rig":copy.deepcopy(lock)}
        equiv_path=self.write(root,"evidence/equivalence.json",equiv)

        export_manifest_path=self.write(root,"exports/CANDIDATE_GLB_EXPORT.json",{"fixture":True})
        bare_path=self.write(root,"exports/HomeGymPT_Male_ORIGINAL_v1_CANDIDATE_r99_BARE.glb",b"bare")
        dressed_path=self.write(root,"exports/HomeGymPT_Male_ORIGINAL_v1_CANDIDATE_r99_DRESSED.glb",b"dressed")
        export_receipt={"schema_version":1,"status":"EXPORT_IDENTITY_VERIFIED","candidate_revision":revision,
                        "candidate_sha256":candidate,"production_approved":False,
                        "source_evidence":[p9.ref(root,export_manifest_path),p9.ref(root,bare_path),p9.ref(root,dressed_path)]}
        export_path=self.write(root,"evidence/export_receipt.json",export_receipt)

        prod={}
        for group in p9.GROUPS:
            path=self.write(root,f"evidence/prod_{group}.json",p9.summary_for_group(root,merged,group))
            prod[group]=p9.ref(root,path)

        receipt={"schema_version":1,"phase":9,"contract_status":"PHASE9_VALIDATION_VERIFIED",
                 "phase_complete":False,"production_approved":False,
                 "candidate_revision":revision,"candidate_sha256":candidate,
                 "full_evidence_manifest":p9.ref(root,full_path),
                 "merged_pose_report":p9.ref(root,merged_path),
                 "production_evaluations":prod,
                 "raw_pair":p9.ref(root,raw_path),
                 "static_dressed":p9.ref(root,static_path),
                 "range_evidence":p9.ref(root,range_path),
                 "contact_bridge":p9.ref(root,bridge_path),
                 "bare_dressed_equivalence":p9.ref(root,equiv_path),
                 "export_evidence":p9.ref(root,export_path),
                 "final_body_clothing_hashes":p9.final_identity_from_raw_and_export(root,raw,export_receipt),
                 "verifier":p9.ref(root,root/p9.HELPER),
                 "production_evaluator":p9.ref(root,root/p9.EVALUATOR),
                 "acceptance_spec":p9.ref(root,root/p9.ACCEPTANCE),
                 "source_git_commit":"b"*40,"generated_utc":"2026-10-03T12:00:00+00:00","issues":[]}
        return receipt,{"root":root,"candidate":candidate,"merged":merged,"raw":raw_path,"static":static_path,
                       "range":range_path,"export_manifest":export_manifest_path}

    def verify(self, root, receipt):
        with patch.object(p9.export_evidence,"verify",return_value={"candidate_sha256":receipt["candidate_sha256"]}),              patch.object(p9,"audit_candidate_set",return_value={"pass":True}):
            return p9.verify_receipt(root,receipt,receipt["candidate_sha256"])

    def test_complete_fixture_verifies_without_promoting(self):
        with tempfile.TemporaryDirectory() as td:
            receipt,ctx=self.fixture(Path(td))
            self.assertEqual(self.verify(ctx["root"],receipt),[])
            self.assertFalse(receipt["phase_complete"]);self.assertFalse(receipt["production_approved"])

    def test_production_target_drift_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            receipt,ctx=self.fixture(Path(td))
            group=p9.GROUPS[0];path=p9.ref_path(ctx["root"],receipt["production_evaluations"][group],"prod")
            data=json.loads(path.read_text());data["failure_count"]=1;data["status"]="FAIL";path.write_text(json.dumps(data))
            receipt["production_evaluations"][group]=p9.ref(ctx["root"],path)
            issues=self.verify(ctx["root"],receipt)
            self.assertTrue(any("production evaluation differs" in x or "zero-failure" in x for x in issues))

    def test_unresolved_range_contact_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            receipt,ctx=self.fixture(Path(td))
            path=ctx["range"];data=json.loads(path.read_text());data["classification"]["unclassified_findings"]=1
            data["classification"]["classification_complete"]=False;path.write_text(json.dumps(data))
            receipt["range_evidence"]=p9.ref(ctx["root"],path)
            issues=self.verify(ctx["root"],receipt)
            self.assertTrue(any("contact classification" in x for x in issues))

    def test_broken_static_range_lineage_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            receipt,ctx=self.fixture(Path(td))
            path=ctx["range"];data=json.loads(path.read_text());data["source_evidence"]=[];path.write_text(json.dumps(data))
            receipt["range_evidence"]=p9.ref(ctx["root"],path)
            issues=self.verify(ctx["root"],receipt)
            self.assertTrue(any("static dressed parent" in x for x in issues))

    def test_final_body_clothing_hash_inventory_is_exact(self):
        with tempfile.TemporaryDirectory() as td:
            receipt,ctx=self.fixture(Path(td))
            receipt["final_body_clothing_hashes"]["body_snapshot"]["sha256"]="f"*64
            issues=self.verify(ctx["root"],receipt)
            self.assertTrue(any("final body/clothing/export hash inventory differs" in x for x in issues))

    def test_candidate_mismatch_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            receipt,ctx=self.fixture(Path(td))
            receipt["candidate_sha256"]="c"*64
            issues=self.verify(ctx["root"],receipt)
            self.assertTrue(any("candidate differs" in x for x in issues))


if __name__=="__main__":
    unittest.main()
