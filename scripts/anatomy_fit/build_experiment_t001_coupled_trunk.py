#!/usr/bin/env python3
"""T001: isolated EXPERIMENTAL coupled trunk rebuild (U10 + U5). NOT a candidate, NOT canonical, not c005.

Owner approval 2026-10-09: "isolated experimental coupled trunk rebuild addressing U10 and U5 ... do not simply lower the
entire ribcage by an arbitrary amount; resolve the anatomical relationships and document missing evidence".

What is held fixed (and why)
  * sacrum (pelvic ring; its position against the P1 S1 frame is a separate pelvic question) and its tail = S1 centre;
  * C2, C1, skull, hyoid (head height is set by stature; the head geometry is a separate region);
  * sternum, clavicles, scapulae, arms: c003/c004 already placed the bony jugular notch at the ANSUR suprasternale height
    (1494.5 mm at 1.82 m) and solved the girdle relative to it; the SC joints hang from the sternum.
What is solved
  * The C2-S1 column as a sagittal chain of explicit bodies and discs with sourced heights
      lumbar  bodies/discs  Hegazy 2014 male MRI edge means; T12/L1 LUMBAR_DISC_CT_2018; L5/S1 Hegazy edge mean
      thoracic bodies THORACIC_CT_2016 (source B, ANSUR-compatible; source A rejected), discs THORACIC_BODY_DISC_2011
      cervical bodies/discs Yukawa 2012 male; C7/T1 4.5 mm (THORACIC_BODY_DISC_2011)
    times ONE stature scale s (the source cohorts' statures are not recorded); and the sagittal angles
      SS  sacral slope (start of the chain)      prior Hasegawa male 40.9 +/- 9.6 deg
      LL  L1-S1 lordosis, Kim/Fang level pattern prior 56.4 +/- 12.7 deg
      TK  T1-T12 kyphosis                       prior 43.7 +/- 9.0 deg
      CL  C2-C7 lordosis, Reinhold level pattern prior -0.6 +/- 8.6 deg (Hasegawa male; Reinhold mean 9.6 reported)
    minimising the sum of squared z-scores subject to the chain ending exactly at the fixed C2 inferior endplate.
    Thoracic per-level shape: NOT sourced (tables unreachable); c004's own thoracic shape is kept and only its total is
    scaled to TK. Recorded as a limitation, not evidence.
  * Ribs: each rib's head stays rigidly attached to its articular level (rib 1, 10-12: own vertebra; ribs 2-9: the
    T(n-1)/T(n) disc level, rotation = mean of the two vertebrae). The rib is a rigid bone (chord length kept); ribs 1-10
    re-aim at their unchanged c004 anterior end (sternum/costal cartilage fixed), so the residual is a costal-cartilage
    length change, reported per rib. Floating ribs 11-12 move rigidly with their vertebra.
  * Markers: rib markers move with their rib; disc/facet markers to the new gap midpoints; vertebral frames rotate.

  build_experiment_t001_coupled_trunk.py --out-dir DIR [--cervical-prior hasegawa|reinhold]
"""
import argparse, copy, hashlib, json, math
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parents[2]
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
BASE = ANAT / 'audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json'
BASE_SHA = '99500d94e06c66ca'
LUMBAR = ['l5', 'l4', 'l3', 'l2', 'l1']
THOR = [f't{i}' for i in range(12, 0, -1)]
CERV = ['c7', 'c6', 'c5', 'c4', 'c3']
CHAIN = LUMBAR + THOR + CERV
PRIORS = {'SS': (40.9, 9.6), 'LL': (56.4, 12.7), 'TK': (43.7, 9.0), 'CL_hasegawa': (-0.6, 8.6), 'CL_reinhold': (9.6, 8.6)}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def lean(h, t):
    return math.degrees(math.atan2(-(t[1] - h[1]), t[2] - h[2]))


def rx(deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    # rotation about +X that increases the anterior lean (axis (y,z) = (-sin, cos))
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def heights():
    stack = json.loads((ANAT / 'canonical_spine_level_stack_v1.json').read_text())
    edges = json.loads((ANAT / 'canonical_lumbar_edge_height_crosscheck_v1.json').read_text())
    props = json.loads((ANAT / 'canonical_proportion_sources_v1.json').read_text())

    def find(x, sid):
        if isinstance(x, dict):
            if x.get('id') == sid:
                return x
            for v in x.values():
                r = find(v, sid)
                if r is not None:
                    return r
        if isinstance(x, list):
            for v in x:
                r = find(v, sid)
                if r is not None:
                    return r
    srcB = find(props, 'THORACIC_CT_2016_INDIA')['body_height_anterior_posterior_mm']
    em = lambda e: (e['anterior_mean_mm'] + e['posterior_mean_mm']) / 2
    body = {f'l{i}': em(edges['body_edge_heights'][f'L{i}']) for i in range(1, 6)}
    body.update({f't{i}': sum(srcB[f'T{i}']) / 2 for i in range(1, 13)})
    body.update({f'c{i}': stack['vertebral_bodies_mm'][f'C{i}']['candidate'] for i in range(3, 8)})
    disc = {('sacrum', 'l5'): em(edges['disc_edge_gaps']['L5/S1'])}
    for a, b in [('l5', 'l4'), ('l4', 'l3'), ('l3', 'l2'), ('l2', 'l1')]:
        disc[(a, b)] = em(edges['disc_edge_gaps'][f'{b.upper()}/{a.upper()}'])
    disc[('l1', 't12')] = stack['disc_gaps_mm']['T12/L1']['candidate']
    for i in range(12, 1, -1):
        disc[(f't{i}', f't{i - 1}')] = stack['disc_gaps_mm'][f'T{i - 1}/T{i}']['candidate']
    disc[('t1', 'c7')] = stack['disc_gaps_mm']['C7/T1']['candidate']
    for a, b in [('c7', 'c6'), ('c6', 'c5'), ('c5', 'c4'), ('c4', 'c3'), ('c3', 'c2')]:
        disc[(a, b)] = stack['disc_gaps_mm'][f'{b.upper()}/{a.upper()}']['candidate']
    return body, disc


class Chain:
    def __init__(self, base):
        B = base['bones']
        self.B = B
        self.start = np.array(B['sacrum']['tail_m']) * 1000
        self.end = np.array(B['c2']['head_m']) * 1000
        self.body, self.disc = heights()
        fr = json.loads((ANAT / 'canonical_lumbar_body_disc_frames_p1.json').read_text())['geometry']
        ang = lambda n: math.degrees(math.atan2(-n[1], n[2]))
        self.sup = {k: ang(v['normal']) for k, v in fr['superior_frames'].items()}
        self.inf = {k: ang(v['normal']) for k, v in fr['inferior_frames'].items()}
        c = {n: lean(B[n]['head_m'], B[n]['tail_m']) for n in THOR}
        self.tshape = {n: (c[n] - c['t12']) / (c['t1'] - c['t12']) for n in THOR}           # c004 shape, 0 at T12, 1 at T1
        align = json.loads((ANAT / 'canonical_spine_sagittal_alignment_v1.json').read_text())
        lv = align['cervical_segment_family']['levels']
        self.cpat = {k: v['mean'] / align['cervical_segment_family']['total_C2_C7_deg'] for k, v in lv.items()}   # shares, sum 1

    def elements(self, SS, LL, TK, CL):
        """[(name, kind, height_mm, lean_deg)] from S1 upward. Leans: + = superior end anterior."""
        k = LL / 56.4
        lump = lambda a: SS + (a - 40.9) * k                                   # P1 pattern rescaled to SS/LL
        E = []
        below = 'S1'
        for v in LUMBAR:
            V = v.upper()
            E.append(((below.lower() if below != 'S1' else 'sacrum', v), 'disc', self.disc[('sacrum' if below == 'S1' else below.lower(), v)],
                      (lump(self.inf[V]) + lump(self.sup[below])) / 2))
            E.append((v, 'body', self.body[v], (lump(self.inf[V]) + lump(self.sup[V])) / 2))
            below = V
        l1s = lump(self.sup['L1'])
        E.append((('l1', 't12'), 'disc', self.disc[('l1', 't12')], l1s))
        tang = {n: l1s + TK * self.tshape[n] for n in THOR}
        for i, n in enumerate(THOR):
            E.append((n, 'body', self.body[n], tang[n]))
            if n != 't1':
                nxt = THOR[i + 1]
                E.append(((n, nxt), 'disc', self.disc[(n, nxt)], (tang[n] + tang[nxt]) / 2))
        phi = tang['t1']
        E.append((('t1', 'c7'), 'disc', self.disc[('t1', 'c7')], phi))
        seg = {'c7': 'C6/C7', 'c6': 'C5/C6', 'c5': 'C4/C5', 'c4': 'C3/C4', 'c3': 'C2/C3'}
        for i, n in enumerate(CERV):
            E.append((n, 'body', self.body[n], phi))
            d = -CL * self.cpat[seg[n]]                    # lordosis turns the upper level posteriorly (lean decreases)
            nxt = CERV[i + 1] if i + 1 < len(CERV) else 'c2'
            E.append(((n, nxt), 'disc', self.disc[(n, nxt)], phi + d / 2))
            phi += d
        return E

    def walk(self, x):
        SS, LL, TK, CL, s = x
        p = self.start.copy(); pts = []
        for name, kind, h, phi in self.elements(SS, LL, TK, CL):
            a = p.copy(); r = math.radians(phi)
            p = p + s * h * np.array([0, -math.sin(r), math.cos(r)])
            pts.append((name, kind, a, p.copy(), phi))
        return pts


def solve(chain, cl_key):
    pri = [PRIORS['SS'], PRIORS['LL'], PRIORS['TK'], PRIORS[cl_key]]
    f = lambda x: sum(((x[i] - m) / sd) ** 2 for i, (m, sd) in enumerate(pri))
    def closure(x):
        e = chain.walk(x)[-1][3]
        return [e[1] - chain.end[1], e[2] - chain.end[2]]
    x0 = [m for m, _ in pri] + [1.0]
    r = minimize(f, x0, constraints=[{'type': 'eq', 'fun': closure}], method='SLSQP', options={'ftol': 1e-12, 'maxiter': 500})
    assert r.success, r.message
    assert max(abs(v) for v in closure(r.x)) < 1e-6
    return r.x, f(r.x), pri


def build(cl_key='CL_hasegawa'):
    assert sha(BASE).startswith(BASE_SHA)
    base = json.loads(BASE.read_text()); out = copy.deepcopy(base)
    B, J = out['bones'], out['joint_markers']
    ch = Chain(base)
    x, chi2, pri = solve(ch, cl_key)
    pts = ch.walk(x)
    T = {}                                              # per vertebra rigid transform (R, t) in metres: p' = R p + t
    old = {n: (np.array(B[n]['head_m']), np.array(B[n]['tail_m'])) for n in CHAIN}
    gaps = {}
    for name, kind, a, b, phi in pts:
        if kind == 'body':
            n = name; h0, t0 = old[n]
            nh, nt = a / 1000, b / 1000
            R = rx(phi - lean(h0, t0))
            t = (nh + nt) / 2 - R @ ((h0 + t0) / 2)
            T[n] = (R, t)
            B[n]['head_m'], B[n]['tail_m'] = nh.tolist(), nt.tolist()
        else:
            gaps[name] = ((a + b) / 2000, float(np.linalg.norm(b - a)))
    app = lambda Rt, p: (Rt[0] @ np.asarray(p) + Rt[1])
    # spinal markers
    mid = {}
    for (lo, up), (c, g) in gaps.items():
        did = 'disc_l5_sacrum' if lo == 'sacrum' else f'disc_{up}_{lo}'
        if did in J:
            ref = lo if lo in T else up
            delta = c - np.asarray(J[did]['centre_m'])
            J[did]['centre_m'] = c.tolist(); mid[did] = round(float(np.linalg.norm(delta)) * 1000, 2)
            R = T[ref][0] if ref in T else np.eye(3)
            J[did]['frame_axes_columns_XYZ'] = (R @ np.array(J[did]['frame_axes_columns_XYZ'])).tolist()
            lvl = did[len('disc_'):]
            for sd in ('left', 'right'):
                fk = f'facet_{lvl}_{sd}'
                if fk in J:
                    J[fk]['centre_m'] = (np.asarray(J[fk]['centre_m']) + delta).tolist()
                    J[fk]['frame_axes_columns_XYZ'] = (R @ np.array(J[fk]['frame_axes_columns_XYZ'])).tolist()
    for k, m in J.items():
        if m['frame_bone'] in T and not k.startswith(('disc_', 'facet_')):
            m['centre_m'] = app(T[m['frame_bone']], m['centre_m']).tolist()
            m['frame_axes_columns_XYZ'] = (T[m['frame_bone']][0] @ np.array(m['frame_axes_columns_XYZ'])).tolist()
    # ribs
    ribs = {}
    for n in range(1, 13):
        if n in (1, 10, 11, 12):
            Rt = T[f't{n}']
        else:                                             # head at the T(n-1)/T(n) disc: rotation mean, translation of the junction
            Ra, ta = T[f't{n}']; Rb, tb = T[f't{n - 1}']
            ang = 0.5 * (math.degrees(math.atan2(Ra[2, 1], Ra[1, 1])) + math.degrees(math.atan2(Rb[2, 1], Rb[1, 1])))
            Rm = rx(ang)
            j0 = (old[f't{n}'][1] + old[f't{n - 1}'][0]) / 2
            j1 = (np.array(B[f't{n}']['tail_m']) + np.array(B[f't{n - 1}']['head_m'])) / 2
            Rt = (Rm, j1 - Rm @ j0)
        for side in ('left', 'right'):
            k = f'rib_{n:02d}_{side}'
            h0, a0 = np.array(base['bones'][k]['head_m']), np.array(base['bones'][k]['tail_m'])
            L = float(np.linalg.norm(a0 - h0))
            h1 = app(Rt, h0)
            if n <= 10:                                   # re-aim at the unchanged anterior attachment, rigid length
                d = (a0 - h1) / np.linalg.norm(a0 - h1); a1 = h1 + L * d
                u0, u1 = (a0 - h0) / L, d
                v = np.cross(u0, u1); c = float(u0 @ u1)
                K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
                Rr = np.eye(3) + K + K @ K / (1 + c)
                rib_T = (Rr, h1 - Rr @ h0)
                cart = float(np.linalg.norm(a0 - h1) - L)
            else:
                rib_T = Rt; a1 = app(Rt, a0); cart = None
            B[k]['head_m'], B[k]['tail_m'] = h1.tolist(), a1.tolist()
            for mk, m in J.items():
                if m['frame_bone'] == k:
                    m['centre_m'] = app(rib_T, m['centre_m']).tolist()
                    m['frame_axes_columns_XYZ'] = (rib_T[0] @ np.array(m['frame_axes_columns_XYZ'])).tolist()
            desc0 = math.degrees(math.atan2(h0[2] - a0[2], math.hypot(*(a0 - h0)[:2])))
            desc1 = math.degrees(math.atan2(h1[2] - a1[2], math.hypot(*(a1 - h1)[:2])))
            ribs[k] = {'head_shift_mm': [round(float(x) * 1000, 2) for x in (h1 - h0)], 'anterior_end_shift_mm': round(float(np.linalg.norm(a1 - a0)) * 1000, 2),
                       'cartilage_gap_change_mm': None if cart is None else round(cart * 1000, 2),
                       'descent_deg_c004': round(desc0, 2), 'descent_deg_t001': round(desc1, 2)}
    names = ['SS', 'LL', 'TK', cl_key[:2]]
    sol = {nm: round(float(v), 3) for nm, v in zip(names, x[:4])}
    sol['stature_scale_s'] = round(float(x[4]), 5)
    sol['implied_source_cohort_stature_m'] = round(1.82 / float(x[4]), 3)
    sol['z_scores'] = {nm: round((float(v) - m) / sd, 3) for nm, v, (m, sd) in zip(names, x[:4], pri)}
    sol['chi2'] = round(float(chi2), 4)
    out['candidate'] = {
        'id': 'T001_COUPLED_TRUNK_EXPERIMENT', 'status': 'EXPERIMENTAL_NOT_A_CANDIDATE_NOT_CANONICAL', 'freeze_ready': False,
        'owner_approval': 'isolated experimental coupled trunk rebuild addressing U10 and U5 (2026-10-09)',
        'derived_from': {'record': str(BASE.relative_to(ROOT)), 'sha256': sha(BASE)}, 'cervical_prior': cl_key,
        'solution': sol,
        'element_heights_scaled_mm': {(n if isinstance(n, str) else f'{n[0]}/{n[1]}'): round(h * float(x[4]), 3) for n, _, h, _ in ch.elements(*x[:4])},
        'disc_gaps_mm': {('L5/S1' if lo == 'sacrum' else f'{up.upper()}/{lo.upper()}'): round(g, 3) for (lo, up), (c, g) in gaps.items()},
        'disc_marker_shift_mm': mid, 'ribs': ribs,
        'fixed': 'sacrum, C2, C1, skull, hyoid, sternum, clavicles, scapulae, arms, pelvis, legs (byte-identical to c004)',
        'limitations': ['thoracic per-level shape kept from c004 (unsourced); only its total is solved',
                        'one stature scale for all spine sources; per-source cohort statures are not recorded',
                        'rib re-aiming keeps rib length and the c004 anterior attachment; costal-cartilage change is the residual, '
                        'rib inclination (pump-handle angle) has no usable committed source frame (Holcombe 2017 alpha_PH frame unmapped)',
                        'sternum and shoulder girdle left at the c003/c004 ANSUR-governed position; thorax frame axes change with C7/T8']}
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out-dir', required=True)
    ap.add_argument('--cervical-prior', default='hasegawa', choices=['hasegawa', 'reinhold'])
    o = ap.parse_args()
    d = Path(o.out_dir)
    if d.exists():
        raise FileExistsError(d)
    out = build('CL_' + o.cervical_prior); d.mkdir(parents=True)
    (d / 'experiment_record.json').write_text(json.dumps(out, indent=1) + '\n')
    c = out['candidate']
    print(json.dumps(c['solution']))
    print('discs', c['disc_gaps_mm'])
    for k, v in c['ribs'].items():
        if k.endswith('left'):
            print(k, v)


if __name__ == '__main__':
    main()
