"""Evidence integrity audit: committed result pinned and re-verified live (any later change to accepted evidence, a
manifest or a referenced file shows up as a status-count change), and every detector proven on a synthetic git repository
(OK, MISMATCH, STALE_HISTORICAL, MISSING, OK_VIA_GZIP, ABSENT_BINARY_NOT_COMMITTED, EXTERNAL, sidecars, doc refs, orphans)."""
import gzip, hashlib, json, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit'))
import evidence_integrity_audit as e  # noqa: E402

OUT = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/evidence_integrity/evidence_integrity_v1.json'


def h(b):
    return hashlib.sha256(b).hexdigest()


class Committed(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads(OUT.read_text())

    def test_pinned_findings(self):
        d = self.d
        self.assertEqual(d['status'], 'READ_ONLY_INTEGRITY_AUDIT_NOTHING_REWRITTEN')
        mism = [r for r in d['non_ok'] if r['status'] == 'MISMATCH']
        self.assertEqual(len(mism), 12)
        for r in mism:                                       # only early isolated-run script provenance (uncommitted working copies)
            self.assertRegex(r['json'], r'audit/runs/isolated_bone_only_0(0\d|1[01])/isolated_report.json$')
            self.assertTrue(r['pointer'].startswith('/provenance/scripts/'))
            self.assertIn('uncommitted working copy', r['note'])
        self.assertEqual([r['path'] for r in d['non_ok'] if r['status'] == 'MISSING'], ['atlas.json'])
        self.assertEqual(d['doc_missing_references'], [])
        self.assertTrue(all(x['status'] == 'OK_VIA_GZIP' for x in d['sidecar_files']) and len(d['sidecar_files']) == 2)
        self.assertEqual(sorted(x['path'] for x in d['orphan_candidates'] if x['kind'] == 'ORPHAN')[:2],
                         ['ORIGINAL_V1_WORK/anatomy/audit/runs/isolated_bone_only_001/crosscheck_expectations.json',
                          'ORIGINAL_V1_WORK/anatomy/audit/runs/isolated_bone_only_001/crosscheck_plan.json'])

    def test_live_reverification_matches_committed(self):
        refs, unanchored, by_status = e.hash_refs()
        committed = dict(self.d['by_status'])
        for k in ('MISMATCH', 'MISSING', 'ABSENT_BINARY_NOT_COMMITTED'):
            self.assertLessEqual(by_status.get(k, 0), committed.get(k, 0), k)
        # every non-OK reference must already be recorded, or be an inherited duplicate of a recorded one (same pointer, same
        # recorded hash, same status - e.g. a derived candidate copying its parent's provenance), or an EXTERNAL scratch blend
        known = {(r['json'], r['pointer']) for r in self.d['non_ok']}
        inherited = {(r['pointer'], r['recorded'], r['status']) for r in self.d['non_ok']}
        for r in refs:
            if r['status'] in ('OK', 'OK_VIA_GZIP', 'EXTERNAL') or (r['json'], r['pointer']) in known:
                continue
            self.assertIn((r['pointer'], r['recorded'], r['status']), inherited, (r['json'], r['pointer'], r['status']))
        self.assertGreaterEqual(by_status['OK'], committed['OK'])
        self.assertEqual([x for x in e.doc_refs()[1] if x['status'] == 'MISSING'], [])


class Mutations(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); R = Path(self.tmp.name)
        self.saved = {k: getattr(e, k) for k in ('ROOT', 'ANAT', 'AUD', 'DOCS', 'TRACKED_NAMES')}
        e._sha_cache.clear()
        A = R / 'ORIGINAL_V1_WORK/anatomy'; U = A / 'audit/runs/x'; U.mkdir(parents=True); (R / 'docs').mkdir()
        git = lambda *a: subprocess.run(['git', '-C', str(R), *a], check=True, capture_output=True)
        git('init', '-q'); git('config', 'user.email', 't@t'); git('config', 'user.name', 't')
        (U / 'stale.txt').write_text('v1'); git('add', '-A'); git('commit', '-qm', 'v1')
        (U / 'stale.txt').write_text('v2')
        (U / 'ok.txt').write_text('ok'); (U / 'tampered.txt').write_text('changed')
        (U / 'big.json.gz').write_bytes(gzip.compress(b'payload'))
        (U / 'data.json.sha256').write_text(h(b'payload') + '  big.json\n')
        (U / 'stray.txt').write_text('nobody names me')
        man = {'files_sha256': {'ok.txt': h(b'ok'), 'tampered.txt': h(b'original'), 'stale.txt': h(b'v1'), 'gone.txt': h(b'x'),
                                'big.json': h(b'payload'), 'model.blend': h(b'b'), '/tmp/elsewhere.blend': h(b'c'), 'https://example.org/src/mesh.vtp': h(b'd')}}
        (U / 'manifest.json').write_text(json.dumps(man))
        (U / 'data.json.sha256').write_text(h(b'payload') + '  big.json\n')
        (R / 'docs/d.md').write_text('see `audit/runs/x/ok.txt` and `audit/runs/x/absent.json` and `x/ok.txt`\n')
        git('add', '-A'); git('commit', '-qm', 'v2')
        e.ROOT, e.ANAT, e.AUD, e.DOCS = R, A, A / 'audit', ['docs/d.md']
        e.TRACKED_NAMES = {Path(x).name for x in git('ls-files').stdout.decode().split()}

    def tearDown(self):
        for k, v in self.saved.items():
            setattr(e, k, v)
        e._sha_cache.clear(); self.tmp.cleanup()

    def test_every_status_detected(self):
        refs, _, by = e.hash_refs()
        st = {Path(r['path']).name: r['status'] for r in refs}
        self.assertEqual(st, {'ok.txt': 'OK', 'tampered.txt': 'MISMATCH', 'stale.txt': 'STALE_HISTORICAL', 'gone.txt': 'MISSING',
                              'big.json': 'OK_VIA_GZIP', 'model.blend': 'ABSENT_BINARY_NOT_COMMITTED', 'elsewhere.blend': 'EXTERNAL', 'mesh.vtp': 'EXTERNAL'})

    def test_sidecar_doc_and_orphan(self):
        self.assertEqual([x['status'] for x in e.sidecars()], ['OK_VIA_GZIP'])
        Path(e.AUD / 'runs/x/big.json.gz').write_bytes(gzip.compress(b'tampered'))
        self.assertEqual([x['status'] for x in e.sidecars()], ['MISMATCH'])
        n, refs = e.doc_refs()
        self.assertEqual({x['reference']: x['status'] for x in refs}, {'audit/runs/x/absent.json': 'MISSING', 'x/ok.txt': 'CONTEXT_RELATIVE'})
        self.assertIn('ORIGINAL_V1_WORK/anatomy/audit/runs/x/stray.txt', [x['path'] for x in e.orphans()])


if __name__ == '__main__':
    unittest.main()
