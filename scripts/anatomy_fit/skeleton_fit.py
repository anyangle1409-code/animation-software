"""Construct the 206-bone anatomical reference skeleton from fitted character landmarks.

Pure numpy. Input: the landmark/joint-centre dictionary from `fit_character` (Blender world metres,
character facing -Y, +Z up, anatomical left = +X). Output: per bone head/tail/axis hint, tree parent,
parent relation (articular joint id or explicit carrier), role and placement class/confidence.

Placement classes (strongest first):
  regression        - joint centre from a published landmark regression
  surface_landmark  - from measured character surface features
  surface_station   - inherited from generator surface stations (no independent anatomical evidence)
  proportional      - anatomical approximation relative to fitted anchors (low confidence)
"""
import json
from pathlib import Path

import numpy as np

UP = np.array([0.0, 0.0, 1.0])
ANT = np.array([0.0, -1.0, 0.0])
DATA = Path(__file__).resolve().parents[2] / 'ORIGINAL_V1_WORK/anatomy'


def v(x):
    return np.asarray(x, float)


def unit(a):
    a = v(a)
    n = np.linalg.norm(a)
    return a / n if n > 0 else a


def lerp(a, b, t):
    return v(a) + (v(b) - v(a)) * t


def side_vec(sign):
    return np.array([sign, 0.0, 0.0])  # lateral direction for a side


class Skeleton:
    def __init__(self):
        self.bones = {}

    def add(self, bid, head, tail, parent, relation, placement, confidence, recipe, axis=None):
        head, tail = v(head), v(tail)
        if np.linalg.norm(tail - head) < 1e-4:
            raise ValueError('Degenerate reference bone ' + bid)
        self.bones[bid] = {'head_m': head.tolist(), 'tail_m': tail.tolist(), 'parent': parent,
                           'parent_relation': relation, 'placement': placement, 'confidence': confidence,
                           'recipe': recipe, 'axis_hint': (unit(axis) if axis is not None else None)}


def joint_role_index():
    inv = json.loads((DATA / 'adult_articulation_inventory.json').read_text())['articulations']
    return {j['id']: j for j in inv}


def find_joint(joints, a, b):
    hits = [j['id'] for j in joints.values() if a in j['participants'] and b in j['participants']]
    return sorted(hits)[0] if hits else None


def build(L, rig=None):
    """L: landmark dictionary with keys described in fit_character. Returns Skeleton."""
    S = Skeleton()
    joints = joint_role_index()

    def art(child, parent):
        jid = find_joint(joints, child, parent)
        return {'type': 'articular', 'joint_id': jid} if jid else None

    def add(bid, head, tail, parent, placement, confidence, recipe, axis=None, carrier_reason=None):
        rel = None
        if parent is not None:
            rel = art(bid, parent)
            if rel is None:
                if not carrier_reason:
                    raise ValueError(f'{bid}->{parent} has no inventory articulation; give a carrier reason')
                rel = {'type': 'carrier', 'joint_id': None, 'reason': carrier_reason}
        else:
            rel = {'type': 'root', 'joint_id': None, 'reason': carrier_reason or 'tree root'}
        S.add(bid, head, tail, parent, rel, placement, confidence, recipe, axis)

    T = L['trunk']
    # ------------------------------------------------------------------ spine
    levels = T['vertebral_body_centres']  # dict level -> centre (m), including 'S1' top and 'C0'
    order = ['l5', 'l4', 'l3', 'l2', 'l1'] + [f't{i}' for i in range(12, 0, -1)] + [f'c{i}' for i in range(7, 0, -1)]
    sac_top, sac_apex = T['sacrum_s1_endplate'], T['sacrum_apex']
    add('sacrum', sac_apex, sac_top, None, 'proportional', 'low',
        'S1 endplate centre from the pelvic landmarks (L5/S1 estimate) to the sacral apex; posterior to the ASIS plane.',
        carrier_reason='pelvic reference root')
    coccyx_tip = lerp(sac_apex, sac_apex + v([0, -0.02, -0.03]), 1.0)
    add('coccyx', sac_apex, coccyx_tip, 'sacrum', 'proportional', 'low', 'Sacral apex to a 36 mm anteroinferior tip.')
    prev = 'sacrum'
    for name in order:
        c = v(levels[name])
        idx = order.index(name)
        below = v(levels[order[idx - 1]]) if idx > 0 else v(sac_top)
        above = v(levels[order[idx + 1]]) if idx + 1 < len(order) else v(T['c0_c1_centre'])
        head = (below + c) / 2 if name != 'l5' else (v(sac_top) + c) / 2
        tail = (c + above) / 2
        add(name, head, tail, prev, 'proportional', 'low',
            'Vertebral body: inferior to superior endplate midpoints of an anchor-interpolated spinal curve (anchors: jugular notch=T2/T3, xiphisternal=T8/T9, C0-C1, L5/S1).',
            axis=ANT)
        prev = name
    # ------------------------------------------------------------------ skull
    Hd = L['head']
    occ_c, top, nasion, chin = v(Hd['occipital_centre']), v(Hd['vertex_skin']), v(Hd['nasion_skin']), v(Hd['chin_skin'])
    centre = v(Hd['cranial_centre'])
    add('occipital', T['c0_c1_centre'], occ_c, 'c1', 'proportional', 'low', 'Occipital condyles (C0-C1 centre) to the occipital squama centre.')
    for s, sg in (('left', 1), ('right', -1)):
        add(f'parietal_{s}', centre + v([sg * 0.045, 0.01, 0.03]), centre + v([sg * 0.055, 0.03, 0.065]), 'occipital',
            'proportional', 'low', 'Upper lateral cranial vault relative to the cranial centre.')
        add(f'temporal_{s}', v(Hd['porion_est'][s]) + v([-sg * 0.01, 0.0, 0.01]), v(Hd['porion_est'][s]) + v([-sg * 0.015, -0.03, 0.03]),
            'occipital', 'proportional', 'low', 'Petrous/squamous temporal from the estimated ear canal.')
    add('sphenoid', centre + v([0, -0.015, -0.03]), centre + v([0, -0.045, -0.025]), 'occipital', 'proportional', 'low', 'Central skull base anterior to the clivus.')
    add('frontal', centre + v([0, -0.06, 0.04]), lerp(nasion, top, 0.45) + v([0, 0.015, 0]), 'sphenoid', 'proportional', 'low', 'Forehead region behind the frontal skin.')
    add('ethmoid', nasion + v([0, 0.03, -0.01]), nasion + v([0, 0.055, -0.015]), 'sphenoid', 'proportional', 'low', 'Between the orbits behind the nasion.')
    add('vomer', nasion + v([0, 0.035, -0.035]), nasion + v([0, 0.055, -0.055]), 'sphenoid', 'proportional', 'low', 'Nasal septum.')
    for s, sg in (('left', 1), ('right', -1)):
        x = sg
        add(f'nasal_{s}', nasion + v([x * 0.004, 0.006, -0.003]), nasion + v([x * 0.006, -0.002, -0.022]), 'frontal', 'proportional', 'low', 'Nasal bridge below the nasion.')
        add(f'lacrimal_{s}', nasion + v([x * 0.016, 0.012, -0.012]), nasion + v([x * 0.016, 0.018, -0.022]), 'frontal', 'proportional', 'low', 'Medial orbital wall.')
        add(f'maxilla_{s}', nasion + v([x * 0.018, 0.012, -0.03]), nasion + v([x * 0.02, 0.02, -0.065]), 'frontal', 'proportional', 'low', 'Midface below the orbit.')
        add(f'zygomatic_{s}', nasion + v([x * 0.05, 0.02, -0.02]), nasion + v([x * 0.058, 0.04, -0.03]), 'temporal_' + s, 'proportional', 'low', 'Cheekbone lateral to the orbit.')
        add(f'palatine_{s}', nasion + v([x * 0.008, 0.045, -0.055]), nasion + v([x * 0.008, 0.06, -0.06]), 'maxilla_' + s, 'proportional', 'low', 'Posterior hard palate.')
        add(f'inferior_nasal_concha_{s}', nasion + v([x * 0.012, 0.02, -0.04]), nasion + v([x * 0.012, 0.045, -0.042]), 'maxilla_' + s, 'proportional', 'low', 'Lateral nasal wall.')
        por = v(Hd['porion_est'][s])
        add(f'malleus_{s}', por + v([-x * 0.012, 0.002, 0.0]), por + v([-x * 0.012, 0.002, -0.006]), 'temporal_' + s, 'proportional', 'low', 'Middle ear, medial to the ear canal.', carrier_reason='ossicle carried by the temporal bone via ligaments')
        add(f'incus_{s}', por + v([-x * 0.014, 0.006, 0.0]), por + v([-x * 0.014, 0.006, -0.005]), f'malleus_{s}', 'proportional', 'low', 'Middle ear.')
        add(f'stapes_{s}', por + v([-x * 0.016, 0.006, -0.004]), por + v([-x * 0.019, 0.006, -0.004]), f'incus_{s}', 'proportional', 'low', 'Middle ear, oval window.')
    tmj_mid = (v(Hd['tmj_est']['left']) + v(Hd['tmj_est']['right'])) / 2
    add('mandible', tmj_mid, chin + v([0, 0.012, 0.008]), 'temporal_left', 'proportional', 'low',
        'Condylar midpoint (bilateral TMJ estimates) to the mental region. Tree parent via tmj_left; tmj_right closes the bilateral chain through its joint marker.')
    add('hyoid', T['hyoid_est'] + v([0, 0.01, 0]), T['hyoid_est'] + v([0, -0.01, 0]), None, 'proportional', 'low',
        'Anterior neck below the mandible near C3.', carrier_reason='no osseous articulation (hyoid exception); suspended reference')
    # ------------------------------------------------------------------ thorax
    add('sternum', T['ij_bone'], T['px_bone'], 't4', 'surface_landmark', 'moderate',
        'Jugular notch to xiphisternal region, each inset from the skin.', carrier_reason='sternum joins ribs through costal cartilage (not in the 206); carrier at sternal-angle level')
    for i in range(1, 13):
        for s, sg in (('left', 1), ('right', -1)):
            r = T['ribs'][f'{i:02d}'][s]
            add(f'rib_{i:02d}_{s}', r['costovertebral'], r['anterior_end'], f't{i}', 'proportional', 'low',
                'Costovertebral joint to the anterior rib end on the inset chest-wall contour at the anchored level.')
    # ------------------------------------------------------------------ limbs
    for s, sg in (('left', 1), ('right', -1)):
        P = L['sides'][s]
        lat = side_vec(sg)
        sc, ac, gh = v(P['SC']), v(P['AC']), v(P['GH'])
        add(f'clavicle_{s}', sc, ac, 'sternum', 'surface_landmark', 'moderate', 'SC joint (lateral to the jugular notch) to the AC joint.')
        add(f'scapula_{s}', v(P['glenoid']), v(P['AI']), f'clavicle_{s}', 'surface_landmark', 'low',
            'Glenoid centre to inferior angle (from the authored medial scapular border).', axis=v(P['TS']) - v(P['AA']))
        ejc, wjc = v(P['EJC']), v(P['WJC'])
        add(f'humerus_{s}', gh, ejc, f'scapula_{s}', 'regression', 'moderate', 'GH centre (acromion depth chain) to elbow centre (ISB epicondyle midpoint).', axis=lat)
        hu, hr = v(P['humeroulnar']), v(P['humeroradial'])
        add(f'ulna_{s}', hu, v(P['ulnar_styloid_bone']), f'humerus_{s}', 'surface_landmark', 'moderate', 'Trochlear notch to ulnar head/styloid.')
        add(f'radius_{s}', hr, v(P['radial_styloid_bone']), f'humerus_{s}', 'surface_landmark', 'moderate', 'Radial head to radial styloid.')
        C = P['carpals']
        for cid, parent in [('scaphoid', f'radius_{s}'), ('lunate', f'radius_{s}'), ('triquetrum', f'lunate_{s}'), ('pisiform', f'triquetrum_{s}'),
                            ('trapezium', f'scaphoid_{s}'), ('trapezoid', f'scaphoid_{s}'), ('capitate', f'lunate_{s}'), ('hamate', f'triquetrum_{s}')]:
            add(f'{cid}_{s}', C[cid][0], C[cid][1], parent, 'proportional', 'low', 'Carpal row layout between the wrist centre and metacarpal bases.')
        Hn = P['hand']
        mc_parent = {1: 'trapezium', 2: 'trapezoid', 3: 'capitate', 4: 'hamate', 5: 'hamate'}
        for d in range(1, 6):
            add(f'metacarpal_{d}_{s}', Hn[f'mc{d}'][0], Hn[f'mc{d}'][1], f'{mc_parent[d]}_{s}', 'surface_station', 'low', 'CMC to MCP at generator finger stations.')
        add(f'thumb_proximal_phalanx_{s}', Hn['th_pp'][0], Hn['th_pp'][1], f'metacarpal_1_{s}', 'surface_station', 'low', 'Thumb MCP to IP.')
        add(f'thumb_distal_phalanx_{s}', Hn['th_dp'][0], Hn['th_dp'][1], f'thumb_proximal_phalanx_{s}', 'surface_station', 'low', 'Thumb IP to tip.')
        for d in range(2, 6):
            add(f'digit{d}_proximal_phalanx_{s}', Hn[f'd{d}_pp'][0], Hn[f'd{d}_pp'][1], f'metacarpal_{d}_{s}', 'surface_station', 'low', 'MCP to PIP.')
            add(f'digit{d}_middle_phalanx_{s}', Hn[f'd{d}_mp'][0], Hn[f'd{d}_mp'][1], f'digit{d}_proximal_phalanx_{s}', 'surface_station', 'low', 'PIP to DIP.')
            add(f'digit{d}_distal_phalanx_{s}', Hn[f'd{d}_dp'][0], Hn[f'd{d}_dp'][1], f'digit{d}_middle_phalanx_{s}', 'surface_station', 'low', 'DIP to tip.')
        add(f'hip_bone_{s}', v(P['SI']), v(P['pubic_symphysis_side']), 'sacrum', 'proportional', 'low',
            'Sacroiliac joint centre to the pubic symphysis side; acetabulum at the fitted HJC (joint marker).', axis=v(P['HJC']) - v(P['SI']))
        hjc, kjc, ajc = v(P['HJC']), v(P['KJC']), v(P['AJC'])
        add(f'femur_{s}', hjc, kjc, f'hip_bone_{s}', 'regression', 'moderate', 'HJC (Harrington/Hara mean) to KJC (ISB epicondyle midpoint).', axis=lat)
        add(f'patella_{s}', v(P['patella'])[0], v(P['patella'])[1], f'femur_{s}', 'proportional', 'low', 'Superior to inferior pole anterior to the femoral condyles, extended knee.')
        add(f'tibia_{s}', kjc, ajc, f'femur_{s}', 'surface_landmark', 'moderate',
            'KJC (epicondylar flexion-axis centre, so Blender rotation is about the knee centre) to the ankle centre; the tibial plateau is kept as a separate landmark.', axis=lat)
        add(f'fibula_{s}', v(P['fibular_head']), v(P['lateral_malleolus_bone']), f'tibia_{s}', 'proportional', 'low', 'Fibular head (posterolateral, below plateau) to lateral malleolus.')
        F = P['foot']
        add(f'talus_{s}', ajc, F['talar_head'], f'tibia_{s}', 'proportional', 'low', 'Talar dome at the ankle centre to the talar head.')
        add(f'calcaneus_{s}', F['subtalar'], F['heel_bone'], f'talus_{s}', 'proportional', 'low', 'Posterior subtalar facet to the calcaneal tuber.')
        add(f'navicular_{s}', F['navicular'][0], F['navicular'][1], f'talus_{s}', 'proportional', 'low', 'Medial midfoot in front of the talar head.')
        add(f'cuboid_{s}', F['cuboid'][0], F['cuboid'][1], f'calcaneus_{s}', 'proportional', 'low', 'Lateral midfoot in front of the calcaneus.')
        for cu in ('medial', 'intermediate', 'lateral'):
            add(f'{cu}_cuneiform_{s}', F[cu][0], F[cu][1], f'navicular_{s}', 'proportional', 'low', 'Distal tarsal row.')
        mt_parent = {1: 'medial_cuneiform', 2: 'intermediate_cuneiform', 3: 'lateral_cuneiform', 4: 'cuboid', 5: 'cuboid'}
        for t in range(1, 6):
            add(f'metatarsal_{t}_{s}', F[f'mt{t}'][0], F[f'mt{t}'][1], f'{mt_parent[t]}_{s}', 'surface_landmark', 'low', 'TMT base to metatarsal head at the measured ball line.')
        add(f'hallux_proximal_phalanx_{s}', F['hx_pp'][0], F['hx_pp'][1], f'metatarsal_1_{s}', 'surface_landmark', 'low', 'MTP to hallux IP.')
        add(f'hallux_distal_phalanx_{s}', F['hx_dp'][0], F['hx_dp'][1], f'hallux_proximal_phalanx_{s}', 'surface_landmark', 'low', 'Hallux IP to tip.')
        for t in range(2, 6):
            add(f'toe{t}_proximal_phalanx_{s}', F[f't{t}_pp'][0], F[f't{t}_pp'][1], f'metatarsal_{t}_{s}', 'surface_landmark', 'low', 'MTP to PIP along the measured toe centreline.')
            add(f'toe{t}_middle_phalanx_{s}', F[f't{t}_mp'][0], F[f't{t}_mp'][1], f'toe{t}_proximal_phalanx_{s}', 'surface_landmark', 'low', 'PIP to DIP.')
            add(f'toe{t}_distal_phalanx_{s}', F[f't{t}_dp'][0], F[f't{t}_dp'][1], f'toe{t}_middle_phalanx_{s}', 'surface_landmark', 'low', 'DIP to tip.')
    return S


MIDLINE = None


def is_midline(bid):
    return not (bid.endswith('_left') or bid.endswith('_right'))


def enforce_midline(S):
    for bid, b in S.bones.items():
        if is_midline(bid):
            b['head_m'][0] = 0.0
            b['tail_m'][0] = 0.0
    return S


def contain(S, clearance, margin=0.003, anchors=None):
    """Pull low-confidence placements inside the body surface with a margin.

    clearance(p) returns signed distance to the skin (positive inside). Points of 'proportional' and
    'surface_station' bones that are outside or closer than `margin` move along the line toward an
    anchor (the other endpoint, or a supplied interior anchor such as the cranial centre). Every move
    is recorded on the bone; measured/regression placements are never moved.
    """
    anchors = anchors or {}
    for bid, b in S.bones.items():
        if b['placement'] not in ('proportional', 'surface_station'):
            continue
        moves = {}
        for key, other in (('head_m', 'tail_m'), ('tail_m', 'head_m')):
            p = np.asarray(b[key], float)
            if clearance(p) >= margin:
                continue
            anchor = np.asarray(anchors.get(bid, b[other]), float)
            if clearance(anchor) < margin:
                anchor = np.asarray(anchors.get('__fallback__', anchor), float)
            for t in np.linspace(0.02, 1.0, 50):
                q = p + (anchor - p) * t
                if clearance(q) >= margin:
                    break
            moves[key] = float(np.linalg.norm(q - p))
            b[key] = q.tolist()
        if moves:
            b['containment_adjustment_m'] = moves
    return S


def assign_roles(S):
    joints = joint_role_index()
    for bid, b in S.bones.items():
        rel = b['parent_relation']
        if bid == 'hyoid':
            b['role'] = 'REFERENCE'
        elif rel['type'] == 'articular':
            b['role'] = joints[rel['joint_id']]['role']
        elif rel['type'] == 'root':
            b['role'] = 'ACTIVE'
        else:
            b['role'] = 'FOLLOWER' if bid == 'sternum' else 'FIXED'   # sternum follows the rib cage; malleus is ligament-suspended
    return S
