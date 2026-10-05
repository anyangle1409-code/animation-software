"""Tests for weights-only contract and candidate acceptance."""
import copy,importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

P1=Path(__file__).with_name("validate_original_v1_weights_only_contract.py")
S1=importlib.util.spec_from_file_location("wo_contract",P1); contract=importlib.util.module_from_spec(S1); S1.loader.exec_module(contract)

P2=Path(__file__).with_name("validate_original_v1_weights_only_acceptance.py")
S2=importlib.util.spec_from_file_location("wo_accept",P2); accept=importlib.util.module_from_spec(S2); S2.loader.exec_module(accept)

class WeightsOnlyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=contract.read(contract.CONTRACT); cls.t=contract.read(contract.TEMPLATE)
        cls.m=contract.read(contract.MASTER); cls.cm=contract.read(contract.COUPLING)

    def test_live_contract_valid(self):
        out=contract.validate(self.c,self.t,self.m,self.cm)
        self.assertEqual(out["regions"],12)

    def fixture(self):
        d=copy.deepcopy(self.t)
        d["status"]="WEIGHTS_ONLY_ACCEPTANCE_IN_PROGRESS"
        d["candidate_revision"]="r96"; d["candidate_sha256"]="a"*64; d["source_branch"]="fixture"
        contact={x["id"]:bool(x.get("contact_applicable")) for x in self.c["regions"]}
        for row in d["regions"]:
            row["state"]="CLEAR"; row["evidence_refs"]=["weights.json","renders.json"]
            for k in row["checks"]:
                row["checks"][k]=True if k!="contact_load_path_if_applicable" else (True if contact[row["id"]] else None)
        return d

    def test_all_regions_can_clear_only_with_full_checks(self):
        out=accept.validate(self.fixture(),self.c,True)
        self.assertEqual(out["clear"],12)

    def test_clear_without_return_reversibility_fails(self):
        bad=self.fixture(); bad["regions"][0]["checks"]["return_reversibility"]=False
        with self.assertRaisesRegex(ValueError,"return_reversibility"):
            accept.validate(bad,self.c)

    def test_contact_region_requires_load_path(self):
        bad=self.fixture()
        row=next(x for x in bad["regions"] if x["id"]=="forearm_wrist")
        row["checks"]["contact_load_path_if_applicable"]=False
        with self.assertRaisesRegex(ValueError,"contact/load"):
            accept.validate(bad,self.c)

    def test_not_run_region_blocks_exit(self):
        bad=self.fixture(); bad["regions"][0]["state"]="NOT_RUN"
        with self.assertRaisesRegex(ValueError,"exit blocked"):
            accept.validate(bad,self.c,True)

if __name__=="__main__": unittest.main()
