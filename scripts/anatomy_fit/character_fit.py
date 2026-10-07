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
