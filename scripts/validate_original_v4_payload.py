"""Independent structural gate for the project-authored Blender rig handoff."""
import math

CENTER = {'root': None, 'pelvis': 'root', 'spine_01': 'pelvis',
          'spine_02': 'spine_01', 'spine_03': 'spine_02',
          'neck': 'spine_03', 'head': 'neck'}
SIDE = {'clavicle': 'spine_03', 'scapula': 'clavicle',
        'upperarm': 'scapula', 'forearm': 'upperarm', 'hand': 'forearm',
        'thigh': 'pelvis', 'shin': 'thigh', 'foot': 'shin', 'toe': 'foot'}
for finger in ('thumb', 'index', 'middle', 'ring', 'pinky'):
    if finger != 'thumb':
        SIDE[f'metacarpal_{finger}'] = 'hand'
    SIDE[f'{finger}_01'] = 'hand' if finger == 'thumb' else f'metacarpal_{finger}'
    SIDE[f'{finger}_02'] = f'{finger}_01'
    SIDE[f'{finger}_03'] = f'{finger}_02'

EXPECTED = CENTER | {
    f'{name}_{side}': (f'{parent}_{side}' if parent not in CENTER else parent)
    for side in ('l', 'r') for name, parent in SIDE.items()
}


def validate(data):
    errors = []
    if data.get('identity') != 'hgpt_canonical_v4_original':
        errors.append('identity')
    if data.get('coordinate_system') != 'project_x_right_y_up_z_forward':
        errors.append('coordinate system')
    bones = data.get('bones', [])
    if len(bones) != 63:
        errors.append('bone count')
    by_name = {b.get('name'): b for b in bones if isinstance(b, dict)}
    if set(by_name) != set(EXPECTED) or len(by_name) != len(bones):
        errors.append('exact bone names')
    for name, parent in EXPECTED.items():
        bone = by_name.get(name)
        if bone is None:
            continue
        if bone.get('parent') != parent:
            errors.append(f'{name} parent')
        head, tail = bone.get('head'), bone.get('tail')
        if not all(isinstance(v, list) and len(v) == 3 and all(isinstance(x, (int, float)) and math.isfinite(x) for x in v) for v in (head, tail)):
            errors.append(f'{name} coordinates')
            continue
        if math.dist(head, tail) <= .004:
            errors.append(f'{name} degenerate')
        if name.endswith('_l') and name[:-2] + '_r' in by_name:
            opposite = by_name[name[:-2] + '_r']
            if any(not isinstance(opposite.get(k), list) or len(opposite[k]) != 3 or
                   any(abs(a - b * sign) > 1e-9 for a, b, sign in zip(bone[k], opposite[k], (-1, 1, 1)))
                   for k in ('head', 'tail')):
                errors.append(f'{name} mirror')
    if 'head' in by_name and abs(by_name['head']['tail'][1] - 1.82) > 1e-9:
        errors.append('target height')
    for name, width in (('upperarm_l', .430), ('thigh_l', .184)):
        if name in by_name and abs(-2 * by_name[name]['head'][0] - width) > 1e-9:
            errors.append('shoulder joint breadth' if name == 'upperarm_l' else 'hip joint breadth')
    lengths = {
        'upperarm_l': .325, 'forearm_l': .270, 'hand_l': .095,
        'thigh_l': .445, 'shin_l': .430,
        'metacarpal_index_l': .070, 'metacarpal_middle_l': .072,
        'metacarpal_ring_l': .066, 'metacarpal_pinky_l': .058,
    }
    for finger, segments in {
        'thumb': (.048, .031, .024), 'index': (.045, .027, .020),
        'middle': (.049, .030, .022), 'ring': (.046, .028, .021),
        'pinky': (.036, .022, .018),
    }.items():
        lengths.update({f'{finger}_0{i}_l': length for i, length in enumerate(segments, 1)})
    for name, length in lengths.items():
        if name in by_name and abs(math.dist(by_name[name]['head'], by_name[name]['tail']) - length) > 1e-9:
            errors.append(f'{name} target length')
    return errors
