#!/usr/bin/env python3
"""Adversarial chirality regression tests; stdlib only, no Blender dependency."""
import copy
import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))
import anatomical_runtime_chirality_gate as gate


class ChiralityGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = {
            k: json.loads((ROOT / path).read_text())
            for k, path in gate.SOURCE.items()
        }

    def records_copy(self):
        r = copy.deepcopy(self.records)
        return r["fitted_skeleton"], r["runtime_skeleton"], r["alias_inventory"]

    def test_real_frozen_source_reports_six_crossed_aliases(self):
        result = gate.from_repository(ROOT)
        self.assertEqual(result["anchors_compared"], 6)
        self.assertEqual(result["crossed_count"], 6)
        self.assertEqual(result["status"], "BLOCK_RUNTIME_SIDE_BINDING")
        self.assertEqual(set(result["crossed_aliases"]), {
            "clavicle_left", "clavicle_right", "humerus_left", "humerus_right",
            "femur_left", "femur_right"})
        self.assertEqual(result["frame"]["audit_to_runtime"], "(x,y,z) -> (x,z,-y)")
        self.assertEqual(len(result["input_sha256"]), 3)

    def test_inputs_remain_read_only(self):
        a,b,c=self.records_copy()
        before=json.dumps([a,b,c],sort_keys=True)
        gate.inspect(a,b,c)
        self.assertEqual(json.dumps([a,b,c],sort_keys=True),before)

    def test_crossed_mapping_correction_is_diagnostic_not_approval(self):
        fit,rig,aliases=self.records_copy()
        by_id={a["anatomical_id"]:a for a in aliases["aliases"]}
        for a,r in gate.PROBES:
            by_id[a+"_left"]["current_rig"]=[r+"_r"]
            by_id[a+"_right"]["current_rig"]=[r+"_l"]
        report=gate.inspect(fit,rig,aliases)
        self.assertEqual(report["crossed_count"],0)
        self.assertEqual(report["status"],"EVIDENCE_ONLY_OWNER_DECISION_PENDING")
        self.assertFalse(report["owner_approval"])
        self.assertFalse(report["canonical_promotion"])
        self.assertFalse(report["runtime_mapping_changed"])

    def test_error_on_changed_fitted_frame(self):
        fit,rig,aliases=self.records_copy()
        fit["conventions"]["world"]="unknown handedness"
        with self.assertRaisesRegex(ValueError,"frame"):
            gate.inspect(fit,rig,aliases)

    def test_error_on_changed_runtime_frame(self):
        fit,rig,aliases=self.records_copy()
        rig["coordinate_system"]="mirror_unknown"
        with self.assertRaisesRegex(ValueError,"runtime frame"):
            gate.inspect(fit,rig,aliases)

    def test_error_on_source_side_binding_claim_change(self):
        fit,rig,aliases=self.records_copy()
        fit["conventions"]["runtime_side_binding"]={"left":"_l","right":"_r"}
        with self.assertRaisesRegex(ValueError,"binding changed"):
            gate.inspect(fit,rig,aliases)

    def test_error_on_unproven_anatomical_side(self):
        fit,rig,aliases=self.records_copy()
        # Swap source sides without changing identifiers; cannot silently accept.
        fit["bones"]["humerus_left"],fit["bones"]["humerus_right"]=(
            fit["bones"]["humerus_right"],fit["bones"]["humerus_left"])
        with self.assertRaisesRegex(ValueError,"side not established"):
            gate.inspect(fit,rig,aliases)

    def test_error_if_source_contains_nonfinite_coordinate(self):
        fit,rig,aliases=self.records_copy()
        fit["bones"]["femur_left"]["head_m"][0]=float("nan")
        with self.assertRaisesRegex(ValueError,"finite"):
            gate.inspect(fit,rig,aliases)

    def test_error_if_runtime_counterpart_missing(self):
        fit,rig,aliases=self.records_copy()
        rig["bones"]=[b for b in rig["bones"] if b["name"]!="thigh_r"]
        with self.assertRaisesRegex(ValueError,"Missing runtime"):
            gate.inspect(fit,rig,aliases)

    def test_proper_frame_conversion_with_two_bilateral_axes(self):
        self.assertEqual(gate.convert_audit_to_runtime([0,0,1]),(0.,1.,0.))
        self.assertEqual(gate.convert_audit_to_runtime([0,-1,0]),(0.,0.,1.))
        self.assertEqual(gate.convert_audit_to_runtime([1,0,0]),(1.,0.,0.))
        self.assertEqual(gate.cross((0,0,1),(0,-1,0)),(1,0,0))
        self.assertEqual(gate.cross((0,1,0),(0,0,1)),(1,0,0))

    def test_reject_nonfinite_or_boolean_vectors(self):
        for bad in ([True,0,0],[math.inf,0,0],[1,2],[1,2,3,4]):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    gate.vector(bad)


if __name__=="__main__":
    unittest.main()
