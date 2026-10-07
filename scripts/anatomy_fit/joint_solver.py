"""Phase 8: ISB joint-coordinate-system (JCS) solver and measurement for HGPT_ANATOMICAL_MASTER.

Pure numpy. Segment frames follow the ISB pattern used for the joint markers: X anterior, Y proximal/
superior, Z to the character's right (Wu et al. 2002, 2005). The proximal segment's frame is the
reference; the distal segment's relative rotation R satisfies D = P @ R @ (P0^T @ D0) for rest frames
P0, D0. Cardan sequences:
  hip, knee, ankle, elbow, wrist, spine, digits: Z (flexion) -> X (floating: ab/adduction, varus/valgus,
      inversion/eversion, lateral bending) -> Y (axial rotation)            [Grood & Suntay; ISB 2002/2005]
  glenohumeral:  Y (plane of elevation) -> X (elevation) -> Y (axial rotation)   [ISB 2005]
Clinical sign mapping (both sides): flexion/dorsiflexion +, adduction/inversion/varus +, internal rotation +.
With Z to the right for both sides, X/Y signs are mirrored for the anatomical left. Knee flexion is the
negative Z rotation (distal tibia moves posteriorly).

Rotations here are commands applied about the fitted joint centre; contact translations, coupled
follower kinematics and posture/load dependence are separate (see FOLLOWER_COUPLINGS) and remain
unaccepted until verified.
"""
import math

import numpy as np

X, Y, Z = np.eye(3)


def rot(axis, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    x, y, z = axis / np.linalg.norm(axis)
    return np.array([[c + x * x * (1 - c), x * y * (1 - c) - z * s, x * z * (1 - c) + y * s],
                     [y * x * (1 - c) + z * s, c + y * y * (1 - c), y * z * (1 - c) - x * s],
                     [z * x * (1 - c) - y * s, z * y * (1 - c) + x * s, c + z * z * (1 - c)]])


def zxy_matrix(z, x, y):
    return rot(Z, z) @ rot(X, x) @ rot(Y, y)


def zxy_angles(R):
    """Inverse of zxy_matrix. Returns (z, x, y) degrees; x in [-90, 90]."""
    x = math.degrees(math.asin(max(-1.0, min(1.0, R[2, 1]))))
    z = math.degrees(math.atan2(-R[0, 1], R[1, 1]))
    y = math.degrees(math.atan2(-R[2, 0], R[2, 2]))
    return z, x, y


def yxy_matrix(plane, elev, axial):
    return rot(Y, plane) @ rot(X, elev) @ rot(Y, axial)


def yxy_angles(R):
    """Inverse of yxy_matrix with elevation in [0, 180]; plane/axial undefined at 0/180 (returns plane=0)."""
    elev = math.degrees(math.acos(max(-1.0, min(1.0, R[1, 1]))))
    if abs(math.sin(math.radians(elev))) < 1e-9:
        return 0.0, elev, math.degrees(math.atan2(R[0, 2], R[0, 0]))
    plane = math.degrees(math.atan2(R[0, 1], R[2, 1]))
    axial = math.degrees(math.atan2(R[1, 0], -R[1, 2]))
    return plane, elev, axial


SIDE_SIGN = {'left': -1.0, 'right': 1.0, 'midline': 1.0}


def clinical_to_zxy(joint, side, flexion=0.0, adduction=0.0, internal=0.0):
    """Clinical angles -> Cardan (z, x, y) for the ISB frames used here."""
    s = SIDE_SIGN[side]
    z = -flexion if joint in ('knee',) else flexion
    return z, s * adduction, s * internal


def zxy_to_clinical(joint, side, z, x, y):
    s = SIDE_SIGN[side]
    return {'flexion': -z if joint in ('knee',) else z, 'adduction': s * x, 'internal_rotation': s * y}


def gh_command(side, plane, elevation, internal=0.0):
    """Clinical GH command -> rotation in the proximal (thorax-aligned) frame.

    plane: 0 = coronal abduction, +90 = forward flexion (sagittal), for both sides.
    elevation: angle between the humeral long axis and its rest direction (+).
    internal: twist about the humeral long axis, internal rotation +.
    Swing-twist form R = Ry(sP) Rx(-s e) Ry(s(IR - P)): pure elevation about the horizontal axis
    perpendicular to the plane, then axial twist; equal to Ry(s IR) at zero elevation.
    """
    s = SIDE_SIGN[side]
    return yxy_matrix(s * plane, -s * elevation, s * (internal - plane))


def gh_measure(side, R):
    """Inverse of gh_command (swing-twist). Also returns raw ISB Y-X-Y angles."""
    s = SIDE_SIGN[side]
    d = R @ np.array([0.0, -1.0, 0.0])
    elevation = math.degrees(math.atan2(np.linalg.norm(np.cross(d, [0.0, -1.0, 0.0])), -d[1]))   # well conditioned near 0
    plane = math.degrees(math.atan2(d[0], s * d[2])) if elevation > 1e-6 else 0.0
    swing = yxy_matrix(s * plane, -s * elevation, -s * plane)   # gh_command with zero twist
    twist = swing.T @ R
    internal = s * math.degrees(math.atan2(twist[0, 2], twist[0, 0]))
    return {'plane_of_elevation': plane, 'elevation': elevation, 'internal_rotation': internal,
            'isb_yxy_raw': yxy_angles(R)}


def frame_from_bone(head, tail):
    """ISB-pattern frame (columns X, Y, Z) for a segment from its bone head/tail at rest."""
    head, tail = np.asarray(head, float), np.asarray(tail, float)
    up, ant = np.array([0, 0, 1.0]), np.array([0, -1.0, 0])
    d = tail - head
    d = d / np.linalg.norm(d)
    if abs(d[2]) >= 0.5:
        Yd = d if d[2] > 0 else -d
        Xd = ant - (ant @ Yd) * Yd
        Xd /= np.linalg.norm(Xd)
    else:
        Xd = d if d @ ant >= 0 else -d
        Yd = up - (up @ Xd) * Xd
        Yd /= np.linalg.norm(Yd)
    return np.stack([Xd, Yd, np.cross(Xd, Yd)], axis=1)


WORLD_FRAME = np.stack([np.array([0, -1.0, 0]), np.array([0, 0, 1.0]), np.array([-1.0, 0, 0])], axis=1)  # thorax/pelvis at rest


def relative_rotation(P, D, P0, D0):
    """R such that D = P @ R @ (P0^T @ D0)."""
    return P.T @ D @ (P0.T @ D0).T


def pose_child(P0, D0, R):
    """Distal frame after applying JCS rotation R with the proximal frame at rest."""
    return P0 @ R @ (P0.T @ D0)


def world_delta(P0, R):
    """World-space rotation that maps the distal segment's rest orientation to its posed orientation."""
    return P0 @ R @ P0.T


# Follower couplings: direction sourced; magnitude only where a source value exists.
FOLLOWER_COUPLINGS = {
    'subtalar_axis': {'inclination_deg': 42.0, 'medial_deviation_deg': 23.0, 'variation': '+/-9 deg inclination',
                      'source': 'Inman (as reported in search snippets); ANKLE_GEOMETRY review',
                      'use': 'Inversion/eversion command axis from posterior-plantar-lateral to anterior-dorsal-medial.'},
    'shoulder_girdle': {'directions': 'Elevation couples clavicular elevation, retraction and posterior axial rotation; scapular upward rotation, internal rotation and posterior tilt (SHOULDER_PINS, Ludewig 2009).',
                        'magnitudes': {'sc_posterior_rotation_mean_deg': 31, 'ac_posterior_tilt_mean_deg': 19},
                        'unverified': 'Rate curves, upward rotation magnitude and plane dependence are not sourced here.'},
    'knee_screw_home': {'direction': 'Tibial external rotation in terminal extension (KNEE_SHM).', 'magnitude_deg': 3.6,
                        'source': 'Fluoroscopic dynamic knee study: tibia externally rotated 3.6 deg relative to the femur as the knee extended (search snippet); stair ascent 4 deg over 57 deg (second snippet)',
                        'shape': 'Applied linearly over the last 20 deg of extension (shape not sourced; terminal-extension locking described over the last ~10 deg).',
                        'used_in': 'coupled test knee_flexion_with_screw_home only'},
    'scapulothoracic_rhythm': {'upward_rotation_per_gh_deg': 0.43, 'max_scapular_plane': {'upward_rotation_deg': 50, 'posterior_tilt_deg': 30, 'external_rotation_deg': 24},
                               'gh_at_max_deg': 117.5,
                               'sources': ['Bone-pin study, active scapular-plane elevation (McClure et al. 2001; search snippet): 50 (SD 4.8) upward, 30 (13.0) posterior tilt, 24 (12.8) external rotation',
                                           'GH-relative rate 0.43 deg scapular upward rotation per deg GH elevation (search snippet)', 'SHOULDER_PINS: clavicular posterior rotation 31 deg'],
                               'cross_check': '0.43 x 117.5 = 50.5 deg upward rotation; 117.5 + 50.5 = 168 deg, matching the CDC humerothoracic flexion mean (168.8).',
                               'clavicle_retraction_deg': 15.0,
                               'clavicle_retraction_source': 'Secondary review snippet: clavicle retracts about 15 deg at the SC joint during elevation; elevation typically below 10 deg (bound only, not applied); posterior rotation about 30 deg (consistent with SHOULDER_PINS 31 deg)',
                               'unverified': 'Tilt/external-rotation/clavicle curves scaled linearly with GH elevation; clavicular elevation not applied (only an upper bound is sourced); plane dependence not applied.'},
    'wrist_stage_split': {'radiocarpal_fraction': None, 'evidence_conflict': 'Accessible snippets disagree (radiocarpal and midcarpal contribute almost equally to flexion versus midcarpal 65-72 percent of flexion; radiocarpal predominates flexion and midcarpal extension).',
                          'unverified': 'Gross wrist commands are split equally between radiocarpal and midcarpal and labelled unverified.'},
}
