#!/usr/bin/env python3
"""Read-only queue of unsupported amplitudes; never converts test peaks into ROM limits."""
import argparse
import json
import re
from pathlib import Path

import amplitude_provenance_audit as provenance

FAMILIES = {
    'hip_frontal': ('hip_abduction_adduction_',
        'Match hip/pelvis frames, posture, passive versus active protocol and population; clinical means are not hard limits.'),
    'talocrural': ('talocrural_dorsi_plantarflexion_',
        'Isolate talus/tibia motion from ankle-foot complex and specify knee posture and loading.'),
    'subtalar': ('subtalar_inversion_eversion_',
        'Obtain talus/calcaneus motion with documented axis, not whole-foot inversion/eversion.'),
    'gh_elevation': ('gh_elevation_plane_',
        'Separate humerus/scapula elevation from humerothoracic elevation; specify plane and scapular coupling.'),
    'gh_rotation': ('gh_axial_rotation_at_',
        'Match scapular reference, arm elevation and rotation direction; verify coupled translation/contact.'),
    'finger_extension': ('digit[2-5]_flexion_(left|right)$',
        'Source MCP/PIP/DIP extension separately; negative ten percent of flexion means has no physiological basis.'),
    'thumb_opposition': ('thumb_opposition_',
        'Separate CMC pronation from composite opposition; validate task-dependent coupling and coordinate definition.'),
    'rib_inspiration': ('rib',
        'Source rib-specific thoracic rotation/translation versus lung volume and posture; costal contacts remain unverified.'),
    'hallux_plantarflexion': ('hallux_mtp_dorsiflexion_',
        'Obtain plantarflexion evidence distinct from dorsiflexion and specify weight-bearing and measurement endpoints.'),
    'knee_conditioning': ('knee_flexion_with_',
        'These are conditioning poses for screw-home/follower tests, not proposed maximum knee ROM; source couplings versus angle.'),
    'cervical_segment': ('cervical_c4_c5_',
        'Source C4/C5 segment-specific axial/frontal motion; whole-neck ranges cannot be assigned to one segment.'),
    'tmj': ('tmj_opening',
        'Source condylar rotation and translation as a coupled trajectory; inter-incisor opening is not condylar glide.'),
}


def build(specs):
    rows = []
    for t in specs:
        classified = provenance.classify(t)
        if any(r['kind'] == 'UNTRACED' for r in classified):
            raise ValueError(f"untraced amplitude requires explicit review: {t['id']}")
        unsupported = [r for r in classified if r['kind'] == 'LABELLED_TEST_AMPLITUDE']
        if not unsupported:
            continue
        matches = [(name, blocker) for name, (pattern, blocker) in FAMILIES.items() if re.match(pattern, t['id'])]
        if len(matches) != 1:
            raise ValueError(f"unmapped unsupported motion family: {t['id']}")
        family, blocker = matches[0]
        for r in unsupported:
            if family == 'finger_extension' and (r['channel'] not in ('mcp', 'pip', 'dip') or r['peak'] >= 0):
                raise ValueError(f"unmapped finger extension semantics: {t['id']} {r['channel']} {r['peak']}")
            row = {'test': t['id'], 'channel': r['channel'], 'peak': r['peak'],
                   'units': 'm' if r['channel'] in provenance.LENGTH_CHANNELS else 'deg',
                   'family': family, 'role': 'conditioning_pose' if family == 'knee_conditioning' else 'diagnostic_excursion',
                   'status': 'UNSOURCED_TEST_AMPLITUDE', 'blocker': blocker,
                   'recorded_basis': t.get('amplitude_basis'), 'replacement_authorized_by_this_report': False}
            if row['units'] == 'm':
                row['peak_mm'] = row['peak'] * 1000
            rows.append(row)
    counts = {name: sum(r['family'] == name for r in rows) for name in FAMILIES}
    return {'schema_version': 1, 'kind': 'READ_ONLY_MOVEMENT_EVIDENCE_QUEUE',
            'peak_count': len(rows), 'test_count': len({r['test'] for r in rows}), 'by_family': counts,
            'anatomical_acceptance': False, 'existing_limits_changed': False, 'peaks': rows}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--record', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    atlas = json.loads((provenance.ROOT / 'ORIGINAL_V1_WORK/anatomy/whole_body_movement_atlas.json').read_text())
    rec = json.loads(Path(args.record).read_text())
    result = build(provenance.it.specs(rec, atlas))
    result['record_sha256'] = provenance.sha(args.record)
    result['atlas_sha256'] = provenance.sha(provenance.ROOT / 'ORIGINAL_V1_WORK/anatomy/whole_body_movement_atlas.json')
    content = json.dumps(result, indent=2, allow_nan=False) + '\n'
    with Path(args.out).open('x') as f:
        f.write(content)
    print(json.dumps({k: result[k] for k in ('peak_count', 'test_count', 'by_family')}))


if __name__ == '__main__':
    main()
