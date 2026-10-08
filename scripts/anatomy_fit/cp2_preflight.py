#!/usr/bin/env python3
"""CP2 coordinate/contact preflight for a whole-body skeleton candidate (read-only).

Two parts:
  check_candidate(...)  hard structural invariants of a candidate in the fit-record schema
                        (bones: head_m/tail_m/parent/parent_relation; joint_markers: centre_m/frame).
  readiness_ledger(...) what is still missing per region, from GPT's readiness/selection files
                        and the a003 placement classes.

Statuses: PASS, FAIL, UNVERIFIED (required data absent), INFO (measurement only, no gate).
No anatomical tolerance is invented: geometric gates are strict (> 0, sign, identity).
The only numeric tolerance is FLOAT_EPS for frame orthonormality: Blender stores matrices in single precision, so a
captured proper frame shows ~7e-7 orthonormality error (CP3 rehearsal); 1e-5 (~0.0006 deg skew) is numerical, not anatomical.
A full PASS is necessary for CP2, not sufficient: evidence review is still required.
The current disc_surfaces schema contains planes and a caller-supplied ellipse,
not candidate-bound anatomical envelopes. Positive plane diagnostics therefore
remain UNVERIFIED for full endplate clearance; no metadata flag can promote them.

CLI:
  cp2_preflight.py --candidate FIT.json [--out DIR]
"""
import argparse, json, math, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from endplate_clearance import clearance  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
FLOAT_EPS = 1e-5
SPINAL_DISCS = ['disc_c2_c3', 'disc_c3_c4', 'disc_c4_c5', 'disc_c5_c6', 'disc_c6_c7', 'disc_c7_t1'] + \
    [f'disc_t{i}_t{i + 1}' for i in range(1, 12)] + ['disc_t12_l1', 'disc_l1_l2', 'disc_l2_l3', 'disc_l3_l4', 'disc_l4_l5', 'disc_l5_sacrum']
SHOULDER = ('sternoclavicular', 'acromioclavicular', 'glenohumeral')

# Claude bookkeeping only (not anatomy): which readiness region each inventory region is tracked under.
READINESS_OF_INVENTORY_REGION = {
    'skull': 'head_neck_fixed', 'facial_skeleton': 'head_neck_fixed', 'auditory_ossicles': 'head_neck_fixed',
    'neck': 'head_neck_fixed', 'vertebral_column': 'spine', 'thoracic_cage': 'ribs', 'pectoral_girdle': 'shoulder_girdle',
    'wrist': 'carpus', 'hand': 'hand', 'pelvic_girdle': 'pelvis', 'lower_limb': 'lower_limb_long_bones',
}
TARSALS = ('talus', 'calcaneus', 'navicular', 'cuboid', 'medial_cuneiform', 'intermediate_cuneiform', 'lateral_cuneiform')
SELECTION_OF_READINESS = {
    'shoulder_girdle': 'shoulder_girdle', 'spine': 'spine', 'ribs': 'ribs', 'forearm': 'forearm', 'carpus': 'carpus_hand',
    'hand': 'carpus_hand', 'pelvis': 'pelvis', 'lower_limb_long_bones': 'lower_limb_long', 'tarsus': 'tarsus_forefoot',
    'forefoot_toes': 'tarsus_forefoot', 'head_neck_fixed': 'head_neck', 'humerus': None,
}


def load_reference(anat=ANAT):
    inv = json.loads((anat / 'adult_bone_inventory_206.json').read_text())['bones']
    art = json.loads((anat / 'adult_articulation_inventory.json').read_text())
    return inv, art['articulations'], art['additional_structures']


def _vec3(v):
    return isinstance(v, list) and len(v) == 3 and all(
        isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) for x in v)


def _sub(a, b):
    return [x - y for x, y in zip(a, b)]


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _result(cid, failures=(), unverified=(), info=None, detail=''):
    status = 'FAIL' if failures else 'UNVERIFIED' if unverified else 'INFO' if info is not None and detail == 'measurement' else 'PASS'
    out = {'id': cid, 'status': status}
    if failures:
        out['failures'] = list(failures)
    if unverified:
        out['unverified'] = list(unverified)
    if info is not None:
        out['measurements'] = info
    return out


def check_candidate(cand, inventory, articulations, additional):
    bones, markers = cand.get('bones', {}), cand.get('joint_markers', {})
    inv_ids = {b['id']: b for b in inventory}
    art_ids = {a['id']: a for a in articulations}
    owner = {k: v['owner_bone'] for k, v in additional.items()}
    checks = []

    # 1 identity: exactly the 206 inventory bones
    missing, extra = sorted(set(inv_ids) - set(bones)), sorted(set(bones) - set(inv_ids))
    checks.append(_result('bone_identity_206', [f'missing {m}' for m in missing] + [f'extra {e}' for e in extra]))

    # 2 finite coordinates (null = unresolved target, never filled)
    bad = [k for k, b in bones.items() if not (_vec3(b.get('head_m')) and _vec3(b.get('tail_m')))]
    checks.append(_result('bone_coordinates_finite', [f'{k} head/tail not a finite 3-vector' for k in sorted(bad)]))
    good = {k: b for k, b in bones.items() if k not in bad}

    # 3 nondegenerate sticks
    lengths = {k: math.dist(b['head_m'], b['tail_m']) for k, b in good.items()}
    shortest = min(lengths, key=lengths.get) if lengths else None
    checks.append(_result('bone_nondegenerate', [f'{k} zero length' for k, L in sorted(lengths.items()) if L == 0],
                          info={'shortest_bone': shortest, 'shortest_mm': lengths[shortest] * 1000} if shortest else None))

    # 4 parent tree, joint references and hyoid exception
    fails = []
    for k, b in bones.items():
        p, rel = b.get('parent'), b.get('parent_relation')
        if p is not None and p not in bones:
            fails.append(f'{k}: parent {p} absent')
        if not isinstance(rel, dict) or rel.get('type') not in ('root', 'articular', 'carrier'):
            fails.append(f'{k}: missing, malformed or unknown parent relation')
            continue
        if rel.get('type') == 'articular':
            jid = rel.get('joint_id')
            j = art_ids.get(jid) if isinstance(jid, str) else None
            if j is None:
                fails.append(f'{k}: joint {rel.get("joint_id")} not in articulation inventory')
            else:
                parts = {owner.get(x, x) for x in j['participants']}
                if not {k, p} <= parts:
                    fails.append(f'{k}: joint {j["id"]} does not join {k} and {p}')
        else:
            reason = rel.get('reason')
            if not isinstance(reason, str) or not reason.strip():
                fails.append(f'{k}: {rel["type"]} relation requires an explicit reason')
            if rel.get('joint_id') is not None:
                fails.append(f'{k}: {rel["type"]} relation cannot claim an articulation')
            if rel['type'] == 'root' and p is not None:
                fails.append(f'{k}: root relation has a parent')
        if p is None and rel.get('type') != 'root':
            fails.append(f'{k}: no parent but relation is {rel.get("type")}')
    for k in bones:
        seen, cur = set(), k
        while cur is not None and cur in bones:
            if cur in seen:
                fails.append(f'{k}: parent cycle')
                break
            seen.add(cur)
            cur = bones[cur].get('parent')
    if 'hyoid' in bones and bones['hyoid'].get('parent') is not None:
        fails.append('hyoid has an osseous parent (must remain suspended)')
    roots = sorted(k for k, b in bones.items() if b.get('parent') is None)
    checks.append(_result('parent_tree', fails, info={'roots': roots}))

    # 5 side sign: anatomical left = +X
    fails, mid = [], {}
    for k, b in good.items():
        side = inv_ids.get(k, {}).get('side')
        x = (b['head_m'][0] + b['tail_m'][0]) / 2
        if side == 'left' and not x > 0 or side == 'right' and not x < 0:
            fails.append(f'{k}: {side} bone midpoint x = {x * 1000:.2f} mm')
        if side == 'midline':
            mid[k] = abs(x) * 1000
    worst = max(mid, key=mid.get) if mid else None
    checks.append(_result('side_sign_left_plus_x', fails, info={'largest_midline_offset': worst, 'mm': mid[worst]} if worst else None))

    # 6 bilateral mirror asymmetry: measurement only (no symmetry tolerance is sourced)
    asym = {}
    for k in good:
        if k.endswith('_left') or '_left_' in k:
            m = k.replace('_left', '_right')
            if m in good:
                a, c = good[k], good[m]
                asym[k] = max(math.dist(a[e], [-c[e][0], c[e][1], c[e][2]]) for e in ('head_m', 'tail_m')) * 1000
    worst = max(asym, key=asym.get) if asym else None
    checks.append(_result('bilateral_mirror_asymmetry', info={'pairs': len(asym), 'largest_pair': worst,
                                                              'largest_mm': asym[worst] if worst else None}, detail='measurement'))

    # 7 joint identity: exactly the articulation inventory
    missing, extra = sorted(set(art_ids) - set(markers)), sorted(set(markers) - set(art_ids))
    checks.append(_result(f'joint_identity_{len(art_ids)}', [f'missing {m}' for m in missing] + [f'extra {e}' for e in extra]))

    # 8 joint centres finite; frame bone exists; frame proper (orthonormal, det +1)
    fails = []
    for k, m in markers.items():
        if not _vec3(m.get('centre_m')):
            fails.append(f'{k}: centre not a finite 3-vector')
        if m.get('frame_bone') not in bones:
            fails.append(f'{k}: frame bone {m.get("frame_bone")} absent')
        F = m.get('frame_axes_columns_XYZ')
        if not (isinstance(F, list) and len(F) == 3 and all(_vec3(r) for r in F)):
            fails.append(f'{k}: frame not a finite 3x3')
            continue
        cols = [[F[r][c] for r in range(3)] for c in range(3)]
        err = max(abs(_dot(cols[i], cols[j]) - (i == j)) for i in range(3) for j in range(3))
        det = _dot(cols[0], [cols[1][1] * cols[2][2] - cols[1][2] * cols[2][1], cols[1][2] * cols[2][0] - cols[1][0] * cols[2][2],
                             cols[1][0] * cols[2][1] - cols[1][1] * cols[2][0]])
        if err > FLOAT_EPS or det <= 0:
            fails.append(f'{k}: frame not proper (orthonormal error {err:.2e}, det {det:.6f})')
    checks.append(_result('joint_frames_proper', fails))

    # 9 shoulder SC / AC / GH centres distinct on each side
    fails, unv, dists = [], [], {}
    for side in ('left', 'right'):
        c = {j: markers.get(f'{j}_{side}', {}).get('centre_m') for j in SHOULDER}
        if not all(_vec3(v) for v in c.values()):
            unv.append(f'{side}: SC/AC/GH centre missing')
            continue
        for i, a in enumerate(SHOULDER):
            for b in SHOULDER[i + 1:]:
                d = math.dist(c[a], c[b]) * 1000
                dists[f'{a}-{b}_{side}_mm'] = d
                if d == 0:
                    fails.append(f'{side}: {a} and {b} centres coincide')
    checks.append(_result('shoulder_centres_distinct', fails, unv, info=dists))

    # 10 spinal disc centre-line gap (sticks run inferior -> superior endplate midpoint)
    fails, unv, gaps = [], [], {}
    for d in SPINAL_DISCS:
        sup, inf = (art_ids.get(d) or {}).get('participants', [None, None])
        if sup not in good or inf not in good:
            unv.append(f'{d}: participant geometry missing')
            continue
        if lengths[sup] == 0 or lengths[inf] == 0:
            fails.append(f'{d}: degenerate vertebral participant (no defined endplate axis)')
            continue
        axis = _sub(good[inf]['tail_m'], good[inf]['head_m'])
        step = _sub(good[sup]['head_m'], good[inf]['tail_m'])
        along = _dot(step, axis) / math.hypot(*axis) * 1000
        gaps[d] = round(along, 4)
        if not along > 0:
            fails.append(f'{d}: superior body starts {along:.2f} mm along the inferior body axis (no disc space)')
    checks.append(_result('spinal_disc_centre_gap_positive', fails, unv, info=gaps))

    # 11 planar diagnostics cannot verify full candidate-bound curved endplates.
    surf = cand.get('disc_surfaces') or {}
    fails, unv, mins = [], [], {}
    for k in sorted(set(surf) - set(SPINAL_DISCS)):
        fails.append(f'{k}: not a C2/C3-L5/S1 disc (no discs at C0/C1 or C1/C2)')
    for d in SPINAL_DISCS:
        s = surf.get(d)
        if s is None:
            unv.append(f'{d}: no endplate surfaces')
            continue
        try:
            r = clearance(s['upper_origin_mm'], s['upper_normal'], s['lower_origin_mm'], s['lower_normal'],
                          s['footprint_centre_xy_mm'], s['footprint_radii_xy_mm'])
        except (KeyError, ValueError, TypeError) as e:
            fails.append(f'{d}: invalid surface data ({e})')
            continue
        mins[d] = r['minimum_projected_gap_mm']
        if not r['separated_everywhere']:
            fails.append(f'{d}: supplied planes touch or overlap (minimum {r["minimum_projected_gap_mm"]:.3f} mm)')
        else:
            unv.append(f'{d}: positive plane diagnostic only; candidate-bound curved surfaces, '
                       'full footprint coverage and approximation error remain unverified')
    checks.append(_result('disc_endplate_clearance', fails, unv, info=mins or None))

    counts = {s: sum(c['status'] == s for c in checks) for s in ('PASS', 'FAIL', 'UNVERIFIED', 'INFO')}
    verdict = 'STRUCTURE_PASS_EVIDENCE_REVIEW_STILL_REQUIRED' if not counts['FAIL'] and not counts['UNVERIFIED'] else \
        'FAIL' if counts['FAIL'] else 'INCOMPLETE'
    return {'verdict': verdict, 'counts': counts, 'checks': checks}


def readiness_region_of(bone):
    if bone['region'] == 'upper_limb':
        return 'forearm' if bone['id'].startswith(('radius', 'ulna')) else 'humerus'
    if bone['region'] == 'foot':
        return 'tarsus' if bone['id'].startswith(TARSALS) else 'forefoot_toes'
    return READINESS_OF_INVENTORY_REGION.get(bone['region'])


def _nulls(obj, path):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _nulls(v, f'{path}.{k}')
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _nulls(v, f'{path}[{i}]')
    elif obj is None:
        yield path


def readiness_ledger(inventory, readiness, selection, a003_bones):
    regions = {}
    for name, r in readiness['regions'].items():
        sel_name = SELECTION_OF_READINESS[name]
        sel = selection['regions'].get(sel_name, {}) if sel_name else {}
        regions[name] = {'readiness': r['readiness'], 'blockers': r.get('blockers', []),
                         'selection_region': sel_name, 'selection_freeze_state': sel.get('freeze_state'),
                         'unselected_targets': list(_nulls(sel.get('selected', {}), 'selected')),
                         'bones': [], 'a003_placement': {}}
    unassigned = []
    for b in inventory:
        name = readiness_region_of(b)
        if name is None:
            unassigned.append(b['id'])
            continue
        reg = regions[name]
        reg['bones'].append(b['id'])
        cls = a003_bones.get(b['id'], {}).get('placement', 'absent')
        reg['a003_placement'][cls] = reg['a003_placement'].get(cls, 0) + 1
    for reg in regions.values():
        reg['bone_count'] = len(reg['bones'])
    return {'overall_status': readiness['overall_status'], 'freeze_ready': selection['freeze_ready'],
            'region_counts': {s: sum(r['readiness'] == s for r in regions.values()) for s in ('READY', 'PARTIAL', 'BLOCKED')},
            'bones_covered': sum(r['bone_count'] for r in regions.values()),
            'bones_without_readiness_region': unassigned, 'regions': regions}


def markdown(report, ledger, candidate_label):
    L = [f'# CP2 preflight: {candidate_label}', '',
         f'**Verdict: {report["verdict"]}** ({report["counts"]}).', '',
         'A full pass is necessary for CP2, not sufficient. UNVERIFIED means the required data does not exist yet; it is never a pass.', '',
         '| Check | Status | Detail |', '|---|---|---|']
    for c in report['checks']:
        items = c.get('failures') or c.get('unverified') or []
        det = (f'{len(items)} item(s); first: {items[0]}' if items else
               json.dumps(c.get('measurements'))[:160] if c.get('measurements') else '')
        L.append(f'| `{c["id"]}` | {c["status"]} | {det} |')
    L += ['', f'## What is still missing per region (freeze_ready={ledger["freeze_ready"]}, {ledger["region_counts"]})', '',
          '| Region | Readiness | Bones | a003 placement | Unselected targets | Blockers |', '|---|---|---|---|---|---|']
    for n, r in ledger['regions'].items():
        pl = ', '.join(f'{k} {v}' for k, v in sorted(r['a003_placement'].items()))
        L.append(f'| {n} | {r["readiness"]} | {r["bone_count"]} | {pl} | {len(r["unselected_targets"])} | ' +
                 '; '.join(r['blockers']) + ' |')
    L += ['', f'Bones without a readiness region: {", ".join(ledger["bones_without_readiness_region"]) or "none"}.', '']
    return '\n'.join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--candidate', required=True)
    ap.add_argument('--out')
    o = ap.parse_args()
    inv, arts, add = load_reference()
    cand = json.loads(Path(o.candidate).read_text())
    report = check_candidate(cand, inv, arts, add)
    a003 = json.loads((ANAT / 'character_fit_r95_a003.json').read_text())['bones']
    ledger = readiness_ledger(inv, json.loads((ANAT / 'canonical_freeze_readiness_v1.json').read_text()),
                              json.loads((ANAT / 'canonical_target_selection_v1.json').read_text()), a003)
    if o.out:
        out = Path(o.out)
        out.mkdir(parents=True, exist_ok=False)
        (out / 'cp2_preflight_report.json').write_text(json.dumps({'candidate': o.candidate, 'report': report, 'ledger': ledger}, indent=1) + '\n')
        (out / 'README.md').write_text(markdown(report, ledger, o.candidate))
    print(json.dumps({'verdict': report['verdict'], 'counts': report['counts'], 'regions': ledger['region_counts'],
                      'unassigned': ledger['bones_without_readiness_region']}))


if __name__ == '__main__':
    main()
