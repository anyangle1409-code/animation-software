#!/usr/bin/env python3
"""Index the repository-backed skeleton review pack (GitHub-viewable) and verify every manifest hash.

Scans the shoulder-stage evidence sets (each has a manifest.json with files_sha256), re-hashes every file, classifies
each image/clip by coverage category and writes:
  ORIGINAL_V1_WORK/anatomy/audit/review_pack_index_v1.json
  ORIGINAL_V1_WORK/anatomy/audit/REVIEW_PACK_INDEX.md   (clickable GitHub links, start-here list)

  build_review_pack_index.py
"""
import hashlib, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit'
BLOB = 'https://github.com/anyangle1409-code/animation-software/blob/codex/whole-body-biomechanics-audit-20261007/'
SETS = [
    ('c001 shoulder proposal (vs a003)', AUD / 'candidates/shoulder_proposal_c001/review/manifest.json'),
    ('c002 ANSUR-height shoulder drop (FAILED closure; vs c001/a003)', AUD / 'candidates/shoulder_proposal_c002_ansur_height/review/manifest.json'),
    ('c003 coupled thorax+shoulder (vs a003/c001/c002)', AUD / 'candidates/shoulder_thorax_c003_ansur_coupled/review/manifest.json'),
    ('ANSUR acromion correspondence audit', AUD / 'shoulder_ansur_acromion_evidence/manifest.json'),
    ('movement clips: c001 isolated shoulder tests', AUD / 'runs/isolated_bone_only_c001_shoulder_proposal_002/clips/manifest.json'),
    ('movement clips: c003 isolated shoulder tests', AUD / 'runs/isolated_bone_only_c003_shoulder_thorax_001/clips/manifest.json'),
    ('movement clips: rib-sternum coupled inspiration (a003 vs c003)', AUD / 'runs/rib_sternum_coupling_c003_001/clips/manifest.json'),
    ('movement collision scan: hip adduction leg-through-leg (a003 vs c003)', AUD / 'movement_collision_scan/clips/manifest.json'),
    ('joint attachment scan: subtalar midfoot column split (a003 vs c003)', AUD / 'joint_attachment_scan/clips/manifest.json'),
]
CATS = [
    ('full_body', r'full_(front|back|left_side|right_side|front_left_three_quarter|front_right_three_quarter|back_left_three_quarter)'),
    ('shoulder_left', r'shoulder_left_(front|side|rear)|left_(front|side|rear)\.'),
    ('shoulder_right', r'shoulder_right_(front|side|rear)|right_(front|side|rear)\.'),
    ('axilla', r'axilla_(left|right)'),
    ('overhead', r'overhead'),
    ('upper_body', r'upper_body_'),
    ('poses', r'pose_|poses_'),
    ('comparison', r'before_after|four_way|sheet_'),
    ('movement_clip', r'\.gif$'),
    ('chart', r'chart_'),
]
REQUIRED = ['full_body', 'shoulder_left', 'shoulder_right', 'axilla', 'overhead', 'comparison', 'movement_clip', 'poses']


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build():
    sets, bad, cover = [], [], {c: 0 for c, _ in CATS}
    for title, man_path in SETS:
        man = json.loads(man_path.read_text())
        files = []
        for rel, h in sorted(man['files_sha256'].items()):
            ok = (ROOT / rel).exists() and sha(ROOT / rel) == h
            if not ok:
                bad.append(rel)
            cats = [c for c, rx in CATS if re.search(rx, rel)]
            for c in cats:
                cover[c] += 1
            files.append({'path': rel, 'sha256': h, 'hash_ok': ok, 'categories': cats})
        sets.append({'title': title, 'manifest': str(man_path.relative_to(ROOT)), 'manifest_sha256': sha(man_path),
                     'status_in_manifest': man.get('status') or man.get('note', '')[:80], 'files': files})
    return {'schema_version': 1, 'created': '2026-10-08', 'branch': 'codex/whole-body-biomechanics-audit-20261007',
            'sets': sets, 'file_count': sum(len(s['files']) for s in sets), 'hash_failures': bad,
            'coverage_counts': cover, 'required_categories_present': {c: cover[c] > 0 for c in REQUIRED},
            'note': 'All candidates are AUDIT proposals, NOT CANONICAL; no production asset is included.'}


def markdown(ix):
    L = ['# Skeleton review pack (shoulder stage): index', '',
         'Every image and clip below is in the repository, and its sha256 is verified against its manifest (`review_pack_index_v1.json`). All candidates are **audit proposals, not canonical**; nothing here is a production asset.', '',
         '## Start here', '']
    starts = [('c003: four-way left shoulder and axilla (a003 / c001 / c002 / c003)', 'candidates/shoulder_thorax_c003_ansur_coupled/review/sheets/sheet_four_way_shoulder_left.jpg'),
              ('c003: four-way right shoulder and axilla', 'candidates/shoulder_thorax_c003_ansur_coupled/review/sheets/sheet_four_way_shoulder_right.jpg'),
              ('c003: four-way full and upper body', 'candidates/shoulder_thorax_c003_ansur_coupled/review/sheets/sheet_four_way_body.jpg'),
              ('c003: four-way overhead', 'candidates/shoulder_thorax_c003_ansur_coupled/review/sheets/sheet_four_way_overhead.jpg'),
              ('c003: arm-raise clip, left (a003 vs c003)', 'runs/isolated_bone_only_c003_shoulder_thorax_001/clips/shoulder_complex_scapular_plane_left__rear.gif'),
              ('Rib–sternum breathing clip, side (a003 vs c003)', 'runs/rib_sternum_coupling_c003_001/clips/rib_sternum_coupled_inspiration__left.gif'),
              ('Acromion landmark audit chart', 'shoulder_ansur_acromion_evidence/chart_required_clavicle_elevation.png')]
    for t, p in starts:
        L.append(f'- [{t}]({BLOB}ORIGINAL_V1_WORK/anatomy/audit/{p})')
    L += ['', '## Coverage', '', '| Category | Files | Required present |', '|---|---|---|']
    for c, n in ix['coverage_counts'].items():
        L.append(f'| {c} | {n} | {"yes" if ix["required_categories_present"].get(c, True) else "**MISSING**"} |')
    L += ['', f'Total files: {ix["file_count"]}. Hash failures: {len(ix["hash_failures"])}.', '']
    eia = AUD / 'evidence_integrity/evidence_integrity_v1.json'
    if eia.exists():
        e = json.loads(eia.read_text()); rel = str(eia.relative_to(ROOT))
        L += ['## Repository-wide evidence integrity', '',
              f'Every recorded sha256 across all anatomy evidence JSON is re-checked by [`{rel}`]({BLOB}{rel}) '
              f'({e["hash_references_checked"]} references: ' + ', '.join(f'{k} {v}' for k, v in e['by_status'].items()) +
              f'; document references missing: {len(e["doc_missing_references"])}; orphans: '
              f'{sum(1 for x in e["orphan_candidates"] if x["kind"] == "ORPHAN")}). Nothing was rewritten; see the JSON for each flagged item.', '']
    for s in ix['sets']:
        L += [f'## {s["title"]}', '', f'Manifest: [`{s["manifest"]}`]({BLOB}{s["manifest"]})', '']
        for f in s['files']:
            L.append(f'- [{Path(f["path"]).name}]({BLOB}{f["path"]}) ({", ".join(f["categories"]) or "other"})')
        L.append('')
    return '\n'.join(L) + '\n'


def main():
    ix = build()
    (AUD / 'review_pack_index_v1.json').write_text(json.dumps(ix, indent=1) + '\n')
    (AUD / 'REVIEW_PACK_INDEX.md').write_text(markdown(ix))
    print(ix['file_count'], 'files', 'hash failures', len(ix['hash_failures']), ix['required_categories_present'])


if __name__ == '__main__':
    main()
