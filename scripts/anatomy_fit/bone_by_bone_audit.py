#!/usr/bin/env python3
"""Bone-by-bone audit of all 206 bones (read-only; changes nothing). For each bone of each record:

  identity/region, parent, parent articulation, placement class and confidence (as recorded);
  stick length (mm) and direction (angle to world vertical, components);
  REPRESENTATION: what the head->tail stick stands for (an articular-centre span of a long bone, or a chord / control
     stick for a curved, flat or volumetric bone). A chord's straightness or shortness is a visualisation property, not
     an anatomical error;
  CONNECTION: distance from the parent articulation's joint-marker centre to the nearest point of this bone's stick and of
     the parent's stick (a joint centre off a stick is expected for condyles/heads; reported, graded only for the
     articular-span class where the stick endpoint IS the joint centre by construction);
  MIRROR: max endpoint distance between the bone and its reflected partner;
  EVIDENCE: the committed convergence grade for its region (canonical_evidence_convergence_v1.json) and, only where the
     stick's endpoints match a committed measurement definition, a corridor comparison (z against mean/SD).
No anatomical threshold is invented: corridor z-scores are reported against the committed source values only.

  bone_by_bone_audit.py --out JSON [--records a003=PATH c004=PATH ...]
"""
import argparse, hashlib, json, math, sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ROOT = HERE.parents[1]
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'

LONG_SPAN = ('humerus', 'radius', 'ulna', 'femur', 'tibia', 'fibula', 'metacarpal', 'digit', 'thumb', 'metatarsal', 'hallux', 'toe')
VERT = tuple(f'c{i}' for i in range(1, 8)) + tuple(f't{i}' for i in range(1, 13)) + tuple(f'l{i}' for i in range(1, 6))
SKULL = ('frontal', 'parietal', 'occipital', 'temporal', 'sphenoid', 'ethmoid', 'maxilla', 'zygomatic', 'nasal', 'lacrimal', 'palatine',
         'vomer', 'inferior_nasal', 'mandible', 'malleus', 'incus', 'stapes', 'hyoid')
CARPAL = ('scaphoid', 'lunate', 'triquetrum', 'pisiform', 'trapezium', 'trapezoid', 'capitate', 'hamate')
TARSAL = ('talus', 'calcaneus', 'navicular', 'cuboid', 'medial_cuneiform', 'intermediate_cuneiform', 'lateral_cuneiform')


def region(n):
    b = n.rsplit('_', 1)[0] if n.endswith(('_left', '_right')) else n
    if b in VERT or b in ('sacrum', 'coccyx'):
        return 'spine'
    if b.startswith('rib') or b == 'sternum':
        return 'ribs_sternum'
    if b.startswith(SKULL):
        return 'head_neck'
    if b in ('clavicle', 'scapula'):
        return 'shoulder_girdle'
    if b in ('humerus', 'radius', 'ulna'):
        return 'arm'
    if b.startswith(CARPAL):
        return 'carpus'
    if b.startswith(('metacarpal', 'digit', 'thumb')):
        return 'hand'
    if b == 'hip_bone':
        return 'pelvis'
    if b in ('femur', 'patella', 'tibia', 'fibula'):
        return 'lower_limb'
    if b.startswith(TARSAL):
        return 'tarsus'
    if b.startswith(('metatarsal', 'hallux', 'toe')):
        return 'forefoot'
    return 'other'


def representation(n):
    b = n.rsplit('_', 1)[0] if n.endswith(('_left', '_right')) else n
    if b.startswith('rib'):
        return 'CHORD_OF_CURVED_BONE (costovertebral joint to anterior end; true rib is a curved centreline)'
    if b == 'hip_bone':
        return 'CHORD_OF_FLAT_BONE (SI joint to pubic symphysis side; ilium, acetabulum and ischium not represented)'
    if b == 'scapula':
        return 'CHORD_OF_FLAT_BONE (glenoid centre to inferior angle; spine, acromion, coracoid not represented)'
    if b == 'clavicle':
        return 'CHORD_OF_CURVED_BONE (SC to AC joint centres; S-shaped centreline not represented)'
    if b == 'mandible':
        return 'CHORD_THROUGH_SPACE (condylar midpoint to mental region; U-shaped bone)'
    if b.startswith(SKULL):
        return 'SCHEMATIC_STICK (placement reference only; cranial/facial shape not represented)'
    if b in VERT:
        return 'BODY_AXIS_STICK (vertebral body axis; posterior elements not represented)'
    if b in ('sacrum', 'coccyx', 'sternum', 'patella'):
        return 'AXIS_STICK_OF_VOLUMETRIC_BONE'
    if b.startswith(CARPAL) or b.startswith(TARSAL):
        return 'CONTROL_STICK_OF_SHORT_BONE (not whole-bone length; INV_TARSAL_SEMANTICS)'
    if b.startswith(LONG_SPAN):
        return 'ARTICULAR_SPAN (joint centre/station to joint centre/station)'
    return 'UNCLASSIFIED'


CONVERGENCE_REGION = {
    'clavicle': 'clavicle', 'scapula': 'scapula', 'radius': 'radius_forearm', 'ulna': 'ulna', 'sacrum': 'sacrum', 'patella': 'patella_size',
    'femur': 'femur_tibia', 'tibia': 'femur_tibia', 'sternum': 'sternum'}


def convergence_key(n):
    b = n.rsplit('_', 1)[0] if n.endswith(('_left', '_right')) else n
    if b in CONVERGENCE_REGION:
        return CONVERGENCE_REGION[b]
    if b in ('metacarpal_2', 'metacarpal_3', 'metacarpal_4'):
        return 'hand_metacarpals_2_4'
    if b.startswith(('digit', 'thumb', 'metacarpal')):
        return 'hand_other_phalanges'
    if b in VERT:
        return 'spine'
    if b.startswith('rib'):
        return 'ribs'
    if b.startswith(TARSAL):
        return 'tarsals'
    if b.startswith('metatarsal'):
        return 'metatarsals'
    if b.startswith(SKULL):
        return 'cranial_facial_fixed_geometry'
    return None


def seg_point_dist(p, a, b):
    ab = b - a; t = np.clip((p - a) @ ab / (ab @ ab), 0, 1)
    return float(np.linalg.norm(p - (a + t * ab)))


def corridors():
    """Only corridors whose committed measurement definition matches the stick endpoints closely enough to compare."""
    hp = json.loads((ANAT / 'canonical_hand_proportion_audit_v1.json').read_text())['bones']
    out = {}
    for k, v in hp.items():
        if v.get('ayd1998_male_mean_mm') and v.get('ayd1998_sd_mm'):
            out[k] = {'source': 'DOGAN_1998_HAND_RELATIONS (Aydinlioglu 1998, 50 men, AP radiograph head/base midpoint length)',
                      'mean': v['ayd1998_male_mean_mm'], 'sd': v['ayd1998_sd_mm'],
                      'endpoint_note': 'stick spans joint centres/stations; source spans bony boundary midpoints (close, not identical)'}
    delta = json.loads((ANAT / 'canonical_rebuild_delta_summary_v1.json').read_text())['regions']
    ref = delta['shoulder_clavicle']['adult_male_endpoint_reference_mm']
    out['clavicle'] = {'source': 'independent CT male SC-AC endpoint reference (canonical_rebuild_delta_summary_v1)', 'mean': ref['mean'],
                       'observed_range': ref['observed_range'], 'endpoint_note': 'joint-centre chord vs bony endpoint chord'}
    return out


def audit(rec, corr):
    B, J = rec['bones'], rec['joint_markers']
    rows = {}
    for n, b in B.items():
        h, t = np.asarray(b['head_m']), np.asarray(b['tail_m']); d = t - h; L = float(np.linalg.norm(d))
        row = {'region': region(n), 'parent': b['parent'], 'relation': b['parent_relation'], 'placement': b['placement'], 'confidence': b['confidence'],
               'recipe': b.get('recipe'), 'length_mm': round(L * 1000, 2), 'direction': [round(x, 4) for x in d / L],
               'angle_to_vertical_deg': round(math.degrees(math.acos(abs(d[2]) / L)), 2), 'representation': representation(n),
               'convergence': convergence_key(n)}
        jid = b['parent_relation'].get('joint_id')
        if jid and jid in J:
            c = np.asarray(J[jid]['centre_m'])
            row['joint_to_own_stick_mm'] = round(seg_point_dist(c, h, t) * 1000, 3)
            row['joint_to_own_head_mm'] = round(float(np.linalg.norm(c - h)) * 1000, 3)
            if b['parent'] in B:
                ph, pt = np.asarray(B[b['parent']]['head_m']), np.asarray(B[b['parent']]['tail_m'])
                row['joint_to_parent_stick_mm'] = round(seg_point_dist(c, ph, pt) * 1000, 3)
        if n.endswith('_left') and n[:-5] + '_right' in B:
            o = B[n[:-5] + '_right']
            row['mirror_max_mm'] = round(max(float(np.linalg.norm(np.asarray(b[e]) * [-1, 1, 1] - np.asarray(o[e]))) for e in ('head_m', 'tail_m')) * 1000, 4)
        base = n.rsplit('_', 1)[0] if n.endswith(('_left', '_right')) else n
        key = n if n in corr else base if base in corr else None
        if key:
            cr = corr[key]
            row['corridor'] = {**cr, 'value_mm': row['length_mm']}
            if 'sd' in cr:
                row['corridor']['z'] = round((row['length_mm'] - cr['mean']) / cr['sd'], 2)
            else:
                lo, hi = cr['observed_range']; row['corridor']['outside_observed_range'] = not lo <= row['length_mm'] <= hi
        rows[n] = row
    return rows


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); ap.add_argument('--records', nargs='+', required=True)
    o = ap.parse_args()
    conv = json.loads((ANAT / 'canonical_evidence_convergence_v1.json').read_text())['region_findings']
    corr = corridors(); out = {'records': {}, 'convergence_grades': {k: {'grade': v['grade'], 'state': v['state']} for k, v in conv.items()}}
    for spec in o.records:
        lab, p = spec.split('=', 1)
        rec = json.loads(Path(p).read_text())
        out['records'][lab] = {'path': p, 'sha256': hashlib.sha256(Path(p).read_bytes()).hexdigest(), 'bones': audit(rec, corr)}
    Path(o.out).parent.mkdir(parents=True, exist_ok=True)
    Path(o.out).write_text(json.dumps({'schema_version': 1, 'created': '2026-10-09', 'kind': 'BONE_BY_BONE_AUDIT_READ_ONLY', **out}, indent=1) + '\n')
    for lab, r in out['records'].items():
        B = r['bones']
        print(lab, len(B), 'bones')
        off = sorted(((v.get('joint_to_own_stick_mm', 0), n) for n, v in B.items() if v['representation'].startswith('ARTICULAR_SPAN')), reverse=True)[:8]
        print('  articular-span bones farthest from their parent joint centre (mm):', off)
        print('  max mirror:', max((v.get('mirror_max_mm', 0), n) for n, v in B.items()))
        print('  corridor |z|>2:', sorted((n, v['corridor']['z']) for n, v in B.items() if 'corridor' in v and 'z' in v['corridor'] and abs(v['corridor']['z']) > 2))
        print('  clavicle:', [(n, v['length_mm'], v['corridor'].get('outside_observed_range')) for n, v in B.items() if n.startswith('clavicle')])


if __name__ == '__main__':
    main()
