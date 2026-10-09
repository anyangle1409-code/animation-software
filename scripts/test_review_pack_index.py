"""Review-pack index: reproducible, every indexed file present with matching sha256, all required categories covered."""
import json, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit'))
import build_review_pack_index as m  # noqa: E402

IX = json.loads((ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/review_pack_index_v1.json').read_text())


class ReviewPack(unittest.TestCase):
    def test_reproduces_and_hashes(self):
        self.assertEqual(IX, json.loads(json.dumps(m.build())))
        self.assertEqual(IX['hash_failures'], [])
        self.assertTrue(all(f['hash_ok'] for s in IX['sets'] for f in s['files']))

    def test_required_coverage(self):
        self.assertTrue(all(IX['required_categories_present'].values()), IX['required_categories_present'])
        self.assertGreaterEqual(IX['coverage_counts']['movement_clip'], 6)

    def test_markdown_links_resolve_to_repo_files(self):
        md = (ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/REVIEW_PACK_INDEX.md').read_text()
        for line in md.splitlines():
            if m.BLOB in line:
                rel = line.split(m.BLOB, 1)[1].split(')', 1)[0]
                self.assertTrue((ROOT / rel).exists(), rel)


if __name__ == '__main__':
    unittest.main()
