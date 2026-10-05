"""Tests for fail-closed human sweep contact classification."""
import hashlib,importlib.util,json,tempfile
from pathlib import Path
import unittest
P=Path(__file__).with_name("validate_original_v1_human_movement_sweep_contact.py")
S=importlib.util.spec_from_file_location("contact",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)

class SweepContactTests(unittest.TestCase):
    def fixture(self,root,sweep="loaded_hip_hinge"):
        req=mod.read(mod.REQ)["sweeps"][sweep]; csha="a"*64
        raw=root/"raw_contact.json"; raw.write_text(json.dumps({"candidate_sha256":csha,"measurements":[]}),encoding="utf-8")
        rows=[]
        for label,ar in req["samples"].items():
            domains={}
            for domain in ar.get("required_domains",[]):
                domains[domain]={"classification":ar["expected"],"raw_measurement_ref":f"raw_contact.json#{label}/{domain}","evidence_note":"fixture reviewed contact"}
            row={"label":label,"domains":domains}
            if "heel_state" in ar:
                row["heel_state_observed"]={
                  "CONTACT_OR_NEAR_SUPPORT":"CONTACT","RISING":"RISING","CLEAR":"CLEAR","RISING_OR_RETURNING":"RETURNING"
                }[ar["heel_state"]]
            rows.append(row)
        return {"schema_version":1,"status":"HUMAN_MOVEMENT_SWEEP_CONTACT_REPORT","production_approved":False,
                "candidate_revision":"r96","candidate_sha256":csha,"sweep_id":sweep,
                "raw_contact_evidence_refs":[{"path":raw.name,"sha256":hashlib.sha256(raw.read_bytes()).hexdigest(),"candidate_sha256":csha}],
                "samples":rows,"engineering_review":"PASS","owner_review":"PENDING"}

    def test_complete_contact_classification_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); out=mod.validate(self.fixture(root),root,True); self.assertEqual(out["engineering_review"],"PASS")

    def test_unexplained_defect_blocks_pass(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); d=self.fixture(root)
            domain=next(iter(d["samples"][0]["domains"])); d["samples"][0]["domains"][domain]["classification"]="UNEXPLAINED_DEFECT"
            with self.assertRaisesRegex(ValueError,"expected|blocking"): mod.validate(d,root,True)

    def test_raw_evidence_hash_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); d=self.fixture(root); (root/"raw_contact.json").write_text("changed",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"SHA mismatch"): mod.validate(d,root,True)

    def test_ankle_heel_state_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); d=self.fixture(root,"ankle_plantarflexion")
            row=next(x for x in d["samples"] if x["label"]=="heel_raise_end"); row["heel_state_observed"]="CONTACT"
            with self.assertRaisesRegex(ValueError,"heel state"): mod.validate(d,root,True)

if __name__=="__main__": unittest.main()
