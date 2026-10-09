#!/usr/bin/env python3
"""P005: diagnostic rigid-chain shoulder FOLLOW-UP on the P004 rib/sternum replay.

Mechanical correspondence experiment, NOT joint-centre, scapulothoracic
contact, clavicle rhythm or clinical anatomy. In particular it does not
solve thorax pose or source-compatible scapular location.

Translate the *entire dependent anatomical control-bone subtree* of both
clavicles by P004's sternum reference translation. This restores the
reference SC-relative vector and preserves AC/GH/limb-marker relations
without distorting the arm or fingers. The global arm/torso relationship
and scapulothoracic soft-tissue sliding are still unverified.

The input P004 and original c004/P003 are never mutated.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

import replay_p004_coupled_thorax as p4


def descendants(bones, roots):
    """Traverse the actual recorded parent graph without inventing rig IDs."""
    selected = set(roots)
    if not selected <= set(bones):
        raise ValueError('missing bilateral clavicles')
    while True:
        expanded = selected | {
            bid for bid, record in bones.items()
            if record.get('parent') in selected
        }
        if expanded == selected:
            break
        selected = expanded
    if not any(x.startswith('digit') for x in selected):
        raise ValueError('subtree lacks hand phalanges, investigate parent graph')
    return selected


def build(base, p004):
    if p004.get('candidate', {}).get('id') != 'P004_COUPLED_THORAX_MECHANICS_DIAGNOSTIC_REPLAY':
        raise ValueError('P005 requires isolated P004 source, not c004/P003')
    if set(base['bones']) != set(p004['bones']) or set(base['joint_markers']) != set(p004['joint_markers']):
        raise ValueError('bone or joint identities differ')
    prior = p004['bones']['sternum']['head_m']
    initial = base['bones']['sternum']['head_m']
    shift = [x - y for x, y in zip(prior, initial)]
    if not all(math.isfinite(x) for x in shift):
        raise ValueError('nonfinite sternum translation')
    if math.dist(prior, initial) < 0.001:
        raise ValueError('no substantive P004 sternum movement to reattach shoulder to')

    out = copy.deepcopy(p004)
    moved = descendants(out['bones'], ('clavicle_left', 'clavicle_right'))
    for bone in moved:
        p4._translate_bone(out['bones'][bone], shift)

    # Rigid translations: markers are carried by the corresponding bone,
    # frame axes do not rotate. All SC/AC/GH relative geometry stays fixed.
    moved_markers = p4._translate_markers(out, {bid: shift for bid in moved})
    upperlimbs = {k for k in moved if k.startswith(('clavicle_', 'scapula_', 'humerus_',
                                                 'radius_', 'ulna_', 'metacarpal_'))}
    other = set(out['bones']) - moved
    if any(k.startswith(('rib_', 'sternum', 't1')) for k in moved):
        raise AssertionError('clavicle descendants must not include spine or ribs')
    out['candidate'] = {
        'id': 'P005_STERNUM_SC_RIGID_CHAIN_DIAGNOSTIC',
        'status': 'DIAGNOSTIC_ONLY_NOT_ANATOMICAL_CANDIDATE',
        'freeze_ready': False,
        'canonical_promotion_allowed': False,
        'source_id': 'P004_COUPLED_THORAX_MECHANICS_DIAGNOSTIC_REPLAY',
        'operation': 'RIGID_TRANSLATION_OF_RECORDED_CLAVICLE_SUBTREES',
        'translation_m': shift,
        'translation_mm': [round(v*1000, 5) for v in shift],
        'translated_bone_ids': sorted(moved),
        'translated_joint_markers': moved_markers,
        'translated_bone_count': len(moved),
        'upperlimb_major_bones': sorted(upperlimbs),
        'unchanged_bone_count': len(other),
        'known_unresolved_constraints': [
            'SC relative-vector preservation is a computational invariant, not an accepted SC target.',
            'Thorax-spine AP geometry and S1 AP depth still lack source-compatible evidence.',
            'SC/AC/GH and scapulothoracic physical surface contact/rotation not verified.',
            'Moving the entire arm may change arm/torso, thigh, hand and equipment clearances.',
            'Scapula sliding/rotating against a CURVED ribcage is not solved by translation.',
            'Stature, shoulder heights and ANSUR living-surface landmarks must be rechecked.',
            'No muscle, skin, weights or production character may be fitted to P005.'
        ],
    }
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, default=p4.C004)
    parser.add_argument('--p004', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    bbytes, pbytes = args.baseline.read_bytes(), args.p004.read_bytes()
    result = build(json.loads(bbytes), json.loads(pbytes))
    result['candidate']['input_sha256'] = {
        'baseline': hashlib.sha256(bbytes).hexdigest(),
        'p004': hashlib.sha256(pbytes).hexdigest(),
    }
    with args.out.open('x', encoding='utf-8') as f:
        json.dump(result, f, indent=1)
        f.write('\n')
    print(json.dumps({
        'id': result['candidate']['id'],
        'status': result['candidate']['status'],
        'translated_bone_count': result['candidate']['translated_bone_count'],
        'translated_markers': len(result['candidate']['translated_joint_markers']),
        'canonical_promotion_allowed': False,
        'out': str(args.out),
    }, indent=2))


if __name__ == '__main__':
    main()
