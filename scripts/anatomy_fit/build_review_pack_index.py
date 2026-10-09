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

# Current-status handoff (documentation only). Every path is checked to exist so a stale link fails the build/test.
HANDOFF_PATHS = [
    ('Handover: independent verification (c004 audit, defect register, renders)', 'docs/CLAUDE_SKELETON_INDEPENDENT_VERIFICATION_20261009.md'),
    ('Handover: anatomical development (spine/trunk, knee, hip, grip, shoulder rhythm, PR #12 review, erratum, T001 summary)', 'docs/CLAUDE_ANATOMICAL_DEVELOPMENT_20261009.md'),
    ('Live tracker (integration checkpoint at the end)', 'docs/COMPLETE_HUMAN_SKELETON_LIVE_TRACKER_20261007.md'),
    ('Readiness gates (0 READY / 9 PARTIAL / 3 BLOCKED)', 'ORIGINAL_V1_WORK/anatomy/canonical_freeze_readiness_v1.json'),
    ('c004 current audit candidate record', 'ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json'),
    ('c004 isolated movement run (135 sweeps)', 'ORIGINAL_V1_WORK/anatomy/audit/runs/isolated_bone_only_c004_arm_inputs_001/isolated_report.json'),
    ('c004 skeleton-only Blender renders (28 views)', 'ORIGINAL_V1_WORK/anatomy/audit/claude_independent_review_20261009/skeleton_only_renders_c004/README.md'),
    ('c004 annotated Blender renders (22 views, camera-checked)', 'ORIGINAL_V1_WORK/anatomy/audit/claude_independent_review_20261009/annotated_renders_c004/README.md'),
    ('Defect register (30 entries)', 'ORIGINAL_V1_WORK/anatomy/audit/claude_independent_review_20261009/skeleton_defect_register_v1.json'),
    ('Defect register update (U5, U10, U11, L3, L4, H10)', 'ORIGINAL_V1_WORK/anatomy/audit/claude_anatomical_development_20261009/defect_register_update_v1.json'),
    ('Bone-by-bone audit (206 bones)', 'ORIGINAL_V1_WORK/anatomy/audit/claude_independent_review_20261009/bone_by_bone_audit_v1.json'),
    ('Spine column length discriminator (thoracic source A rejected)', 'ORIGINAL_V1_WORK/anatomy/audit/claude_anatomical_development_20261009/spine_column_length_discriminator_v1.json'),
    ('Trunk vertical closure on c004 (IJ row superseded by erratum)', 'ORIGINAL_V1_WORK/anatomy/audit/claude_anatomical_development_20261009/trunk_vertical_closure_c004_v1.json'),
    ('Spine sagittal diagnostic (coordinate diagram, not a render)', 'ORIGINAL_V1_WORK/anatomy/audit/claude_anatomical_development_20261009/spine_sagittal_diagnostic.jpg'),
    ('P003 disc re-partition: REJECTED (rib levels)', 'ORIGINAL_V1_WORK/anatomy/audit/proposals/p003_spine_disc_repartition_rejected/README.md'),
    ('Follower verification on c004: patella ratio and shoulder rhythm (expected vs observed, continuity, symmetry, clearance)', 'ORIGINAL_V1_WORK/anatomy/audit/claude_anatomical_development_20261009/follower_verification_c004_v1.json'),
    ('Follower source matrix: patellar path and clavicle elevation (conflicts; E-PAT-1 proposed, E-CLAV-1 unresolved)', 'ORIGINAL_V1_WORK/anatomy/audit/claude_anatomical_development_20261009/follower_source_matrix_v1.json'),
    ('Patellar tracking analysis (L3)', 'ORIGINAL_V1_WORK/anatomy/audit/claude_anatomical_development_20261009/patellar_tracking_c004_v1.json'),
    ('Knee render: static patella vs sourced follower (diagnostic, follower not installed)', 'ORIGINAL_V1_WORK/anatomy/audit/claude_anatomical_development_20261009/renders_knee_patella/knee_patella_static_vs_follower.jpg'),
    ('Hand-thigh start-posture analysis (H6)', 'ORIGINAL_V1_WORK/anatomy/audit/claude_anatomical_development_20261009/hand_thigh_start_posture_c004_v1.json'),
    ('Hip-rotation start-posture analysis (L7)', 'ORIGINAL_V1_WORK/anatomy/audit/claude_anatomical_development_20261009/hip_rotation_start_posture_c004_v1.json'),
    ('Hip adduction start-posture analysis (L4)', 'ORIGINAL_V1_WORK/anatomy/audit/claude_anatomical_development_20261009/hip_adduction_start_posture_c004_v1.json'),
    ('Clavicle elevation gap (U3)', 'ORIGINAL_V1_WORK/anatomy/audit/claude_anatomical_development_20261009/clavicle_elevation_gap_c004_v1.json'),
    ('Grip capacity c004 / P001 (H10, no defect)', 'ORIGINAL_V1_WORK/anatomy/audit/claude_anatomical_development_20261009/grip_capacity_c004_v1.json'),
    ('Bone geometry specification (8 regions; none ready)', 'ORIGINAL_V1_WORK/anatomy/audit/claude_anatomical_development_20261009/bone_geometry_specification_v1.json'),
    ('PR #12 contract probe', 'ORIGINAL_V1_WORK/anatomy/audit/claude_anatomical_development_20261009/pr12_contract_probe_v1.json'),
    ('EXPERIMENTAL P001 metacarpals M2-M4 (diagnostic only)', 'ORIGINAL_V1_WORK/anatomy/audit/proposals/p001_metacarpal_m2_m4/README.md'),
    ('EXPERIMENTAL P001 before/after hand renders', 'ORIGINAL_V1_WORK/anatomy/audit/proposals/p001_metacarpal_m2_m4/before_after/manifest.json'),
    ('EXPERIMENTAL T001 coupled trunk rebuild (README, checks, open problems)', 'ORIGINAL_V1_WORK/anatomy/audit/experiments/t001_coupled_trunk/README.md'),
    ('EXPERIMENTAL T001 outcome audit (independent checks vs c004)', 'ORIGINAL_V1_WORK/anatomy/audit/experiments/t001_coupled_trunk/checks/outcome_audit.json'),
    ('EXPERIMENTAL T001 movement comparison vs c004', 'ORIGINAL_V1_WORK/anatomy/audit/experiments/t001_coupled_trunk/checks/run_comparison_vs_c004.json'),
    ('EXPERIMENTAL T001 isolated movement run', 'ORIGINAL_V1_WORK/anatomy/audit/runs/isolated_bone_only_t001_coupled_trunk_001/isolated_report.json'),
    ('c005 blocker: hand-input source rebuild (no defensible c005)', 'ORIGINAL_V1_WORK/anatomy/audit/hand_input_audit/hand_input_source_rebuild_v1.json'),
    ('Fingertip endpoint evidence (Work)', 'ORIGINAL_V1_WORK/anatomy/audit/work_hand_tip_context_20261009/a003_tip_length_context.json'),
]
T001_RENDERS = ['body_left', 'body_front', 'spine_left', 'spine_back', 'shoulders_front', 'head_neck_left']


def handoff_section():
    for _, p in HANDOFF_PATHS:
        if not (ROOT / p).exists():
            raise FileNotFoundError(p)
    link = lambda p: f'[`{p}`]({BLOB}{p})'
    L = ['## Current status and morning handoff (9 October 2026)', '',
         '**Current audit candidate: c004** (`shoulder_thorax_c004_arm_inputs`). It passes the automated structural, movement and '
         'solver checks but is **not canonical and not anatomically accepted**: CP2 FAILS on zero spinal disc gaps (U5). '
         'Readiness: 0 READY / 9 PARTIAL / 3 BLOCKED. No c005 exists.', '',
         '**Experimental only (not candidates, never accepted anatomy):** P001 (metacarpals M2-M4 lengthened to the male means; '
         'blocked by carpal geometry) and T001 (coupled spine + ribs rebuild with explicit discs; owner-approved isolated experiment). '
         'P003 was rejected. The T001 renders below are labelled before/after diagnostics, not approved anatomy.', '',
         '**Source and commits:** Claude work from `claude/coupled-trunk-rebuild-20261009` @ `de8d521b` was integrated onto this '
         'branch at merge `f864e50d` (destination base `2d4b352c`); tracker checkpoint `e0fdcdbd`. a003, c001-c004 and production '
         'are unchanged.', '',
         '**Tests:** last full suite 1,064 tests, 1,054 pass; 9 inherited production-control failures unchanged '
         '(test_original_v1_production_control: 3 failures + 2 errors; test_original_v1_execution_orchestration: 1 failure + '
         '2 errors; test_verify_original_v1_candidate_status: 1 failure). Post-integration checks: evidence integrity, '
         'T001 (7) and spine/trunk (13) tests OK.', '',
         '**T001 outcome vs c004 (independent checks):** disc gaps 0 -> 3.2-10.6 mm (CP2 no FAIL); T12/L1 vs pelvis prediction '
         '+38.5 -> +6.2 mm; IJ stays within T2-T3; rib levels preserved; girdle and arms unchanged; 60 spine/rib movement tests '
         'changed, all others identical. Worse: C7 vs ANSUR cervicale -17.8 -> -29 mm.', '',
         '**Known defects and open questions:**', '',
         '- C7 / chest-tilt trade-off: lowering the thoracic column (T001) moves C7 further below ANSUR cervicale; tied to the '
         'OPEN thorax-pitch conflict (living C7-IJ 80.7 mm vs bony models 33-46 mm) and a grade-D C7 tip offset.',
         '- Rib-slope evidence gap: Holcombe 2017 pump-handle angles have no mapped frame; T001 rib inclination and the rib-10 '
         'height (+28 mm vs ANSUR) are unverified.',
         '- c005 blocker: ten fingertip endpoints unsourced (H2); hand outside the unmoved a003 skin; carpal centroid layout '
         'BLOCKED, so P001 cannot be frozen.',
         '- Spine: thoracic per-level wedging unsourced; lumbar 43 mm too long in c004 (U10); sacrum 42 mm from the P1 S1 frame; '
         'endplate surfaces absent (clearance UNVERIFIED).',
         '- Movement model: in plain knee flexion the patella is static (ligament +114 %); the existing patellar follower '
         'test rotates it at the sourced 0.66 ratio but has no sourced translation, so the ligament still lengthens by up to '
         '23 mm (+43 %) (L3; Rajagopal path template not installed); '
         'clavicle elevation missing (U3, verified 0 deg at 170 deg humerothoracic; MoBL coefficient vs 10 deg bound conflict); hip-adduction test crosses tibiae (L4, '
         'start-posture fix); hand-thigh contact in forearm sweeps (H6, quantified: GH start abduction >= 7-9 deg clears it); hallux on the opposite '
         'foot in hip internal rotation (L7, quantified: contralateral abduction >= 3-4 deg clears it); 78 unsupported amplitudes.',
         '- Other open tracker items: radius/ulna endpoint corridors, humerus and sternum length, tarsal joint centres (L5), '
         'thumb CMC gap (H3), absolute shoulder height vs trunk, head geometry placeholders.',
         '- Erratum: the earlier "IJ +24.7 mm" residual used a stale a003 skin input; c004 bony IJ is already at ANSUR.', '',
         '**Labelled T001 before/after diagnostics (c004 left, T001 right; experimental):**', '']
    for v in T001_RENDERS:
        p = f'ORIGINAL_V1_WORK/anatomy/audit/experiments/t001_coupled_trunk/before_after/{v}_c004_vs_t001.jpg'
        if not (ROOT / p).exists():
            raise FileNotFoundError(p)
        L.append(f'- [{v}: c004 vs T001 (experimental)]({BLOB}{p})')
    L += ['', '**Every current evidence path:**', '']
    L += [f'- {t}: {link(p)}' for t, p in HANDOFF_PATHS]
    return L + ['']


def markdown(ix):
    L = ['# Skeleton review pack (shoulder stage): index', '',
         'Every image and clip below is in the repository, and its sha256 is verified against its manifest (`review_pack_index_v1.json`). All candidates are **audit proposals, not canonical**; nothing here is a production asset.', '',
         ] + handoff_section() + ['## Start here', '']
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
    reuse = AUD / 'candidates/shoulder_thorax_c004_arm_inputs/review_reuse.json'
    if reuse.exists():
        u = json.loads(reuse.read_text()); rel = str(reuse.relative_to(ROOT))
        L += ['## c004 arm-input resync: reuses the c003 pack (no new renders)', '',
              f'c004 changes only six skeleton_input arm points per side; every visual input is hash-identical to c003 ([`{rel}`]({BLOB}{rel})), '
              'so the c003 images above depict c004 exactly. They and their manifest still name c003. Status: '
              f'`{u["status"]}`. The carpals/hand input follow-up found no defensible c005 (hand_input_audit/hand_input_source_rebuild_v1.json); no images were produced for it.', '']
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
