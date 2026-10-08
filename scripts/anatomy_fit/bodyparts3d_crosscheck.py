#!/usr/bin/env python3
"""Single-specimen layout cross-check from BodyParts3D 4.0 (via the ashemag/human-atlas packing).

Read-only evidence extraction. BodyParts3D is ONE adult male reference anatomy (TARO MRI with illustration
refinement; CC BY 4.0, (c) Database Center for Life Science). One specimen cannot set a population target:
everything here is a layout template / plausibility cross-check, never a frozen value.

Input: a directory with the packed atlas (public/models/atlas.json + body-N.bin), passed as an argument and
only parsed as data (JSON + little-endian float32/uint32 buffers).
Atlas axes: metres, left +x, superior +y, anterior +z. HGPT: left +X, anterior -Y, superior +Z.

  bodyparts3d_crosscheck.py MODELS_DIR --commit SHA --out JSON
"""
import argparse, hashlib, json, math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
TO_HGPT = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float)      # det +1: proper rotation, no mirror
CARPALS = {'scaphoid': 'scaphoid', 'lunate': 'lunate', 'triquetrum': 'triquetral', 'pisiform': 'pisiform',
           'trapezium': 'trapezium', 'trapezoid': 'trapezoid', 'capitate': 'capitate', 'hamate': 'hamate'}
TARSALS = {'talus': '{S} talus', 'calcaneus': '{S} calcaneus', 'navicular': 'Navicular bone of {s} foot',
           'cuboid': '{S} cuboid bone', 'medial_cuneiform': '{S} medial cuneiform bone',
           'intermediate_cuneiform': '{S} intermediate cuneiform bone', 'lateral_cuneiform': '{S} lateral cuneiform bone'}
ORDINAL = ['first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth', 'eleventh', 'twelfth']


class Atlas:
    def __init__(self, models_dir):
        self.dir = Path(models_dir)
        self.meta = json.loads((self.dir / 'atlas.json').read_text())
        self.bins = {}

    def mesh(self, name):
        parts = {p['id']: p for p in self.meta['parts'] if p['name'] == name and p['system'] == 'skeletal'}
        if len(parts) != 1:
            raise ValueError(f'{name}: expected one skeletal mesh, found {len(parts)}')
        p = next(iter(parts.values()))
        if p['chunk'] not in self.bins:
            self.bins[p['chunk']] = (self.dir / f'body-{p["chunk"]}.bin').read_bytes()
        b = self.bins[p['chunk']]
        v = np.frombuffer(b, '<f4', p['vertexCount'] * 3, p['positions']).reshape(-1, 3).astype(float)
        f = np.frombuffer(b, '<u4', p['indexCount'], p['indices']).reshape(-1, 3).astype(np.int64)
        return (v @ TO_HGPT.T) * 1000.0, f, p['id']


def weld(v, f, decimals=4):
    """Merge coincident vertices (split normals duplicate positions); mm rounded to 1e-4."""
    key, inv = np.unique(np.round(v, decimals), axis=0, return_inverse=True)
    f = inv.reshape(-1)[f]
    f = f[(f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 0] != f[:, 2])]
    return key, f


def edge_counts(f):
    e = np.sort(np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), axis=1)
    return np.unique(e, axis=0, return_counts=True)


def shape(v, f):
    """Welded mesh: volume centroid and volume (exact if closed, approximate if open), principal axes, extents (mm)."""
    v, f = weld(v, f)
    _, n = edge_counts(f)
    is_closed = bool(np.all(n == 2))
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    area = np.linalg.norm(np.cross(b - a, c - a), axis=1) / 2
    ref = (area[:, None] * (a + b + c) / 3).sum(0) / area.sum()
    a0, b0, c0 = a - ref, b - ref, c - ref
    vol6 = np.einsum('ij,ij->i', a0, np.cross(b0, c0))
    volume = vol6.sum() / 6
    centroid = ref + (vol6[:, None] * (a0 + b0 + c0)).sum(0) / (4 * vol6.sum())
    w, U = np.linalg.eigh(np.cov((v - centroid).T))
    U = U[:, ::-1]
    proj = (v - centroid) @ U
    return {'closed': is_closed, 'boundary_edge_fraction': float(np.mean(n == 1)), 'centroid_mm': centroid,
            'volume_mm3': abs(volume), 'principal_axes': U.T, 'extents_mm': proj.max(0) - proj.min(0)}


def _geodesic(v, f, src):
    import heapq
    e, _ = edge_counts(f)
    L = np.linalg.norm(v[e[:, 0]] - v[e[:, 1]], axis=1)
    adj = [[] for _ in range(len(v))]
    for (i, j), w in zip(e.tolist(), L.tolist()):
        adj[i].append((j, w)); adj[j].append((i, w))
    d = np.full(len(v), np.inf); d[src] = 0; h = [(0.0, src)]
    while h:
        dist, i = heapq.heappop(h)
        if dist > d[i]:
            continue
        for j, w in adj[i]:
            if dist + w < d[j]:
                d[j] = dist + w; heapq.heappush(h, (d[j], j))
    return d


def rib_curve(v, f, bins=48):
    """Centreline by geodesic ordering on the welded surface: the two geodesically farthest vertices are the rib ends;
    vertices are binned by (d_A - d_B), and bin means form the centreline. Oriented head side (medial, posterior) first."""
    v, f = weld(v, f)
    d0 = _geodesic(v, f, 0)
    if not np.all(np.isfinite(d0)):
        raise ValueError('rib surface is not one connected component')
    A = int(np.argmax(d0)); dA = _geodesic(v, f, A); B = int(np.argmax(dA)); dB = _geodesic(v, f, B)
    t = dA - dB
    edges = np.linspace(t.min(), t.max(), bins + 1)
    pts = np.array([v[(t >= lo) & (t <= hi)].mean(0) for lo, hi in zip(edges[:-1], edges[1:]) if np.any((t >= lo) & (t <= hi))])
    head_score = lambda q: abs(q[0]) - q[1]                         # medial and posterior (+Y) -> head side
    return (pts if head_score(pts[0]) < head_score(pts[-1]) else pts[::-1]), 'geodesic'


def r(x, n=2):
    return [round(float(y), n) for y in x] if hasattr(x, '__len__') else round(float(x), n)


def build(models_dir, commit):
    at = Atlas(models_dir)
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(models_dir).glob('*')) if p.suffix in ('.json', '.bin')
              and (p.name == 'atlas.json' or int(p.stem.split('-')[1]) in {q['chunk'] for q in at.meta['parts'] if q['system'] == 'skeletal'})}
    sk = [p['name'] for p in at.meta['parts'] if p['system'] == 'skeletal']
    zs = []
    for n in set(sk):
        try:
            zs.append(at.mesh(n)[0][:, 2])
        except ValueError:
            pass
    zall = np.concatenate(zs)
    out = {'schema_version': 1, 'created': '2026-10-08',
           'status': 'SINGLE_SPECIMEN_LAYOUT_CROSSCHECK_NOT_A_TARGET',
           'evidence_grade_note': 'One reference male (BodyParts3D 4.0: TARO MRI plus illustration refinement). Grade D for any population '
                                  'target: may support layout plausibility and frame/contact topology only. Never freeze a value from it.',
           'source': {'id': 'BODYPARTS3D_4_0', 'citation': 'Mitsuhashi N et al. BodyParts3D: 3D structure database for anatomical concepts. '
                      'Nucleic Acids Res. 2009;37:D782-D785. doi:10.1093/nar/gkn613',
                      'license': 'CC BY 4.0, (c) The Database Center for Life Science (dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html)',
                      'access_path': f'https://github.com/ashemag/human-atlas at {commit}, public/models',
                      'packing_adaptations': 'mm/Z-up to m/Y-up rigid conversion, translation, meshoptimizer simplification with 0.2% '
                                             'relative error per structure (human-atlas ATTRIBUTION.md)',
                      'file_sha256': hashes,
                      'why_not_primary': 'dbarchive.biosciencedbc.jp, SimTK, Zenodo and journal hosts are blocked in this environment.'},
           'frame': 'HGPT axes (left +X, anterior -Y, superior +Z), mm; origin is the atlas stage origin (arbitrary). Use differences only.',
           'specimen_scale': {'skeleton_vertical_extent_mm': r(zall.max() - zall.min(), 1),
                              'note': 'Bony vertex-to-lowest-foot extent, not stature (no scalp or heel pad).'}}

    carp = {}
    for side in ('left', 'right'):
        S = side.capitalize()
        carp[side] = {k: shape(*at.mesh(f'{S} {n}')[:2]) for k, n in CARPALS.items()}
    tars = {}
    for side in ('left', 'right'):
        tars[side] = {k: shape(*at.mesh(n.format(S=side.capitalize(), s=side))[:2]) for k, n in TARSALS.items()}

    def table(d):
        return {side: {k: {'closed_mesh': s['closed'], 'boundary_edge_fraction': r(s['boundary_edge_fraction'], 4), 'centroid_mm': r(s['centroid_mm']),
                           'volume_mm3_approx': r(s['volume_mm3'], 0),
                           'principal_extents_mm': r(s['extents_mm']),
                           'principal_axis_1': r(s['principal_axes'][0], 4)} for k, s in b.items()} for side, b in d.items()}

    out['carpals'] = table(carp)
    out['tarsals'] = table(tars)

    # rib centrelines
    ribs = {}
    for side in ('left', 'right'):
        for i, o in enumerate(ORDINAL, 1):
            v, f, _ = at.mesh(f'{side.capitalize()} {o} rib')
            c, mode = rib_curve(v, f)
            arc = float(np.linalg.norm(np.diff(c, axis=0), axis=1).sum())
            ribs[f'rib_{i:02d}_{side}'] = {'posterior_end_mm': r(c[0]), 'anterior_end_mm': r(c[-1]),
                                            'centreline_arc_mm': r(arc, 1), 'end_chord_mm': r(np.linalg.norm(c[-1] - c[0]), 1), 'parameterisation': mode,
                                            'centreline_mm': [r(p, 1) for p in c]}
    out['ribs'] = {'method': 'Welded surface; the two geodesically farthest vertices define the ends; vertices binned (48) by the '
                             'difference of geodesic distances to the two ends; bin means form the centreline. Ends are bin means, not '
                             'head/tubercle/costochondral landmarks: the two end bins are biased by up to about the bone thickness (synthetic '
                             'tube test: interior bins within 0.5 mm, ends within one radius), so arc and chord run short of true values.',
                   'per_rib': ribs}
    out['crosschecks'] = crosschecks(carp, tars, ribs)
    return out


def crosschecks(carp, tars, ribs):
    plan = json.loads((ANAT / 'canonical_carpal_geometry_plan_v1.json').read_text())['source_constraints']
    env = json.loads((ANAT / 'canonical_carpal_envelopes_v1.json').read_text())['envelopes']
    tar = json.loads((ANAT / 'canonical_tarsal_geometry_audit_v1.json').read_text())['direct_whole_bone_reference_examples_mm']
    res = {}
    for side, b in carp.items():
        cap_axis = b['capitate']['extents_mm'][0]
        d = lambda x, y: float(np.linalg.norm(b[x]['centroid_mm'] - b[y]['centroid_mm']))
        ct, ht = 100 * d('capitate', 'triquetrum') / cap_axis, 100 * d('hamate', 'triquetrum') / cap_axis
        (m1, s1), (m2, s2) = (plan['centroid_spacing'][k] for k in ('capitate_triquetrum_distance_over_capitate_axis',
                                                                    'hamate_triquetrum_distance_over_capitate_axis'))
        vols = {k: s['volume_mm3'] for k, s in b.items()}
        by_vol = sorted(vols, key=lambda k: -vols[k])
        by_len = sorted(b, key=lambda k: -b[k]['extents_mm'][0])
        sorted_dims = {}
        for k, e in env.items():
            src = sorted((e[a]['mean_mm'], e[a]['sd_mm']) for a in ('X', 'Y', 'Z'))
            mine = sorted(b[k]['extents_mm'])
            sorted_dims[k] = [r((x - m) / s) for x, (m, s) in zip(mine, src)]
        res[f'carpal_{side}'] = {
            'canovas_capitate_triquetrum_pct': {'specimen': r(ct, 1), 'source_mean_sd': [m1, s1], 'z': r((ct - m1) / s1)},
            'canovas_hamate_triquetrum_pct': {'specimen': r(ht, 1), 'source_mean_sd': [m2, s2], 'z': r((ht - m2) / s2)},
            'capitate_axis_definition': 'first principal extent of the capitate (stand-in for the source capitate axis length)',
            'patterson_order': plan['size_hierarchy']['order'], 'specimen_order_by_volume': by_vol,
            'specimen_order_by_principal_length': by_len,
            'asseln_sorted_extent_z': sorted_dims,
            'asseln_note': 'Axis-agnostic: smallest/middle/largest specimen principal extent against smallest/middle/largest source '
                           'bounding-box mean (source axes are not mapped to HGPT). Principal extents are not bounding-box sides.'}
    for side, b in tars.items():
        rows = {}
        for k, key in (('talus', 'talus_length_male'), ('calcaneus', 'calcaneus_axial_length_male'), ('cuboid', 'cuboid_length')):
            L, ref = b[k]['extents_mm'][0], tar[key]
            rows[k] = {'specimen_first_principal_extent_mm': r(L, 1), 'source': ref,
                       'z': r((L - ref['mean']) / ref['sd']) if ref.get('sd') else None}
        vols = {k: s['volume_mm3'] for k, s in b.items()}
        rows['order_by_volume'] = sorted(vols, key=lambda k: -vols[k])
        rows['note'] = 'First principal extent approximates, but is not, each source length definition.'
        res[f'tarsal_{side}'] = rows
    hol = json.loads((ANAT / 'rib_demographic_model_holcombe2017_v1.json').read_text())['levels']
    res['rib_span_vs_holcombe2017'] = {
        'note': 'Specimen end chord (between centreline bin means) against Holcombe 2017 Table A1 population Sx (end-to-end span; '
                'adults of both sexes, ages 20-99). Bin-mean ends sit inside the true ends, so the chord is biased short.',
        'levels': {f'rib_{i:02d}': {'specimen_left_right_mm': [ribs[f'rib_{i:02d}_left']['end_chord_mm'], ribs[f'rib_{i:02d}_right']['end_chord_mm']],
                                    'source_mean_sd_mm': [hol[str(i)]['population_mean']['Sx_mm'], hol[str(i)]['population_sd']['Sx_mm']],
                                    'z_left_right': [r((ribs[f'rib_{i:02d}_{sd}']['end_chord_mm'] - hol[str(i)]['population_mean']['Sx_mm'])
                                                       / hol[str(i)]['population_sd']['Sx_mm']) for sd in ('left', 'right')]}
                   for i in range(1, 13)}}
    res['rib_bilateral'] = {f'rib_{i:02d}': r(ribs[f'rib_{i:02d}_left']['centreline_arc_mm'] - ribs[f'rib_{i:02d}_right']['centreline_arc_mm'], 1)
                            for i in range(1, 13)}
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('models_dir')
    ap.add_argument('--commit', required=True)
    ap.add_argument('--out', required=True)
    o = ap.parse_args()
    out = build(o.models_dir, o.commit)
    Path(o.out).write_text(json.dumps(out, indent=1) + '\n')
    print(json.dumps(out['crosschecks'], indent=1)[:4000])


if __name__ == '__main__':
    main()
