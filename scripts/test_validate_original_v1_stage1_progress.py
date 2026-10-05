"""Tests for fail-closed Stage 1 progress tracking."""
import copy,importlib.util
from pathlib import Path
import unittest

P=Path(__file__).with_name("validate_original_v1_stage1_progress.py")
S=importlib.util.spec_from_file_location("stage1_progress",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)

class Stage1ProgressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=mod.read(mod.PROGRESS); cls.g=mod.read(mod.GRAPH); cls.p=mod.read(mod.PACKAGES)

    def test_live_progress_valid(self):
        out=mod.validate(self.d,self.g,self.p)
        self.assertEqual(out["active_wave_id"],"shoulder_yoke_foundation")
        self.assertFalse(out["global_foundation_clear"])

    def test_next_action_is_global_diagnostics_before_repairs_clear(self):
        out=mod.next_action(self.d,self.g)
        self.assertEqual(out["action"],"complete_global_pre_repair_diagnostics")

    def test_shoulder_package_cannot_clear_before_global_foundation(self):
        bad=copy.deepcopy(self.d)
        row=next(x for x in bad["waves"] if x["id"]=="shoulder_yoke_foundation")
        row["package_statuses"][0]["state"]="CLEAR"
        row["package_statuses"][0]["repair_declaration_refs"]=["d.json"]
        row["package_statuses"][0]["repair_execution_record_refs"]=["e.json"]
        row["package_statuses"][0]["weights_only_evidence_refs"]=["w.json"]
        row["package_statuses"][0]["coupling_evidence_refs"]=["c.json"]
        row["package_statuses"][0]["surface_visual_review_refs"]=["v.json"]
        row["package_statuses"][0]["regression_refs"]=["r.json"]
        row["package_statuses"][0]["comparison_report_refs"]=["cmp.json"]
        bad["overall"]["packages_clear"]=1
        with self.assertRaisesRegex(ValueError,"before global foundation CLEAR"):
            mod.validate(bad,self.g,self.p)

    def test_wave_clear_requires_exit_evidence(self):
        bad=copy.deepcopy(self.d)
        g0=bad["waves"][0]; g0["state"]="CLEAR"; g0["exit_evidence_refs"]=[]
        bad["overall"]["waves_clear"]=1
        with self.assertRaisesRegex(ValueError,"CLEAR without exit evidence"):
            mod.validate(bad,self.g,self.p)

    def test_high_detail_cannot_be_enabled(self):
        bad=copy.deepcopy(self.d); bad["overall"]["high_detail_anatomy_allowed"]=True
        with self.assertRaisesRegex(ValueError,"high-detail anatomy"):
            mod.validate(bad,self.g,self.p)

if __name__=="__main__": unittest.main()
