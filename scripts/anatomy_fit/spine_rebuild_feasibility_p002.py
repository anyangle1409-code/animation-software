#!/usr/bin/env python3
"""P002 spine rebuild feasibility (DIAGNOSTIC ONLY; not a candidate, not c005, freezes nothing).

Builds sagittal C2-S1 vertebral-body centre chains with explicit, non-zero disc gaps from committed evidence, and
measures how far each vertebra (and therefore each rib head) would move relative to c004. The purpose is to replace the
earlier worst-case statement ("a local re-partition would move C7/T1 by about 40 mm") with the actual consequence of
the stack that spine_column_length_discriminator.py found compatible with a 1.82 m man.

Chain (Y posterior, Z up, mm), from the provisional P1 S1 superior-endplate centre upwards:
  lumbar   MRI edge-mean body and disc heights (Hegazy 2014 male), P1 superior/inferior endplate orientations
  T12/L1   level-stack disc (5.6 mm) at the L1-superior angle
  thoracic body heights: THORACIC_CT_2016 (source B); discs: THORACIC_BODY_DISC_2011; total T1-T12 kyphosis 43.7 deg.
           Per-level tilt distribution is NOT known: three templates are reported side by side
             envelope_min / envelope_max   the extremal monotone sequences of the discriminator envelope
             specimen_shape                the single BodyParts3D specimen's own tilt sequence, affinely mapped onto
                                           the same end angles (grade D shape template, never a target)
  cervical C7/T1 (4.5 mm), Yukawa male bodies/discs; two families, because the source conflict is unresolved:
             reinhold_segmental            per-level Reinhold means (sum 9.6 deg lordosis)
             hasegawa_near_neutral         0 deg per level (Hasegawa male C2-C7 mean is -0.6 +/- 8.6 deg)
Two scalings: 'source_means' (as published) and 'ansur_closed' (every height x the discriminator's
required_column_scale_to_meet_ANSUR, i.e. stature-conditioning by ANSUR cervicale; column length assumed proportional
to stature).

  spine_rebuild_feasibility_p002.py --discriminator JSON --out JSON
"""
import argparse, hashlib, json, math, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import spine_column_length_discriminator as sd  # noqa: E402

ROOT = sd.ROOT
VARIANT = 'MRI_edge_mean|B_CT_2016|C7T1_anatomical_4.5'
CERV = ['C7', 'C6', 'C5', 'C4', 'C3']


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def specimen_body_tilts(bp3d, lo, hi):
    sp = bp3d['spine']
    disc_tilt = {k: sd.axis_angle_from_normal(v['disc_normal']) for k, v in sp.items()}
    names = ['T12/L1'] + [f'T{i}/T{i + 1}' for i in range(11, 0, -1)] + ['C7/T1']      # inferior to superior
    body = []
    for i in range(12):                                    # T12 .. T1: mean of its inferior and superior disc normals
        body.append((disc_tilt[names[i]] + disc_tilt[names[i + 1]]) / 2)
    a, b = body[0], body[-1]
    return [lo + (x - a) * (hi - lo) / (b - a) for x in body], [round(x, 2) for x in body]


def build(scale, tilts_T12_to_T1, cerv_family, stack, frames, edges, geom, s1_yz, phi_L1, kyph, reinhold):
    lel, _, _, _ = sd.lumbar_elements('MRI_edge_mean', frames, stack, edges)
    tbody, tdisc = sd.thoracic_heights('B_CT_2016', stack, geom)
    centres = {}
    y, z = s1_yz
    for h, phi, lab in lel:                                # disc, body, disc, body ... (L5/S1 .. L1)
        r = math.radians(phi); hh = h * scale
        if lab.startswith('body'):
            centres[lab.split()[1]] = (y - hh / 2 * math.sin(r), z + hh / 2 * math.cos(r))
        y -= hh * math.sin(r); z += hh * math.cos(r)

    def step(h, phi, name=None):
        nonlocal y, z
        r = math.radians(phi); hh = h * scale
        if name:
            centres[name] = (y - hh / 2 * math.sin(r), z + hh / 2 * math.cos(r))
        y -= hh * math.sin(r); z += hh * math.cos(r)
    step(stack['disc_gaps_mm']['T12/L1']['candidate'], phi_L1)
    order = [f'T{i}' for i in range(12, 0, -1)]
    for j, t in enumerate(order):
        step(tbody[t], tilts_T12_to_T1[j], t)
        if t != 'T1':
            step(tdisc[f'{order[j + 1]}/{t}'], (tilts_T12_to_T1[j] + tilts_T12_to_T1[j + 1]) / 2)
    phi = phi_L1 + kyph
    step(stack['disc_gaps_mm']['C7/T1']['candidate'], phi)
    for k, c in enumerate(CERV):
        step(stack['vertebral_bodies_mm'][c]['candidate'], phi, c)
        above = f'{CERV[k + 1] if k + 1 < len(CERV) else "C2"}/{c}'
        seg = reinhold.get(above)
        d_phi = seg['mean'] if (cerv_family == 'reinhold_segmental' and seg) else 0.0     # negative = lordosis
        step(stack['disc_gaps_mm'][above]['candidate'], phi + d_phi / 2)
        phi += d_phi
    centres['C2_inferior_endplate'] = (y, z)
    return centres


def c004_centres(rec):
    out = {}
    for n, b in rec['bones'].items():
        if n in {'l1', 'l2', 'l3', 'l4', 'l5', 'c3', 'c4', 'c5', 'c6', 'c7'} or (n.startswith('t') and n[1:].isdigit()):
            h, t = b['head_m'], b['tail_m']
            out[n.upper()] = (500 * (h[1] + t[1]), 500 * (h[2] + t[2]))
    c3 = rec['bones']['c3']
    out['C2_inferior_endplate'] = (1000 * c3['tail_m'][1], 1000 * c3['tail_m'][2])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--discriminator', required=True)
    ap.add_argument('--out', required=True)
    o = ap.parse_args()
    disc = json.loads(Path(o.discriminator).read_text())
    stack, frames, edges, geom = sd.load('stack'), sd.load('frames'), sd.load('edges'), sd.load('geom')
    s1, pose, bp3d = sd.load('s1'), sd.load('pose'), sd.load('bp3d')
    align = json.loads((sd.ANAT / 'canonical_spine_sagittal_alignment_v1.json').read_text())
    reinhold = align['cervical_segment_family']['levels']
    rec = json.loads(sd.IN['c004'].read_text())
    kyph = pose['global_male_reference_deg']['thoracic_kyphosis_T1_T12']
    s1c = s1['derived_S1_superior_endplate']['centre_m']; s1_yz = (1000 * s1c[1], 1000 * s1c[2])
    sup = {k: sd.axis_angle_from_normal(v['normal']) for k, v in frames['geometry']['superior_frames'].items()}
    phi_L1 = sup['L1']
    tb, td = sd.thoracic_heights('B_CT_2016', stack, geom)
    env = sd.thoracic_envelope(tb, td, phi_L1, kyph)
    spec_tilts, spec_raw = specimen_body_tilts(bp3d, phi_L1, phi_L1 + kyph)
    templates = {'envelope_min': env['min_sequence_deg'], 'envelope_max': env['max_sequence_deg'], 'specimen_shape': spec_tilts}
    scales = {'source_means': 1.0, 'ansur_closed': disc['variants'][VARIANT]['required_column_scale_to_meet_ANSUR']}
    ref = c004_centres(rec)
    ij = rec['skeleton_input']['trunk']['ij_skin']['value_m']
    results = {}
    for sk, sc in scales.items():
        for tk, tilts in templates.items():
            for cf in ('reinhold_segmental', 'hasegawa_near_neutral'):
                c = build(sc, tilts, cf, stack, frames, edges, geom, s1_yz, phi_L1, kyph, reinhold)
                rows = {}
                for name, (y, z) in c.items():
                    if name in ref:
                        ry, rz = ref[name]
                        rows[name] = {'rebuilt_yz_mm': [round(y, 1), round(z, 1)], 'c004_yz_mm': [round(ry, 1), round(rz, 1)],
                                      'delta_yz_mm': [round(y - ry, 1), round(z - rz, 1)], 'delta_mm': round(math.hypot(y - ry, z - rz), 1)}
                t2t3 = (c['T2'][1] + c['T3'][1]) / 2
                results[f'{sk}|{tk}|{cf}'] = {
                    'levels': rows,
                    'max_thoracic_shift_mm': max(rows[t]['delta_mm'] for t in rows if t.startswith('T')),
                    'max_lumbar_shift_mm': max(rows[t]['delta_mm'] for t in rows if t.startswith('L')),
                    'C7_shift_mm': rows['C7']['delta_mm'],
                    'C2_inferior_endplate_shift_mm': rows['C2_inferior_endplate']['delta_mm'],
                    'T2_T3_mid_z_minus_IJ_skin_z_mm': round(t2t3 - 1000 * ij[2], 1),
                    'C7_centre_posterior_of_S1_centre_mm': round(c['C7'][0] - s1_yz[0], 1),
                    'T2_T3_mid_posterior_of_IJ_skin_mm': round((c['T2'][0] + c['T3'][0]) / 2 - 1000 * ij[1], 1),
                }
    summary = {k: {x: v[x] for x in ('max_thoracic_shift_mm', 'max_lumbar_shift_mm', 'C7_shift_mm', 'C2_inferior_endplate_shift_mm',
                                     'T2_T3_mid_z_minus_IJ_skin_z_mm', 'C7_centre_posterior_of_S1_centre_mm',
                                     'T2_T3_mid_posterior_of_IJ_skin_mm')} for k, v in results.items()}
    summary['c004_as_built'] = {'C7_centre_posterior_of_S1_centre_mm': round(ref['C7'][0] - s1_yz[0], 1),
                                'T2_T3_mid_posterior_of_IJ_skin_mm': round((ref['T2'][0] + ref['T3'][0]) / 2 - 1000 * ij[1], 1),
                                'T2_T3_mid_z_minus_IJ_skin_z_mm': round((ref['T2'][1] + ref['T3'][1]) / 2 - 1000 * ij[2], 1)}
    out = {'schema_version': 1, 'created': '2026-10-09', 'kind': 'DIAGNOSTIC_FEASIBILITY_NOT_A_CANDIDATE', 'proposal_id': 'P002',
           'stack_variant': VARIANT, 'inputs_sha256': {o.discriminator: sha(o.discriminator), 'scripts/anatomy_fit/spine_column_length_discriminator.py':
                                                       sha(HERE / 'spine_column_length_discriminator.py')},
           'P1_S1_yz_mm': [round(x, 2) for x in s1_yz], 'phi_L1_superior_deg': round(phi_L1, 3),
           'thoracic_templates_T12_to_T1_deg': {k: [round(x, 2) for x in v] for k, v in templates.items()},
           'specimen_raw_body_tilts_T12_to_T1_deg': spec_raw, 'scales': scales,
           'IJ_reference': {'c004_ij_skin_z_mm': round(1000 * ij[2], 1), 'note': 'Razzouk 2023 (supine CT, abstract level): sternal notch at '
                            'the T2-T3 vertebral bodies; skin IJ is used as given in the c004 record'},
           'summary': summary, 'detail': results,
           'reading': ['delta = rebuilt body centre minus c004 stick midpoint; c004 sticks include the disc space, so c004 body centres are '
                       'not definition-identical to the rebuilt ones (expected few-mm offsets even for a perfect column).',
                       'Rib heads articulate with thoracic bodies: a thoracic shift moves the costovertebral joints by about the same amount.']}
    Path(o.out).parent.mkdir(parents=True, exist_ok=True)
    Path(o.out).write_text(json.dumps(out, indent=1) + '\n')
    for k, v in summary.items():
        print(f'{k:60s}', v)


if __name__ == '__main__':
    main()
