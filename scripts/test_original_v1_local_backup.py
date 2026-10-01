"""Local Blend backup is collision-safe and hash-verified."""
from __future__ import annotations
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import original_v1_local_backup as b


class LocalBackupTests(unittest.TestCase):
    def test_collect_requires_matching_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/b.CAND).mkdir(parents=True)
            blend=root/b.CAND/"HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r30.blend";blend.write_bytes(b"blend")
            blend.with_suffix(".json").write_text(json.dumps({"candidate":blend.name,"candidate_sha256":b.digest(blend)}))
            rows=b.collect(root,{"current_candidate":"r30","incomplete_candidates":[]})
            self.assertEqual(rows[0]["blend_sha256"],b.digest(blend))

    def test_hash_mismatch_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/b.CAND).mkdir(parents=True)
            blend=root/b.CAND/"HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r30.blend";blend.write_bytes(b"blend")
            blend.with_suffix(".json").write_text(json.dumps({"candidate":blend.name,"candidate_sha256":"a"*64}))
            with self.assertRaisesRegex(ValueError,"identity differs"):
                b.collect(root,{"current_candidate":"r30","incomplete_candidates":[]})

    def test_selected_revisions_deduplicate_current(self):
        self.assertEqual(b.selected_revisions({"current_candidate":"r30","incomplete_candidates":["r30","r31"]}),["r30","r31"])


if __name__=="__main__":
    unittest.main()
