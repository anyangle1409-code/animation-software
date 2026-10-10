#!/usr/bin/env python3
"""Source hash and strict no-production-asset-change tests for Blender CT prep."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(HERE/"anatomy_fit"))
from nlm_ct_blender_six_source_prep import original_six_source_rows,prepare,SIX
from nlm_ct_laptop_review import DEFAULT_BUNDLE

BUNDLE=json.loads(DEFAULT_BUNDLE.read_text())
SIX_DOC=json.loads(SIX.read_text())


class BlenderOriginalSixPreflight(unittest.TestCase):
    def test_cross_manifest_matches_all_six_original_scanner_images_and_headers(self):
        rows=original_six_source_rows(BUNDLE,SIX_DOC)
        self.assertEqual([r["source_id"] for r in rows],[
            "cvm1749f","cvm1752f","cvm1755f","cvm1797f","cvm1800f","cvm1803f"])
        self.assertEqual([r["scanner_centre_RAS_mm"][2] for r in rows],
                         [-357,-360,-363,-405,-408,-411])
        self.assertTrue(all(r["source_png_bytes"]>100_000 for r in rows))

    def test_tampered_secondary_original_manifest_fails(self):
        changed=json.loads(json.dumps(SIX_DOC))
        changed["exact_png_and_scanner_header_sha256"][0]["png_sha256"]="0"*64
        with self.assertRaises(ValueError):
            original_six_source_rows(BUNDLE,changed)
        changed=json.loads(json.dumps(BUNDLE))
        changed["series"][0]["slices"][5]["source_png_sha256"]="0"*64
        with self.assertRaises(ValueError):
            original_six_source_rows(changed,SIX_DOC)

    def test_six_source_preflight_runs_without_blender_or_any_retroactive_scene_change(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"private_no_model"
            callback=Mock(return_value=(2,0))
            result=prepare(root,downloader=callback)
            self.assertEqual(callback.call_count,6)
            self.assertEqual(result["original_six_verified_source_count"],6)
            self.assertEqual(result["files_new"],12)
            self.assertEqual(result["files_reused"],0)
            self.assertTrue(Path(result["private_ct_dir"]).is_dir())
            self.assertFalse(result["accepted_skeleton_or_model_modified"])
            self.assertFalse(result["scanner_to_HGPT_world_registered"])
            self.assertFalse(result["canonical_promotion_allowed"])

    def test_symlink_private_base_rejected_before_writing(self):
        with tempfile.TemporaryDirectory() as td:
            real=Path(td)/"real";real.mkdir()
            link=Path(td)/"alias"
            link.symlink_to(real,target_is_directory=True)
            with self.assertRaisesRegex(ValueError,"symlink"):
                prepare(link,downloader=Mock())
            self.assertEqual(list(real.iterdir()),[])


if __name__=="__main__":
    unittest.main()
