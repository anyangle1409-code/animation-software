"""Local Blend inventory checks identity without mutating files."""
from __future__ import annotations
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import original_v1_blend_inventory as b


class BlendInventoryTests(unittest.TestCase):
    def setup_root(self,root):
        (root/b.CAND).mkdir(parents=True)
        (root/"ORIGINAL_V1_CANDIDATE_LEDGER.json").write_text(json.dumps({"candidates":[]}))
        return {"current_candidate":"r30","incomplete_candidates":[]}

    def test_matching_manifest_identity(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);state=self.setup_root(root)
            blend=root/b.CAND/"HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r30.blend";blend.write_bytes(b"blend")
            sha=b.digest(blend)
            blend.with_suffix(".json").write_text(json.dumps({"candidate":blend.name,"candidate_sha256":sha}))
            with patch.object(b,"build",return_value=(state,None)):
                result=b.inventory(root)
            self.assertEqual(result["rows"][0]["status"],"IDENTITY_VERIFIED")
            self.assertTrue(result["current_blend_present"])

    def test_missing_current_blend_is_gap(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);state=self.setup_root(root)
            with patch.object(b,"build",return_value=(state,None)):
                result=b.inventory(root)
            self.assertEqual(result["status"],"LOCAL_IDENTITY_GAPS")
            self.assertIn("r30",result["missing_expected_revisions"])

    def test_missing_manifest_is_gap(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);state=self.setup_root(root)
            (root/b.CAND/"HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r30.blend").write_bytes(b"blend")
            with patch.object(b,"build",return_value=(state,None)):
                result=b.inventory(root)
            self.assertEqual(result["status"],"LOCAL_IDENTITY_GAPS")

    def test_manifest_hash_mismatch_is_gap(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);state=self.setup_root(root)
            blend=root/b.CAND/"HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r30.blend";blend.write_bytes(b"blend")
            blend.with_suffix(".json").write_text(json.dumps({"candidate":blend.name,"candidate_sha256":"a"*64}))
            with patch.object(b,"build",return_value=(state,None)):
                result=b.inventory(root)
            self.assertEqual(result["rows"][0]["status"],"MANIFEST_HASH_MISMATCH")


if __name__=="__main__":
    unittest.main()
