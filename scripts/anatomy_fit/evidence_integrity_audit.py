#!/usr/bin/env python3
"""Repository-backed evidence integrity audit (read-only; nothing is rewritten).

1. Hash references: every JSON under ORIGINAL_V1_WORK/anatomy is walked; each recorded sha256 that can be anchored to a
   file path is re-checked. Anchoring rules (no guessing beyond these):
     * {path: hash} maps (files_sha256, inputs_sha256, scripts, sha256_manifest.json, ...): key is the path;
     * {path: {'sha256': hash}} maps: key is the path;
     * a leaf 'X_sha256' with a sibling string 'X', 'X_path' or 'X_file': that sibling is the path;
     * a leaf 'sha256' with a sibling 'path' / 'file' / 'filepath' string: that sibling is the path.
   Paths resolve against the repository root, the JSON's directory, its parent, ORIGINAL_V1_WORK/anatomy and its audit/;
   absolute paths are mapped into the repository at the first ORIGINAL_V1_WORK/, scripts/ or docs/ component.
   Status: OK; STALE_HISTORICAL (file differs, but the recorded hash equals a committed earlier version of that path:
   evidence was recorded against a since-updated file); MISMATCH (no committed version matches); MISSING (in-repo path
   absent); OK_VIA_GZIP (only X.gz is committed and its decompressed content matches); ABSENT_BINARY_NOT_COMMITTED (a
   binary/source-data file - blend, stl, bin, osim, glb, ... - never committed under that name anywhere: hash is
   provenance only, unverifiable here; still flagged, never counted OK); EXTERNAL (outside the repository, e.g. scratch or system paths; unverifiable). Hashes without an anchor
   (e.g. a blend hash 'after' a run, digests) are counted as UNANCHORED, never graded.
2. Document references: backtick paths in the tracker/findings/review/handoff docs and REVIEW_PACK_INDEX.md must exist
   (brace lists {a,b} expanded; short 'audit/...' forms resolve under ORIGINAL_V1_WORK/anatomy).
   Sidecar '*.sha256' files ('<hash>  <name>') are checked against the named file or its committed .gz.
3. Orphans: evidence files under ORIGINAL_V1_WORK/anatomy/audit that no JSON, Markdown or script in the repository names
   by relative path or by file name (informational: a file named only through a directory listing is reported).

  evidence_integrity_audit.py --out JSON
"""
import argparse, gzip, hashlib, json, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
AUD = ANAT / 'audit'
HEX = re.compile(r'^[0-9a-f]{64}$')
DOCS = ['docs/COMPLETE_HUMAN_SKELETON_LIVE_TRACKER_20261007.md', 'docs/COMPLETE_SKELETON_FINDINGS_AND_VERIFICATION_20261007.md',
        'docs/CLAUDE_INDEPENDENT_REVIEW_20261008.md', 'docs/CLAUDE_WORK_SKELETON_INSPECTION_HANDOFF_20261008.md',
        'ORIGINAL_V1_WORK/anatomy/audit/REVIEW_PACK_INDEX.md']
MAX_JSON = 60e6
BINARY_EXT = {'.blend', '.stl', '.bin', '.osim', '.glb', '.fbx', '.zip', '.pdf', '.xlsx', '.obj'}
TRACKED_NAMES = {Path(x).name for x in subprocess.run(['git', '-C', str(ROOT), 'ls-files'], capture_output=True, text=True).stdout.split()}
_sha_cache = {}


def sha(p):
    p = Path(p)
    if p not in _sha_cache:
        h = hashlib.sha256()
        with open(p, 'rb') as f:
            for b in iter(lambda: f.read(1 << 20), b''):
                h.update(b)
        _sha_cache[p] = h.hexdigest()
    return _sha_cache[p]


def pathlike(s):
    return isinstance(s, str) and ('/' in s or re.search(r'\.[A-Za-z0-9]{1,6}$', s) is not None) and '\n' not in s and len(s) < 400


def anchors(o, out, ptr='', key=None):
    if isinstance(o, dict):
        for k, v in o.items():
            here = f'{ptr}/{k}'
            if isinstance(v, str) and HEX.match(v):
                if pathlike(k) and not k.endswith('_sha256'):
                    out.append((here, k, v))
                elif k.endswith('_sha256'):
                    base = k[:-7]
                    for sib in (base, base + '_path', base + '_file'):
                        if pathlike(o.get(sib)):
                            out.append((here, o[sib], v)); break
                    else:
                        out.append((here, None, v))
                elif k == 'sha256':
                    for sib in ('path', 'file', 'filepath'):
                        if pathlike(o.get(sib)):
                            out.append((here, o[sib], v)); break
                    else:
                        out.append((here, key if pathlike(key) else None, v))
                else:
                    out.append((here, None, v))
            else:
                anchors(v, out, here, k)
    elif isinstance(o, list):
        for i, x in enumerate(o):
            anchors(x, out, f'{ptr}[{i}]', key)


def resolve(p, jf):
    if p.startswith(('http://', 'https://')):
        return None, 'EXTERNAL'                       # a URL names an external (third-party) file by definition
    if p.startswith('/'):
        m = re.search(r'/((?:ORIGINAL_V1_WORK|scripts|docs)/.*)$', p)
        if not m:
            return None, 'EXTERNAL'
        p = m.group(1)
    bases = (jf.parent, ROOT, jf.parent.parent, ANAT, AUD) if '/' not in p else (ROOT, jf.parent, jf.parent.parent, ANAT, AUD)
    for base in bases:
        c = (base / p)
        try:
            c = c.resolve()
        except OSError:
            continue
        if c.is_file() and ROOT in c.parents:
            return c, None
    for base in bases:
        g = base / (p + '.gz')
        if g.is_file() and ROOT in g.resolve().parents:
            return g.resolve(), 'GZ'
    return None, 'MISSING'


def git_history_hashes(rel):
    try:
        revs = subprocess.run(['git', '-C', str(ROOT), 'log', '--format=%H', '--', rel], capture_output=True, text=True, timeout=120).stdout.split()
    except Exception:
        return {}
    out = {}
    for r in revs:
        b = subprocess.run(['git', '-C', str(ROOT), 'show', f'{r}:{rel}'], capture_output=True, timeout=300).stdout
        if b:
            out.setdefault(hashlib.sha256(b).hexdigest(), r)
    return out


def hash_refs():
    refs, unanchored, by_status = [], 0, {}
    for jf in sorted(ANAT.rglob('*.json')):
        if jf.stat().st_size > MAX_JSON or 'evidence_integrity' in jf.parts:      # never grade this audit's own output
            continue
        try:
            d = json.loads(jf.read_text())
        except Exception as e:
            refs.append({'json': str(jf.relative_to(ROOT)), 'status': 'UNREADABLE_JSON', 'error': str(e)[:200]}); continue
        found = []; anchors(d, found)
        for ptr, p, h in found:
            if p is None:
                unanchored += 1; continue
            f, st = resolve(p, jf)
            r = {'json': str(jf.relative_to(ROOT)), 'pointer': ptr, 'path': p, 'recorded': h}
            if f is not None and st == 'GZ':
                r['resolved'] = str(f.relative_to(ROOT))
                actual = hashlib.sha256(gzip.decompress(f.read_bytes())).hexdigest()
                st = 'OK_VIA_GZIP' if actual == h else 'MISMATCH'
                if actual != h:
                    r['actual'] = actual
            elif f is not None:
                r['resolved'] = str(f.relative_to(ROOT))
                actual = sha(f)
                if actual == h:
                    st = 'OK'
                else:
                    hist = git_history_hashes(r['resolved'])
                    st = 'STALE_HISTORICAL' if h in hist else 'MISMATCH'
                    r['actual'] = actual
                    if h in hist:
                        r['matching_commit'] = hist[h]
                    else:
                        r['note'] = f'no committed version of {r["resolved"]} ({len(hist)} checked) has the recorded hash: recorded from an uncommitted working copy'
            elif st == 'MISSING' and Path(p).suffix.lower() in BINARY_EXT and Path(p).name not in TRACKED_NAMES:
                st = 'ABSENT_BINARY_NOT_COMMITTED'
            r['status'] = st
            by_status[st] = by_status.get(st, 0) + 1
            refs.append(r)
    return refs, unanchored, by_status


def sidecars():
    """'<hash>  <name>' sidecar files (*.sha256): the named file, or its committed .gz (decompressed), next to the sidecar."""
    out = []
    for rel in subprocess.run(['git', '-C', str(ROOT), 'ls-files', '*.sha256'], capture_output=True, text=True).stdout.split():
        sc = ROOT / rel
        for line in sc.read_text().splitlines():
            m = re.match(r'^([0-9a-f]{64})\s+\*?(\S+)$', line.strip())
            if not m:
                continue
            h, name = m.groups(); tgt = sc.parent / Path(name).name
            if tgt.is_file():
                st = 'OK' if sha(tgt) == h else 'MISMATCH'
            elif Path(str(tgt) + '.gz').is_file():
                st = 'OK_VIA_GZIP' if hashlib.sha256(gzip.decompress(Path(str(tgt) + '.gz').read_bytes())).hexdigest() == h else 'MISMATCH'
            else:
                st = 'MISSING'
            out.append({'sidecar': rel, 'target': name, 'recorded': h, 'status': st})
    return out


def doc_refs():
    """Backtick file references in the docs. EXISTS: resolves from the repository root, ORIGINAL_V1_WORK/anatomy, its audit/ or
    scripts/; CONTEXT_RELATIVE: a short form (e.g. 'review/sheets/x.jpg' under a candidate heading) that matches the end of
    exactly one or more tracked paths; MISSING: neither. Abbreviated forms containing an ellipsis are skipped."""
    tracked = subprocess.run(['git', '-C', str(ROOT), 'ls-files'], capture_output=True, text=True).stdout.split()
    out, n = [], 0
    for d in DOCS:
        txt = (ROOT / d).read_text()
        for tok in sorted(set(re.findall(r'`([^`\s]+)`', txt))):
            if '/' not in tok or '\u2026' in tok or '...' in tok or tok.startswith(('http', '--')) or any(ch in tok for ch in '*<>=()'):
                continue
            m = re.search(r'\{([^{}]+)\}', tok)
            cands = [tok[:m.start()] + x + tok[m.end():] for x in m.group(1).split(',')] if m else [tok]
            for c in cands:
                c = c.rstrip('.,:;')
                if not re.search(r'\.[A-Za-z0-9]{1,6}$', c) and not c.endswith('/'):
                    continue                                             # not a file reference (e.g. a key path)
                n += 1
                if any((b / c).exists() for b in (ROOT, ANAT, AUD, ROOT / 'scripts', ROOT / 'scripts/anatomy_fit')):
                    continue
                hits = [t for t in tracked if ('/' + t).endswith('/' + c) or ('/' + c in '/' + t and c.endswith('/'))]
                out.append({'doc': d, 'reference': c, 'status': 'CONTEXT_RELATIVE' if hits else 'MISSING', 'matches': sorted(hits)[:4], 'match_count': len(hits)})
    return n, out


def orphans():
    corpus = []
    for pat in ('**/*.json', '**/*.md', '**/*.py', '**/*.txt'):
        for f in ROOT.glob(pat):
            if '.git' in f.parts or f.stat().st_size > MAX_JSON or 'evidence_integrity' in f.parts or f.name == 'test_evidence_integrity_audit.py':
                continue                                         # this audit's own outputs/tests would name every orphan
            try:
                corpus.append(f.read_text(errors='ignore'))
            except OSError:
                pass
    blob = '\n'.join(corpus)
    tokens = set(re.findall(r'[\w.\-/]+', blob))
    for pre, alts, post in re.findall(r'([\w.\-/]*)\{([\w.\-,]+)\}([\w.\-/]*)', blob):   # brace lists, e.g. dir/{a003,c003}.json
        tokens |= {pre + a + post for a in alts.split(',')}
    names = {t.rsplit('/', 1)[-1] for t in tokens}
    tracked = subprocess.run(['git', '-C', str(ROOT), 'ls-files', 'ORIGINAL_V1_WORK/anatomy/audit'], capture_output=True, text=True).stdout.split()
    out = []
    for rel in tracked:
        name = Path(rel).name
        if name in ('manifest.json', 'README.md', 'sha256_manifest.json') or name.endswith('.sha256') or name in names \
                or (name.endswith('.gz') and name[:-3] in names):
            continue
        d = ROOT / rel
        documented = any((q / 'README.md').is_file() or (q / 'manifest.json').is_file() for q in list(d.parents)[:3] if AUD in q.parents or q == AUD)
        out.append({'path': rel, 'kind': 'UNNAMED_IN_DOCUMENTED_RUN_DIRECTORY' if documented else 'ORPHAN'})
    return out


def audit():
    refs, unanchored, by_status = hash_refs(); dr = doc_refs(); sc = sidecars()
    bad = [r for r in refs if r['status'] not in ('OK', 'OK_VIA_GZIP', 'EXTERNAL')]
    return {'hash_references_checked': len(refs), 'unanchored_hashes_not_graded': unanchored, 'by_status': dict(sorted(by_status.items())),
            'non_ok': bad, 'external': sorted({r['path'] for r in refs if r['status'] == 'EXTERNAL'}),
            'sidecar_files': sc,
            'doc_references_checked': dr[0], 'doc_references_unresolved_from_roots': dr[1],
            'doc_missing_references': [x for x in dr[1] if x['status'] == 'MISSING'], 'orphan_candidates': orphans()}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); o = ap.parse_args()
    r = audit()
    Path(o.out).write_text(json.dumps({'schema_version': 1, 'created': '2026-10-09', 'status': 'READ_ONLY_INTEGRITY_AUDIT_NOTHING_REWRITTEN', **r}, indent=1) + '\n')
    print({k: r[k] for k in ('hash_references_checked', 'unanchored_hashes_not_graded', 'by_status')})
    for x in r['non_ok']:
        print(' ', x['status'], x['json'], x['pointer'], x.get('resolved', x['path']))
    print('doc missing', len(r['doc_missing_references']), r['doc_missing_references'][:20])
    print('orphans', len(r['orphan_candidates']), r['orphan_candidates'][:40])


if __name__ == '__main__':
    main()
