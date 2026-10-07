"""Character-specific anatomical fitting from a skinned body surface (Phase 6).

Pure numpy. Input: world-space rest vertices/triangles (metres, Blender Z-up, character facing
-Y) plus the authored-feature table of the body generator, after it has been verified to match the
mesh. Output: surface landmarks, joint centres from at least two methods where sources allow,
inter-method disagreement, rig comparison and verification checks.

Conventions
- Anatomical side is geometric: with the character facing -Y and +Z up, its LEFT is +X
  (left = up x forward). Runtime bones named *_l lie on -X, i.e. on the anatomical RIGHT.
- Every value records method, sources and an uncertainty note. Estimates of bony landmarks
  that the surface does not model are marked as such; nothing here is an anatomical acceptance.
"""
import math

import numpy as np

from mesh_sections import loop_metrics, plane_section

UP = np.array([0.0, 0.0, 1.0])
ANTERIOR = np.array([0.0, -1.0, 0.0])
SIDES = {'left': 1.0, 'right': -1.0}  # anatomical side -> sign of world X

# Sources first registered in this phase. Access is what was actually reachable from this
# environment (general web hosts were blocked by egress policy; search snippets and GitHub
# source code were reachable).
FIT_SOURCES = {
    'HARRINGTON_2007': {'work': 'Harrington ME et al. Prediction of the hip joint centre in adults, children, and patients with cerebral palsy based on MRI. J Biomech 2007;40:595-602',
                        'access': 'search_snippet + open-source implementation (pyCGM2 modelDecorator.harringtonRegression)',
                        'claim': 'Pelvis-only HJC: AP -0.24PD-9.9, SI -0.30PW-10.9, ML 0.33PW+7.3 mm; PW-only variant AP -0.138PW-10.4, SI -0.305PW-10.9, ML 0.33PW+7.3 (Sangeux 2015 implementation).'},
    'SANGEUX_2015': {'work': 'Sangeux M. On the implementation of predictive methods to locate the hip joint centres. Gait Posture 2015;42:402-405',
                     'access': 'cited by pyCGM2 source', 'claim': 'PW-only Harrington variant used when PSIS/pelvic depth is unavailable.'},
    'BELL_1990': {'work': 'Bell AL, Pedersen DR, Brand RA. A comparison of the accuracy of several hip center location prediction methods. J Biomech 1990;23:617-621',
                  'access': 'search_snippet (two independent snippets); pyCGM2 implementation conflicts on SI (-0.19PW)',
                  'claim': 'HJC 19% PW posterior, 30% PW distal, 14% PW medial of ipsilateral ASIS (36% lateral of mid-ASIS).'},
    'HARA_2016': {'work': 'Hara R et al. Generation of age and sex specific regression equations to locate the hip joint centres. Gait Posture 2016',
                  'access': 'open-source implementation (pyCGM2 modelDecorator.haraRegression)',
                  'claim': 'AP 11-0.063LL, ML 8+0.086LL, SI -9-0.078LL mm from mid-ASIS (surface; pyCGM2 subtracts marker offsets separately).'},
    'DAVIS_1991': {'work': 'Davis RB et al. A gait analysis data collection and reduction technique. Hum Mov Sci 1991;10:575-587',
                   'access': 'open-source implementations (pyCGM2 davisRegression; pyCGM hipJointCenter)',
                   'claim': 'C=0.115LL-15.3, theta 0.5 rad, beta 0.314 rad, ASIS-trochanter distance.'},
    'PELVIC_TILT': {'work': 'Clinical measures of pelvic tilt (IJSPT review) and cited inclinometer studies',
                    'access': 'search_snippet', 'claim': 'Standing ASIS-PSIS anterior tilt in healthy men 8.6-9.6 deg mean (range 3-18).'},
    'KNEE_EPICONDYLE_JL': {'work': 'Epicondyle-to-joint-line studies: Brazilian MRI (n=500) 33.39/26.32 mm; Thai MRI (n=140) 27.1/21.7 mm; MRI (n=130) lateral 24.4 mm; cadaver (n=40) 28.95/23.97 mm (medial/lateral)',
                           'access': 'search_snippet (PMC12585613, PMC8845375, PMC10250280 and cadaver report)',
                           'claim': 'Femoral epicondyles lie 21.7-33.4 mm proximal to the tibiofemoral joint line.'},
    'DRILLIS_CONTINI': {'work': 'Drillis R, Contini R 1966 segment proportions (as reproduced in Winter, Biomechanics and Motor Control of Human Movement)',
                        'access': 'search_snippet; labels for 0.530H conflict between secondary sources',
                        'claim': 'Knee 0.285H, ankle 0.039H, shoulder 0.818H (population proportions; weak cross-check only).'},
    'TROTTER_GLESER': {'work': 'Trotter M, Gleser GC (1952/1958; Trotter 1970) stature regressions, white males',
                       'access': 'search_snippet (Wikipedia/AAFS reproductions)',
                       'claim': 'Stature cm = 2.38Fem+61.41 (3.27); 2.52Tib+78.62 (3.37); 2.68Fib+71.78 (3.29); 3.08Hum+70.45 (4.05); 3.78Rad+79.01 (4.32); 3.70Ulna+74.05 (4.32).'},
    'AHD': {'work': 'Evaluation of three-dimensional acromiohumeral distance in the standing position (J Orthop Surg Res 2020; PMC7510276)',
            'access': 'search_snippet', 'claim': '2D AHD standing 8.8 +/- 1.3 mm in healthy adults.'},
    'ACROMION_THICKNESS': {'work': 'Acromion morphometry studies (incl. South Indian dry scapulae)',
                           'access': 'search_snippet', 'claim': 'Mean acromial thickness 6.58-7.42 mm.'},
    'HUMERAL_HEAD_RADIUS': {'work': 'Humeral head morphometry (CT 3-D analysis, Acta Orthop; radiologic analysis of normal adults)',
                            'access': 'search_snippet', 'claim': 'Radius of curvature 24.7 mm (bone, coronal) to 28.8 +/- 1.9 mm (males).'},
}

KNEE_EPICONDYLE_OFFSETS_MM = {'medial': [33.39, 27.1, 28.95], 'lateral': [26.32, 21.7, 24.4, 23.97]}


def _sections(V, T, z, keep):
    return [l for l in plane_section(V, T, (0.0, 0.0, z), UP) if keep(l)]


def _leg_loop(V, T, z, sign):
    loops = _sections(V, T, z, lambda l: sign * l[:, 0].mean() > 0.03 and abs(l[:, 0].mean()) < 0.17)
    return max(loops, key=len) if loops else None


def _box_centre(loop):
    return np.array([(loop[:, 0].max() + loop[:, 0].min()) / 2, (loop[:, 1].max() + loop[:, 1].min()) / 2, loop[:, 2].mean()])


def closest_point_on_triangle(p, a, b, c):
    """Ericson, Real-Time Collision Detection, 5.1.5."""
    ab, ac, ap = b - a, c - a, p - a
    d1, d2 = ab @ ap, ac @ ap
    if d1 <= 0 and d2 <= 0:
        return a
    bp = p - b
    d3, d4 = ab @ bp, ac @ bp
    if d3 >= 0 and d4 <= d3:
        return b
    vc = d1 * d4 - d3 * d2
    if vc <= 0 and d1 >= 0 and d3 <= 0:
        return a + d1 / (d1 - d3) * ab
    cp = p - c
    d5, d6 = ab @ cp, ac @ cp
    if d6 >= 0 and d5 <= d6:
        return c
    vb = d5 * d2 - d1 * d6
    if vb <= 0 and d2 >= 0 and d6 <= 0:
        return a + d2 / (d2 - d6) * ac
    va = d3 * d6 - d5 * d4
    if va <= 0 and (d4 - d3) >= 0 and (d5 - d6) >= 0:
        return b + (d4 - d3) / ((d4 - d3) + (d5 - d6)) * (c - b)
    denom = 1.0 / (va + vb + vc)
    return a + ab * (vb * denom) + ac * (vc * denom)


def closest_surface_point(V, T, p, radius=0.05):
    """Exact closest point on the triangle surface (searching triangles near p)."""
    near = np.nonzero(np.linalg.norm(V - p, axis=1) < radius)[0]
    mask = np.isin(T, near).any(1)
    best, dist = None, np.inf
    for tri in T[mask]:
        q = closest_point_on_triangle(p, V[tri[0]], V[tri[1]], V[tri[2]])
        d = float(np.linalg.norm(q - p))
        if d < dist:
            best, dist = q, d
    return best, dist


def entry(value, method, sources, uncertainty, confidence, **extra):
    data = {'value_m': [float(x) for x in np.asarray(value).ravel()] if np.ndim(value) else float(value),
            'method': method, 'sources': sources, 'uncertainty': uncertainty, 'confidence': confidence}
    data.update(extra)
    return data


def global_checks(V):
    from scipy.spatial import cKDTree
    mirror = V * np.array([-1, 1, 1])
    dist, _ = cKDTree(V).query(mirror)
    head = V[(V[:, 2] > 1.60) & (V[:, 2] < 1.75)]
    foot = V[V[:, 2] < 0.05]
    nose = head[np.argmin(head[:, 1])]
    return {
        'stature_m': float(V[:, 2].max() - V[:, 2].min()), 'floor_z_m': float(V[:, 2].min()),
        'mirror_symmetry_max_m': float(dist.max()), 'mirror_symmetry_mean_m': float(dist.mean()),
        'facing': {'nose_y_m': float(nose[1]), 'toe_tip_y_m': float(foot[:, 1].min()), 'heel_y_m': float(foot[:, 1].max()),
                   'faces': '-Y' if nose[1] < 0 and foot[:, 1].min() < -abs(foot[:, 1].max()) else 'UNRESOLVED'},
    }


def hand_chirality(V, sign):
    """Geometric hand chirality: thumb direction versus fingers x palm-normal (right-hand rule)."""
    H = V[(sign * V[:, 0] > 0.14) & (V[:, 2] < 0.92) & (V[:, 2] > 0.70)]
    c = H.mean(0)
    w, U = np.linalg.eigh(np.cov((H - c).T))
    fingers = -UP  # hanging hand
    thumb_tip = H[np.argmin(H[:, 1])]  # most anterior hand vertex
    palm = U[:, 0] * np.sign(U[:, 0] @ (thumb_tip - c))  # palm side contains the opposed thumb
    thumb = thumb_tip - c
    thumb_lateral = thumb - (thumb @ palm) * palm - (thumb @ fingers) * fingers
    handed = 'right' if np.cross(fingers, palm) @ thumb_lateral > 0 else 'left'
    return {'world_x_side': '+X' if sign > 0 else '-X', 'palm_normal': palm.round(3).tolist(),
            'thumb_tip_m': thumb_tip.round(4).tolist(), 'geometric_hand': handed}


def ankle(V, T, sign, H):
    zs = np.arange(0.20, 0.04, -0.002)
    rows = []
    for z in zs:
        l = _leg_loop(V, T, z, sign)
        if l is None:
            continue
        rows.append((z, l[:, 1].max() - l[:, 1].min(), l))
    depths = np.array([r[1] for r in rows])
    i_min = int(np.argmin(depths[:len(depths) // 2 + 10]))
    dmin = depths[i_min]
    j = next(k for k in range(i_min, len(rows)) if rows[k][1] > 1.25 * dmin)
    z_junction = rows[j - 1][0]
    loop = rows[j - 1][2]
    centre = _box_centre(loop)
    medial = loop[np.argmin(sign * loop[:, 0])]
    lateral = loop[np.argmax(sign * loop[:, 0])]
    z_dc = 0.039 * H
    l_dc = _leg_loop(V, T, z_dc, sign)
    c_dc = _box_centre(l_dc) if l_dc is not None else None
    return {
        'shank_min_depth_m': float(dmin), 'shank_min_z_m': float(rows[i_min][0]),
        'leg_foot_junction_z_m': float(z_junction),
        'malleolus_medial_skin': entry(medial, 'Medial extreme of the last shank section above the leg-foot junction (no modelled malleolar prominence).', ['ISB_I'], 'Bony tip not modelled; level +/-15 mm.', 'low'),
        'malleolus_lateral_skin': entry(lateral, 'Lateral extreme of the same section.', ['ISB_I'], 'Bony tip not modelled; level +/-15 mm.', 'low'),
        'AJC_methods': {
            'surface_junction': entry(centre, 'ISB malleolar-midpoint convention applied at the soft-tissue leg-foot junction (section bounding-box centre).', ['ISB_I'], '+/-15 mm vertical', 'low'),
            'drillis_contini': entry(c_dc if c_dc is not None else [np.nan] * 3, 'Height 0.039H; section centre at that height.', ['DRILLIS_CONTINI'], 'Population proportion; individual variation not modelled', 'low'),
        },
    }


def knee(V, T, sign, H):
    rows = []
    for z in np.arange(0.42, 0.60, 0.002):
        l = _leg_loop(V, T, z, sign)
        if l is not None:
            rows.append((z, loop_metrics(l, UP)[2], l))
    i = int(np.argmin([r[1] for r in rows]))
    z_jl = rows[i][0]
    offs = [(m + l) / 2 for m in KNEE_EPICONDYLE_OFFSETS_MM['medial'] for l in KNEE_EPICONDYLE_OFFSETS_MM['lateral']]
    off = (np.mean(KNEE_EPICONDYLE_OFFSETS_MM['medial']) + np.mean(KNEE_EPICONDYLE_OFFSETS_MM['lateral'])) / 2 / 1000
    z_kjc = z_jl + off
    loop = _leg_loop(V, T, z_kjc, sign)
    centre = _box_centre(loop)
    medial = loop[np.argmin(sign * loop[:, 0])]
    lateral = loop[np.argmax(sign * loop[:, 0])]
    z_dc = 0.285 * H
    c_dc = _box_centre(_leg_loop(V, T, z_dc, sign))
    return {
        'joint_line_soft_tissue_z_m': float(z_jl),
        'epicondyle_offset_m': {'used': off, 'range_from_study_means': [min(offs) / 1000, max(offs) / 1000]},
        'epicondyle_medial_skin': entry(medial, 'Medial extreme of leg section at joint line + pooled epicondyle offset.', ['KNEE_EPICONDYLE_JL', 'ISB_I'], 'Offset study range +/-3 mm; soft-tissue joint line +/-10 mm.', 'moderate'),
        'epicondyle_lateral_skin': entry(lateral, 'Lateral extreme of the same section.', ['KNEE_EPICONDYLE_JL', 'ISB_I'], 'as medial', 'moderate'),
        'KJC_methods': {
            'joint_line_plus_epicondyle_offset': entry(centre, 'Minimum-area knee section (soft-tissue joint line) + pooled epicondyle-to-joint-line offset; ISB midpoint of epicondyles taken as section centre.', ['KNEE_EPICONDYLE_JL', 'ISB_I'], '+/-10 mm vertical, +/-8 mm AP (epicondylar axis assumed at mid-depth)', 'moderate'),
            'drillis_contini': entry(c_dc, 'Height 0.285H; section centre at that height.', ['DRILLIS_CONTINI'], 'Population proportion', 'low'),
        },
    }


def pelvis_and_hip(V, T, features, sign, ankle_side, H, tilt_deg=9.0):
    asis = {s: closest_surface_point(V, T, np.array([sg * features['asis'][0], features['asis'][1], features['asis'][2]])) for s, sg in SIDES.items()}
    PW = float(np.linalg.norm(asis['left'][0] - asis['right'][0]))
    mid = (asis['left'][0] + asis['right'][0]) / 2
    right_axis = asis['right'][0] - asis['left'][0]
    right_axis /= np.linalg.norm(right_axis)
    t = math.radians(tilt_deg)
    ant_h = np.cross(UP, right_axis)  # horizontal anterior, right-handed with right and up
    ant_h = ant_h / np.linalg.norm(ant_h)
    if ant_h @ ANTERIOR < 0:
        ant_h = -ant_h
    X = math.cos(t) * ant_h - math.sin(t) * UP   # anterior tilt: ASIS lower than PSIS
    Y = math.sin(t) * ant_h + math.cos(t) * UP
    Z = right_axis
    s_lat = -1.0 if sign > 0 else 1.0   # lateral along ISB Z (right): left side is -Z
    lat_vec = s_lat * Z
    medial_mall = np.array(ankle_side['malleolus_medial_skin']['value_m'])
    LL = float(np.linalg.norm(asis['left' if sign > 0 else 'right'][0] - medial_mall)) * 1000
    pw = PW * 1000

    def place(ap, si, ml):
        return mid + (ap * X + si * Y + ml * lat_vec) / 1000

    hip_loops = []
    for z in np.arange(0.86, 1.00, 0.004):   # above the crotch: single pelvic section, excludes thigh bulges
        for l in plane_section(V, T, (0, 0, z), UP):
            if abs(l[:, 0].mean()) < 0.05 and len(l) > 30:
                hip_loops.append(l)
    pts = np.concatenate(hip_loops)
    troch = pts[np.argmax(sign * pts[:, 0])]
    asis_side = asis['left' if sign > 0 else 'right'][0]
    xdis = float(abs((troch - asis_side) @ X)) * 1000
    C = LL * 0.115 - 15.3
    th, be = 0.5, 0.314
    davis = place(C * math.cos(th) * math.sin(be) - xdis * math.cos(be),
                  -C * math.cos(th) * math.cos(be) - xdis * math.sin(be),
                  pw / 2 - C * math.sin(th))   # lateral of mid-ASIS = half PW minus medial offset
    methods = {
        'harrington_pw_only': entry(place(-0.138 * pw - 10.4, -0.305 * pw - 10.9, 0.33 * pw + 7.3), 'Harrington PW-only regression (Sangeux 2015 implementation), origin mid-ASIS skin, pelvic frame tilted anteriorly by the standing ASIS-PSIS tilt.', ['HARRINGTON_2007', 'SANGEUX_2015', 'PELVIC_TILT'], 'Published MRI validation error ~1-2 cm; ASIS is the skin end of the authored inguinal line.', 'moderate'),
        'bell_1990': entry(place(-0.19 * pw, -0.30 * pw, 0.36 * pw), 'Bell 19% posterior / 30% distal / 36% lateral of mid-ASIS.', ['BELL_1990', 'PELVIC_TILT'], 'Published accuracy lower than Harrington.', 'low'),
        'hara_2016': entry(place(11 - 0.063 * LL, -9 - 0.078 * LL, 8 + 0.086 * LL), 'Hara leg-length regression; LL = ASIS to medial malleolus skin.', ['HARA_2016', 'PELVIC_TILT'], 'Published error ~1 cm in adults; LL depends on estimated malleolus.', 'moderate'),
        'davis_1991': entry(davis, 'Davis (CGM) with skin points (no marker radius).', ['DAVIS_1991', 'PELVIC_TILT'], 'Known to be less accurate than Harrington/Hara.', 'low'),
    }
    pts_m = np.array([m['value_m'] for m in methods.values()])
    selected = (np.array(methods['harrington_pw_only']['value_m']) + np.array(methods['hara_2016']['value_m'])) / 2
    tilt_sens = {}
    for td in (3.0, 18.0):
        tt = math.radians(td)
        Xt = math.cos(tt) * ant_h - math.sin(tt) * UP
        Yt = math.sin(tt) * ant_h + math.cos(tt) * UP
        p = mid + ((-0.138 * pw - 10.4) * Xt + (-0.305 * pw - 10.9) * Yt + (0.33 * pw + 7.3) * lat_vec) / 1000
        tilt_sens[f'{td:g}deg'] = p.tolist()
    return {
        'asis_skin': entry(asis_side, 'Superolateral end of the authored inguinal line (generator feature table, verified unchanged in r95), projected to the nearest surface vertex. Anatomical basis: the inguinal ligament attaches to the ASIS.', ['OS_SELECTED'], 'Aesthetic groove endpoint; +/-20 mm.', 'low', projection_distance_m=asis['left' if sign > 0 else 'right'][1]),
        'trochanterion_skin': entry(troch, 'Lateral-most point of the single pelvic section above the crotch (z 0.86-1.00).', [], 'Surface extreme; bony greater trochanter not modelled.', 'moderate'),
        'inter_asis_width_m': PW, 'leg_length_m': LL / 1000, 'asis_trochanter_ap_m': xdis / 1000, 'pelvic_tilt_used_deg': tilt_deg,
        'HJC_methods': methods,
        'HJC_selected': entry(selected, 'Mean of Harrington PW-only and Hara (both MRI-validated in adults).', ['HARRINGTON_2007', 'HARA_2016'], 'See method spread and tilt sensitivity', 'moderate'),
        'HJC_method_spread_m': float(np.max(np.linalg.norm(pts_m - pts_m.mean(0), axis=1))),
        'HJC_tilt_sensitivity_harrington': tilt_sens,
    }


def shoulder(V, T, sign, H, features):
    arm = arm_vertical(V, T, sign, 1.24, 1.36, 0.02)
    y_c = float(np.mean([_box_centre(r[2])[1] for r in arm]))
    loops = plane_section(V, T, (0.0, y_c, 0.0), (0.0, 1.0, 0.0))
    pts = np.concatenate([l for l in loops if len(l) > 30])
    top = pts[(sign * pts[:, 0] > 0.12) & (pts[:, 2] > 1.40)]
    prof = []
    for xb in np.arange(0.12, 0.30, 0.004):
        m = top[(sign * top[:, 0] >= xb) & (sign * top[:, 0] < xb + 0.004)]
        if len(m):
            prof.append(m[np.argmax(m[:, 2])])
    corner = None
    for p0, p1 in zip(prof, prof[1:]):
        dx = sign * (p1[0] - p0[0])
        if sign * p0[0] > 0.20 and dx > 0 and (p1[2] - p0[2]) / dx <= -1.0:   # top turns past 45 deg laterally
            corner = p0
            break
    depth = {'skin_mm': [3.0, 6.0], 'acromion_thickness_mm': [6.58, 7.42], 'ahd_mm': [8.8 - 1.3, 8.8 + 1.3], 'head_radius_mm': [24.7, 28.8]}
    lo = sum(v[0] for v in depth.values()) / 1000
    hi = sum(v[1] for v in depth.values()) / 1000
    mid_depth = (lo + hi) / 2
    gh_a = corner - np.array([sign * 0.026, 0.0, mid_depth])  # head centre ~one head-radius medial to lateral acromion edge
    # Method B: authored humeral-head-level shoulder ring (generator S1), arm portion centroid.
    ring = np.array(features['s1_arm_ring'])
    ring_b = np.stack([sign * ring[:, 0], -ring[:, 1], ring[:, 2]], 1)
    gh_b = ring_b.mean(0)
    # Method C: sphere fit to the deltoid cap (lateral shoulder surface above the axilla).
    cap = V[(sign * V[:, 0] > 0.20) & (V[:, 2] > 1.40) & (V[:, 2] < 1.53) & (V[:, 1] > -0.07) & (V[:, 1] < 0.11)]
    A = np.c_[2 * cap, np.ones(len(cap))]
    b = (cap ** 2).sum(1)
    sol = np.linalg.lstsq(A, b, rcond=None)[0]
    centre_c = sol[:3]
    radius_c = float(math.sqrt(sol[3] + centre_c @ centre_c))
    return {
        'acromion_lateral_skin': entry(corner, 'Exact coronal section through the upper-arm AP centre; first point lateral of x=0.20 where the shoulder-top contour turns steeper than 45 deg.', [], 'Bony acromion not modelled; +/-10 mm', 'moderate', coronal_plane_y_m=y_c),
        'GH_methods': {
            'acromion_depth_chain': entry(gh_a, f'Acromion skin minus skin+acromion thickness+AHD+head radius ({lo*1000:.1f}-{hi*1000:.1f} mm, mid used) vertically, and ~one head radius medially.', ['AHD', 'ACROMION_THICKNESS', 'HUMERAL_HEAD_RADIUS'], f'Vertical {lo*1000:.0f}-{hi*1000:.0f} mm; skin thickness estimated', 'moderate'),
            'authored_humeral_head_ring': entry(gh_b, 'Centroid of the generator ring labelled "humeral head level, deltoid wraps the joint" (arm portion), verified present in r95.', [], 'Designer intent; ring centroid lies within deltoid soft tissue', 'low'),
            'deltoid_cap_sphere': entry(centre_c, 'Least-squares sphere through lateral deltoid-cap vertices.', [], f'Fitted radius {radius_c*1000:.1f} mm; deltoid thickness not uniform', 'low', sphere_radius_m=radius_c),
        },
        'GH_selected': entry(gh_a, 'Acromion depth chain (only method with sourced dimensions); others are checks.', ['AHD', 'ACROMION_THICKNESS', 'HUMERAL_HEAD_RADIUS'], 'See method spread', 'moderate'),
        'shoulder_height_drillis_contini_m': 0.818 * H,
    }


def arm_vertical(V, T, sign, lo, hi, step=0.002):
    rows = []
    for z in np.arange(lo, hi, step):
        loops = _sections(V, T, z, lambda l: sign * l[:, 0].mean() > 0.17)
        if loops:
            l = max(loops, key=len)
            rows.append((z, loop_metrics(l, UP)[2], l))
    return rows


def elbow_wrist(V, T, sign):
    rows = arm_vertical(V, T, sign, 1.15, 1.25)
    i = int(np.argmin([r[1] for r in rows]))
    z_e, _, le = rows[i]
    ce = _box_centre(le)
    em = le[np.argmin(sign * le[:, 0])]
    el = le[np.argmax(sign * le[:, 0])]
    rows_w = arm_vertical(V, T, sign, 0.90, 0.96, 0.001)
    j = int(np.argmin([r[1] for r in rows_w]))
    z_w, _, lw = rows_w[j]
    cw = _box_centre(lw)
    radial = lw[np.argmin(lw[:, 1])]   # thumb side is anterior with palms medial
    ulnar = lw[np.argmax(lw[:, 1])]
    return {
        'elbow_waist_z_m': float(z_e),
        'epicondyle_medial_skin': entry(em, 'Medial extreme of the minimum-area elbow section between biceps and forearm bellies.', ['ISB_II'], 'Epicondyle-to-waist relation unsourced; +/-20 mm vertical', 'low'),
        'epicondyle_lateral_skin': entry(el, 'Lateral extreme of the same section.', ['ISB_II'], 'as medial', 'low'),
        'EJC': entry(ce, 'ISB midpoint of epicondyles approximated by the elbow-waist section centre.', ['ISB_II'], '+/-20 mm vertical', 'low'),
        'wrist_z_m': float(z_w),
        'styloid_radial_skin': entry(radial, 'Anterior (thumb-side) extreme of the minimum-area wrist section; palms face medially at rest.', ['ISB_II'], '+/-10 mm', 'moderate'),
        'styloid_ulnar_skin': entry(ulnar, 'Posterior extreme of the same section.', ['ISB_II'], '+/-10 mm', 'moderate'),
        'WJC': entry(cw, 'Midpoint between styloids (ISB) approximated by the wrist section centre.', ['ISB_II'], '+/-10 mm', 'moderate'),
    }


# ---------------------------------------------------------------------------
# Trunk, head, girdle, hand and foot recipes (lower confidence; see each recipe)
# ---------------------------------------------------------------------------

def midline_profile(V, T, z):
    pts = np.concatenate([l for l in plane_section(V, T, (0, 0, z), UP) if len(l) > 20])
    m = pts[np.abs(pts[:, 0]) < 0.006]
    return (float(m[:, 1].min()), float(m[:, 1].max())) if len(m) else (np.nan, np.nan)


def head_surface(V, T, z, sign):
    pts = np.concatenate([l for l in plane_section(V, T, (0, 0, z), UP) if abs(l[:, 0].mean()) < 0.05 and len(l) > 20])
    return pts


def trunk_and_head(V, T, features, hips):
    ij, d_ij = closest_surface_point(V, T, np.array(features['ij']))
    px, d_px = closest_surface_point(V, T, np.array(features['px']))
    mid_asis = (np.array(hips['left']['asis_skin']['value_m']) + np.array(hips['right']['asis_skin']['value_m'])) / 2
    # L5/S1: posterior to the ASIS plane at the sacral promontory (anatomical approximation)
    l5s1 = mid_asis + np.array([0.0, 0.115, 0.045])
    # vertebral levels: T2/T3 disc at the jugular-notch height, L5/S1 at the pelvic estimate;
    # thoracic and lumbar motion-segment heights in a 2.55:4.0 ratio (typical adult proportions).
    names = [f't{i}' for i in range(3, 13)] + [f'l{i}' for i in range(1, 6)]
    weights = np.array([2.55] * 10 + [4.0] * 5)
    z_top, z_bot = ij[2], l5s1[2]
    unit_h = (z_top - z_bot) / weights.sum()
    centres, z = {}, z_top
    depth = {'c': 0.055, 't': 0.070, 'l': 0.080}
    for name, w in zip(names, weights):
        zc = z - w * unit_h / 2
        back = midline_profile(V, T, zc)[1]
        centres[name] = [0.0, back - depth[name[0]], zc]
        z -= w * unit_h
    t_step = 2.55 * unit_h
    # cervical: C7/T1 one thoracic step above T2 centre; C1..C7 evenly to the C0-C1 estimate
    t2z = z_top + t_step / 2
    t1z = t2z + t_step
    eye_z = features['eye_ring_z']
    c0c1_z = features['palate_z'] + 0.005
    head_pts = head_surface(V, T, c0c1_z, 1)
    front, back = head_pts[:, 1].min(), head_pts[:, 1].max()
    c0c1 = np.array([0.0, front + 0.62 * (back - front), c0c1_z])
    centres['t2'] = [0.0, midline_profile(V, T, t2z)[1] - depth['t'], t2z]
    centres['t1'] = [0.0, midline_profile(V, T, t1z)[1] - depth['t'], t1z]
    c_top, c_bot = c0c1, np.array(centres['t1']) + np.array([0, 0, t_step / 2])
    for k, i in enumerate(range(7, 0, -1)):
        f = (k + 0.5) / 7
        p = c_bot + (c_top - c_bot) * f
        centres[f'c{i}'] = [0.0, p[1], p[2]]
    sacrum_apex = l5s1 + np.array([0.0, 0.025, -0.10])
    xiphi_level = {n: c[2] for n, c in centres.items()}
    px_check = (xiphi_level['t8'] + xiphi_level['t9']) / 2
    # head landmarks
    vertex = V[np.argmax(V[:, 2])]
    nasion, _ = closest_surface_point(V, T, np.array([0.0, -0.106, eye_z]))
    chin, _ = closest_surface_point(V, T, np.array(features['chin']))
    hp = head_surface(V, T, eye_z - 0.012, 1)
    hf, hb = hp[:, 1].min(), hp[:, 1].max()
    porion = {}
    tmj = {}
    for s, sg in SIDES.items():
        y_p = hf + 0.60 * (hb - hf)
        row = hp[np.abs(hp[:, 1] - y_p) < 0.01]
        x_out = (sg * row[:, 0]).max() if len(row) else 0.07
        porion[s] = [sg * (x_out - 0.012), y_p, eye_z - 0.012]
        tmj[s] = [sg * (x_out - 0.02), y_p - 0.013, eye_z - 0.022]
    cranium = V[V[:, 2] > eye_z]
    cranial_centre = cranium.mean(0)
    cranial_centre[0] = 0.0
    occ = np.array([0.0, hb - 0.03, eye_z - 0.01])
    neck_front = midline_profile(V, T, chin[2] - 0.045)[0]
    hyoid = np.array([0.0, neck_front + 0.012, chin[2] - 0.045])
    # ribs
    ribs = {}
    drops = {1: 0.03, 2: 0.045, 3: 0.06, 4: 0.07, 5: 0.08, 6: 0.09, 7: 0.10, 8: 0.10, 9: 0.10, 10: 0.10, 11: 0.06, 12: 0.04}
    for i in range(1, 13):
        cv = np.array(centres[f't{i}'])
        za = cv[2] - drops[i]
        sec = [l for l in plane_section(V, T, (0, 0, za), UP) if abs(l[:, 0].mean()) < 0.06 and len(l) > 40]
        P = max(sec, key=len)
        ribs[f'{i:02d}'] = {}
        for s, sg in SIDES.items():
            if i <= 7:
                xa, region = 0.03 + 0.006 * i, 'front'
            elif i <= 10:
                xa, region = 0.07 + 0.012 * (i - 8), 'front'
            else:
                xa, region = 0.11 + 0.01 * (i - 11), 'side'
            cand = P[(sg * P[:, 0] > xa - 0.01) & (sg * P[:, 0] < xa + 0.01)]
            if region == 'front':
                skin = cand[np.argmin(cand[:, 1])]
            else:
                skin = cand[np.argmax(cand[:, 1])]
            c_sec = P.mean(0)
            inward = (c_sec - skin)
            inward[2] = 0
            anterior_end = skin + unit_np(inward) * 0.015
            cvj = cv + np.array([sg * 0.022, 0.008, 0.005])
            ribs[f'{i:02d}'][s] = {'costovertebral': cvj.tolist(), 'anterior_end': anterior_end.tolist()}
    return {
        'ij_skin': entry(ij, 'Front centre of the authored "sternal notch" shoulder ring (generator S3), projected to the surface.', ['SP_THORACIC'], '+/-10 mm', 'moderate', projection_distance_m=d_ij),
        'px_skin': entry(px, 'Lower end of the authored sternal groove, projected to the surface.', [], '+/-20 mm; xiphoid not modelled', 'low', projection_distance_m=d_px),
        'ij_bone': (ij + np.array([0, 0.012, 0])).tolist(), 'px_bone': (px + np.array([0, 0.015, 0])).tolist(),
        'vertebral_body_centres': centres, 'sacrum_s1_endplate': l5s1.tolist(),
        'sacrum_apex': sacrum_apex.tolist(), 'c0_c1_centre': c0c1.tolist(), 'hyoid_est': hyoid,
        'level_model': {'anchors': {'T2/T3': float(z_top), 'L5/S1': float(z_bot)}, 'thoracic_segment_m': float(2.55 * unit_h),
                        'lumbar_segment_m': float(4.0 * unit_h), 'xiphisternal_check': {'px_skin_z_m': float(px[2]), 'model_T8_T9_z_m': float(px_check),
                        'difference_m': float(px[2] - px_check), 'source_level': 'xiphisternal joint T8/T9 (surface-anatomy references)'},
                        'depth_from_posterior_skin_m': depth, 'confidence': 'low'},
        'ribs': ribs,
        'head': {'vertex_skin': vertex.tolist(), 'nasion_skin': nasion.tolist(), 'chin_skin': chin.tolist(),
                 'cranial_centre': cranial_centre.tolist(), 'occipital_centre': occ.tolist(), 'porion_est': porion,
                 'tmj_est': tmj, 'note': 'The head has no modelled ears; porion/TMJ are proportional estimates at 60% head length behind the face, 12 mm below the authored eye ring.'},
    }


def unit_np(a):
    n = np.linalg.norm(a)
    return a / n if n > 0 else a


RUNTIME_SUFFIX = {'left': '_r', 'right': '_l'}  # anatomical side -> runtime suffix (F-SIDE-001)


def foot(V, T, sign, ajc):
    sel = (sign * V[:, 0] > 0.02) & (V[:, 2] < 0.10)
    Fv = V[sel]
    low = Fv[Fv[:, 2] < 0.05]
    heel = low[np.argmax(low[:, 1])]
    tip_y = Fv[:, 1].min()
    track = []
    for yy in np.arange(tip_y + 0.001, tip_y + 0.12, 0.002):
        loops = [l for l in plane_section(V, T, (0, yy, 0), (0, 1, 0)) if sign * l[:, 0].mean() > 0.02 and l[:, 2].max() < 0.07]
        track.append((yy, sorted(loops, key=lambda l: sign * l[:, 0].mean())))
    five = [t for t in track if len(t[1]) == 5]
    if not five:
        raise ValueError('Five separate toes not found in coronal foot sections')
    web_y = max(t[0] for t in five)          # most posterior level where all five toes are separate
    base = [t for t in five if t[0] == web_y][0][1]
    toes = {}
    forward = [t for t in track if t[0] <= web_y][::-1]   # from the web toward the tips
    for k, loop in enumerate(base):           # medial (hallux) -> lateral
        c = loop.mean(0)
        last = loop
        for yy, loops in forward[1:]:
            if not loops:
                break
            cand = min(loops, key=lambda l: np.linalg.norm(l.mean(0)[[0, 2]] - last.mean(0)[[0, 2]]))
            if np.linalg.norm(cand.mean(0)[[0, 2]] - last.mean(0)[[0, 2]]) > 0.008:
                break                          # this toe's sections have ended
            last = cand
        tip = last.mean(0)
        tip[1] = last[:, 1].min()             # most anterior section centroid (deterministic, mirror-safe)
        toes[k + 1] = {'web_centre': c, 'tip': tip}
    widths = []
    for yy in np.arange(web_y, web_y + 0.10, 0.002):
        pts = [l for l in plane_section(V, T, (0, yy, 0), (0, 1, 0)) if sign * l[:, 0].mean() > 0.02 and l[:, 2].max() < 0.09]
        if pts:
            P = np.concatenate(pts)
            widths.append((yy, P[:, 0].max() - P[:, 0].min()))
    ball_y = max(widths, key=lambda w: w[1])[0]
    fdir = toes[2]['web_centre'] - heel
    fdir[2] = 0
    fdir = unit_np(fdir)
    lat = np.array([sign, 0.0, 0.0])
    scale = float(heel[1] - tip_y) / 0.265
    mt_len = [0.063, 0.075, 0.070, 0.068, 0.068]
    out = {'heel_skin': heel.tolist(), 'toe_tip_y_m': float(tip_y), 'web_y_m': float(web_y), 'ball_widest_y_m': float(ball_y),
           'foot_length_m': float(heel[1] - tip_y), 'length_scale_vs_265mm': scale}
    mtp = {}
    behind_web = {1: 0.025, 2: 0.022, 3: 0.025, 4: 0.030, 5: 0.037}   # oblique metatarsal-head line (approximation)
    for t in range(1, 6):
        c = toes[t]['web_centre']
        mtp[t] = np.array([c[0], web_y, 0.0]) - fdir * behind_web[t] + np.array([0, 0, 0.022])
    bases = {t: mtp[t] - unit_np(np.array([mtp[t][0] - heel[0], mtp[t][1] - heel[1], 0.0])) * mt_len[t - 1] * scale for t in mtp}
    for t in range(1, 6):
        out[f'mt{t}'] = (bases[t].tolist(), mtp[t].tolist())
        tip = toes[t]['tip']
        L = mtp[t]
        if t == 1:
            ip = L + (tip - L) * 0.58
            out['hx_pp'] = (L.tolist(), ip.tolist())
            out['hx_dp'] = (ip.tolist(), (tip - unit_np(tip - L) * 0.004).tolist())
        else:
            p1 = L + (tip - L) * 0.50
            p2 = L + (tip - L) * 0.77
            out[f't{t}_pp'] = (L.tolist(), p1.tolist())
            out[f't{t}_mp'] = (p1.tolist(), p2.tolist())
            out[f't{t}_dp'] = (p2.tolist(), (tip - unit_np(tip - L) * 0.004).tolist())
    ajc = np.asarray(ajc)
    talar_head = ajc + 0.045 * fdir - 0.012 * UP - 0.005 * lat
    out['talar_head'] = talar_head.tolist()
    out['subtalar'] = (ajc - 0.030 * UP - 0.008 * fdir).tolist()
    out['heel_bone'] = [heel[0], heel[1] - 0.012, 0.035]
    nav_h = talar_head + 0.006 * fdir - 0.010 * lat
    nav_t = nav_h + 0.016 * fdir
    out['navicular'] = (nav_h.tolist(), nav_t.tolist())
    for name, t, f in (('medial', 1, 0.15), ('intermediate', 2, 0.2), ('lateral', 3, 0.2)):
        out[name] = ((nav_t + (bases[t] - nav_t) * f).tolist(), bases[t].tolist())
    b45 = (bases[4] + bases[5]) / 2
    out['cuboid'] = ((np.array(out['heel_bone']) + (b45 - np.array(out['heel_bone'])) * 0.6).tolist(), b45.tolist())
    out['toes_measured'] = {t: {'web_centre': toes[t]['web_centre'].tolist(), 'tip': toes[t]['tip'].tolist()} for t in toes}
    return out


def hand_from_stations(rig, side, wjc):
    sfx = RUNTIME_SUFFIX[side]
    R = {k[:-2]: v for k, v in rig.items() if k.endswith(sfx)}
    wjc = np.asarray(wjc)
    out = {}
    names = {2: 'index', 3: 'middle', 4: 'ring', 5: 'pinky'}
    mcp = {d: np.asarray(R[f'metacarpal_{n}'][1]) for d, n in names.items()}
    for d, n in names.items():
        axis = unit_np(mcp[d] - wjc)
        base = wjc + axis * 0.033     # carpus height between radiocarpal centre and CMC (approximation)
        out[f'mc{d}'] = (base.tolist(), mcp[d].tolist())
        out[f'd{d}_pp'] = (list(R[f'{n}_01'][0]), list(R[f'{n}_01'][1]))
        out[f'd{d}_mp'] = (list(R[f'{n}_02'][0]), list(R[f'{n}_02'][1]))
        out[f'd{d}_dp'] = (list(R[f'{n}_03'][0]), list(R[f'{n}_03'][1]))
    out['mc1'] = (list(R['thumb_01'][0]), list(R['thumb_01'][1]))
    out['th_pp'] = (list(R['thumb_02'][0]), list(R['thumb_02'][1]))
    out['th_dp'] = (list(R['thumb_03'][0]), list(R['thumb_03'][1]))
    return out, mcp


def carpals(wjc, mcp, sign):
    wjc = np.asarray(wjc)
    d = unit_np(mcp[3] - wjc)
    r = mcp[2] - mcp[5]
    r = unit_np(r - (r @ d) * d)          # radial (thumb side)
    p = np.cross(d, r) * (1 if sign > 0 else -1)
    def seg(off_d, off_r, off_p=0.0, length=0.011):
        h = wjc + d * off_d + r * off_r + p * off_p
        return (h.tolist(), (h + d * length).tolist())
    return {'scaphoid': seg(0.006, 0.012), 'lunate': seg(0.006, 0.0), 'triquetrum': seg(0.007, -0.011),
            'pisiform': seg(0.010, -0.012, 0.008, 0.007),
            'trapezium': seg(0.020, 0.016), 'trapezoid': seg(0.020, 0.007), 'capitate': seg(0.018, -0.001, 0.0, 0.015),
            'hamate': seg(0.019, -0.011)}


def fit_character(V, T, features, rig):
    """Run every recipe. Returns (landmark report, skeleton input dictionary)."""
    G = global_checks(V)
    H = G['stature_m']
    report = {'global': G, 'chirality': {s: hand_chirality(V, sg) for s, sg in SIDES.items()}, 'sides': {}}
    sides = {}
    hips = {}
    for s, sg in SIDES.items():
        a = ankle(V, T, sg, H)
        k = knee(V, T, sg, H)
        hp = pelvis_and_hip(V, T, features, sg, a, H)
        sh = shoulder(V, T, sg, H, features)
        ew = elbow_wrist(V, T, sg)
        hips[s] = hp
        report['sides'][s] = {'ankle': a, 'knee': k, 'hip': hp, 'shoulder': sh, 'elbow_wrist': ew}
    tr = trunk_and_head(V, T, features, hips)
    report['trunk'] = {k: v for k, v in tr.items() if k not in ('ribs', 'head')}
    report['head'] = tr['head']
    ij = np.array(tr['ij_skin']['value_m'])
    for s, sg in SIDES.items():
        R = report['sides'][s]
        lat = np.array([sg, 0.0, 0.0])
        ghm = np.array([m['value_m'] for m in R['shoulder']['GH_methods'].values()])
        gh = np.array([ghm[:, 0].mean(), ghm[:, 1].mean(), R['shoulder']['GH_methods']['acromion_depth_chain']['value_m'][2]])
        R['shoulder']['GH_selected'] = entry(gh, 'Height from the sourced acromion depth chain; mediolateral/anteroposterior from the mean of the three methods.',
                                             ['AHD', 'ACROMION_THICKNESS', 'HUMERAL_HEAD_RADIUS'], f'Method spread {np.ptp(ghm, axis=0).round(4).tolist()} m (x,y,z)', 'moderate')
        acr = np.array(R['shoulder']['acromion_lateral_skin']['value_m'])
        kjc = np.array(R['knee']['KJC_methods']['joint_line_plus_epicondyle_offset']['value_m'])
        ajc = np.array(R['ankle']['AJC_methods']['surface_junction']['value_m'])
        hjc = np.array(R['hip']['HJC_selected']['value_m'])
        ejc = np.array(R['elbow_wrist']['EJC']['value_m'])
        wjc = np.array(R['elbow_wrist']['WJC']['value_m'])
        jl = kjc - np.array([0, 0, R['knee']['epicondyle_offset_m']['used']])
        ts_u, ai_l = np.array([sg * 0.045, 0.150, 1.470]), np.array([sg * 0.080, 0.155, 1.320])
        TS = ts_u + 0.2 * (ai_l - ts_u) + np.array([0, -0.015, 0])
        AI = ai_l + np.array([0, -0.015, 0])
        hand, mcp = hand_from_stations(rig, s, wjc)
        sec = _leg_loop(V, T, jl[2] - 0.02, sg)
        lat_pt = sec[np.argmax(sg * sec[:, 0])]
        knee_front = _leg_loop(V, T, kjc[2], sg)
        front_y = knee_front[:, 1].min()
        pc = np.array([kjc[0], front_y + 0.014, kjc[2] + 0.005])
        lm = np.array(R['ankle']['malleolus_lateral_skin']['value_m'])
        rs = np.array(R['elbow_wrist']['styloid_radial_skin']['value_m'])
        us = np.array(R['elbow_wrist']['styloid_ulnar_skin']['value_m'])
        asis = np.array(hips[s]['asis_skin']['value_m'])
        mid_asis = (np.array(hips['left']['asis_skin']['value_m']) + np.array(hips['right']['asis_skin']['value_m'])) / 2
        si = mid_asis + np.array([sg * 0.045, 0.125, 0.035])
        sym = np.array([0.0, mid_asis[1] + 0.01, mid_asis[2] - 0.085])
        sides[s] = {
            'SC': (ij + np.array([sg * 0.025, 0.015, -0.005])).tolist(),
            'AC': (acr + np.array([-sg * 0.022, 0.0, -0.012])).tolist(),
            'AA': (acr + np.array([-sg * 0.005, 0.035, -0.010])).tolist(),
            'TS': TS.tolist(), 'AI': AI.tolist(), 'GH': gh.tolist(), 'glenoid': (gh - lat * 0.025).tolist(),
            'EJC': ejc.tolist(), 'WJC': wjc.tolist(),
            'humeroulnar': (ejc - lat * 0.008 - UP * 0.005).tolist(), 'humeroradial': (ejc + lat * 0.015 - UP * 0.015).tolist(),
            'ulnar_styloid_bone': (us + unit_np(wjc - us) * 0.006).tolist(), 'radial_styloid_bone': (rs + unit_np(wjc - rs) * 0.006).tolist(),
            'carpals': carpals(wjc, mcp, sg), 'hand': hand,
            'SI': si.tolist(), 'pubic_symphysis_side': (sym + np.array([sg * 0.004, 0, 0])).tolist(),
            'HJC': hjc.tolist(), 'KJC': kjc.tolist(), 'AJC': ajc.tolist(),
            'patella': ((pc + UP * 0.022).tolist(), (pc - UP * 0.022).tolist()),
            'tibial_plateau': jl.tolist(), 'fibular_head': (lat_pt - lat * 0.012 + np.array([0, 0.012, 0])).tolist(),
            'lateral_malleolus_bone': (lm - lat * 0.006 - UP * 0.008).tolist(),
            'foot': foot(V, T, sg, ajc),
        }
        R['derived_points'] = {k: v for k, v in sides[s].items() if k not in ('carpals', 'hand', 'foot')}
        R['foot'] = {k: v for k, v in sides[s]['foot'].items() if not isinstance(v, tuple)}
    skeleton_input = {'trunk': {**{k: v for k, v in tr.items() if k != 'head'}}, 'head': tr['head'], 'sides': sides}
    return report, skeleton_input


def make_clearance(V, T):
    """Signed distance to the skin: positive inside (generalised winding number), negative outside."""
    from scipy.spatial import cKDTree
    from joint_markers import winding_inside
    tree = cKDTree(V)

    def clearance(p):
        p = np.asarray(p, float)
        d0, _ = tree.query(p)
        q, d = closest_surface_point(V, T, p, radius=max(0.02, d0 * 1.5 + 0.01))
        inside = winding_inside(p[None, :], V, T)[0] > 0.5
        return d if inside else -d
    return clearance
