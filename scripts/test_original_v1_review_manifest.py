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

    def test_published_compact_prefix_resolves_to_actual_source_and_tampering_stops(self):
        import original_v1_production_control as c
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);candidate=root/c.CAND/'HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r29.json'
            candidate.parent.mkdir(parents=True);candidate.write_text(json.dumps({'candidate_sha256':'a'*64}))
            source=root/c.RC/'shoulder_r29/render_source_manifest.json';source.parent.mkdir(parents=True)
            folder=root/c.CAND/'review/visual_r29';folder.mkdir(parents=True)
            image=folder/'shoulder__pose_press_top_front.png';image.write_bytes(b'test fixture only')
            capture={'protocol':'test fixture only'}
            source.write_text(json.dumps({'candidate_sha256':'a'*64,'images':[{'file':'pose_press_top_front.png','sha256':c.digest(image),'capture':capture}]}))
            packet={'candidate_revision':'r29','candidate_sha256':'a'*64,'candidate_manifest_sha256':c.digest(candidate),
                    'blocking':False,'production_approved':False,'owner_review':'pending',
                    'source_manifests':[{'path':source.relative_to(root).as_posix(),'sha256':c.digest(source)}],
                    'files':[{'output':image.relative_to(root).as_posix(),'source':(source.parent/'pose_press_top_front.png').relative_to(root).as_posix(),'sha256':c.digest(image),'capture':capture}]}
            (folder/'visual_review_manifest.json').write_text(json.dumps(packet))
            result=c.verified_review(root,'r29','a'*64,'visual')
            self.assertEqual(result['owner_review'],'pending');self.assertFalse(result['blocking'])
            image.write_bytes(b'tampered')
            with self.assertRaisesRegex(ValueError,'image hash'):c.verified_review(root,'r29','a'*64,'visual')

if __name__=='__main__':unittest.main()
