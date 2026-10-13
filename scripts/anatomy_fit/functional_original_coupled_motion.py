"""Bounded authored shoulder coupling for original-body diagnostic evidence.

Directions follow the healthy-adult patterns reported by Ludewig et al. 2009.
The magnitudes are project-authored hypotheses, not fitted cohort trajectories.
"""

import math


COUPLED_COMPONENTS = (
    "clavicle_elevation_deg",
    "clavicle_retraction_deg",
    "clavicle_posterior_rotation_deg",
    "scapula_upward_rotation_deg",
    "scapula_posterior_tilt_deg",
    "scapula_internal_rotation_deg",
)

_TOP = {
    "clavicle_elevation_deg": 12.0,
    "clavicle_retraction_deg": 8.0,
    "clavicle_posterior_rotation_deg": 28.0,
    "scapula_upward_rotation_deg": 42.0,
    "scapula_posterior_tilt_deg": 17.0,
    "scapula_internal_rotation_deg": 8.0,
}


def pose_profile(ht_elevation_deg):
    if (
        isinstance(ht_elevation_deg, bool)
        or not isinstance(ht_elevation_deg, (int, float))
        or not math.isfinite(ht_elevation_deg)
        or not 0.0 <= ht_elevation_deg <= 160.0
    ):
        raise ValueError("finite HT elevation 0..160 required")
    angle = float(ht_elevation_deg)
    t = angle / 160.0
    response = t * t * (3.0 - 2.0 * t)
    sample = {name: _TOP[name] * response for name in COUPLED_COMPONENTS}
    sample.update({
        "ht_elevation_deg": angle,
        "plane_deg": 40.0,
        "reference_ceiling_deg": 120.0,
        "coupling_scope": "project-authored directional hypothesis",
        "cohort_trajectory_fit": False,
        "human_motion_accepted": False,
        "approval": False,
    })
    return sample


def sample_profiles(angles):
    return [pose_profile(angle) for angle in angles]
