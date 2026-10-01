import base64
import importlib
import json
from pathlib import Path
import tempfile
import unittest

class ReviewTests(unittest.TestCase):
    def test_source_candidate_hash_required(self):
        c=importlib.import_module('collect_original_v1_review_images')
        self.assertTrue(hasattr(c,'verify_source'),'render source identity validation missing')
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'render_source_manifest.json'
            p.write_text(json.dumps({'candidate_sha256':'a'*64,'images':[]}))
            with self.assertRaisesRegex(ValueError,'candidate'):c.verify_source(p,'b'*64)
    def test_wrong_image_digest_refused(self):
        c=importlib.import_module('collect_original_v1_review_images')
        self.assertTrue(hasattr(c,'verify_source'),'render source identity validation missing')
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'real.png').write_bytes(b'actual render bytes')
            (p/'render_source_manifest.json').write_text(json.dumps({'candidate_sha256':'a'*64,
                'images':[{'file':'real.png','sha256':'b'*64,'capture':{}}]}))
            with self.assertRaisesRegex(ValueError,'image'):c.verify_source(p/'render_source_manifest.json','a'*64)
    def test_comparison_embeds_only_real_images_and_flags_mismatch(self):
        self.assertTrue((Path(__file__).parent/'build_original_v1_comparison_boards.py').exists(),'comparison board generator missing')
        c=importlib.import_module('build_original_v1_comparison_boards')
        svg,matched=c.board_svg('r28','r29',b'real-before',b'real-after',{'scale':1},{'scale':2},'palm')
        self.assertIn(base64.b64encode(b'real-before').decode(),svg)
        self.assertIn(base64.b64encode(b'real-after').decode(),svg)
        self.assertFalse(matched)
        self.assertIn('CAPTURE SETTINGS DIFFER',svg)
if __name__=='__main__':unittest.main()
