"""Numerical triad/path QA for FUTURE reviewed landmarks, not ISB calibration.

Only synthetic examples are executable today. No Blender access, model edits,
anatomical side inference, clinical ROM limits, or muscle attachments.
"""
import argparse
import json
import math
from pathlib import Path

EPS = 1e-10


def point3(value):
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError("point must have exactly three coordinates")
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in value):
        raise ValueError("point coordinates must be finite real numbers")
    return tuple(float(v) for v in value)


def sub(a, b):
    return tuple(x-y for x, y in zip(a, b))


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def unit(v):
    n = math.sqrt(dot(v, v))
    if n < EPS:
        raise ValueError("zero-length or degenerate landmark vector")
    return tuple(x/n for x in v)


def determinant(axes):
    return dot(axes[0], cross(axes[1], axes[2]))


def verify_axes(axes):
    if not isinstance(axes, (tuple, list)) or len(axes) != 3:
        raise ValueError("frame must contain three axes")
    a = tuple(point3(x) for x in axes)
    for i in range(3):
        if abs(dot(a[i], a[i])-1.0) > 1e-7:
            raise ValueError("frame axes must have unit length")
        for j in range(i):
            if abs(dot(a[i], a[j])) > 1e-7:
                raise ValueError("frame axes must be orthogonal")
    if abs(determinant(a)-1.0) > 1e-7:
        raise ValueError("frame must be right-handed (determinant +1)")
    return a


def triad(origin, primary, plane, *, min_plane_sine=0.05):
    """Construct a *generic* proper frame: z=primary, x=projected plane, y=z cross x.

    This is NOT any ISB segment definition; primary/plane roles are synthetic
    until reviewed anatomical landmark definitions and side are supplied.
    """
    if not isinstance(min_plane_sine, (int, float)) or isinstance(min_plane_sine, bool) or not math.isfinite(min_plane_sine) or not (0 < min_plane_sine < 1):
        raise ValueError("invalid conditioning threshold")
    o, p, q = point3(origin), point3(primary), point3(plane)
    z = unit(sub(p, o))
    qv = sub(q, o)
    qn = math.sqrt(dot(qv, qv))
    if qn < EPS:
        raise ValueError("degenerate plane landmark")
    projected = sub(qv, tuple(dot(qv, z)*v for v in z))
    sine = math.sqrt(dot(projected, projected))/qn
    if sine < min_plane_sine:
        raise ValueError("nearly collinear landmark triad")
    x = unit(projected)
    y = unit(cross(z, x))
    axes = verify_axes((x, y, z))
    return {"origin": o, "axes": axes, "plane_sine": sine,
            "determinant": determinant(axes), "frame_type": "GENERIC_TRIAD_NOT_ISB"}


def rotation_angle_degrees(frame_a, frame_b):
    """Unsigned SO(3) geodesic distance; NOT flexion/elevation/pronation."""
    a = verify_axes(frame_a["axes"])
    b = verify_axes(frame_b["axes"])
    trace = sum(dot(a[i], b[i]) for i in range(3))
    cosine = max(-1.0, min(1.0, (trace-1.0)/2.0))
    return math.degrees(math.acos(cosine))


def describe_path(frames):
    if not isinstance(frames, (list, tuple)) or len(frames) < 2:
        raise ValueError("path needs at least two frames")
    for frame in frames:
        verify_axes(frame["axes"])
        point3(frame["origin"])
    steps = [rotation_angle_degrees(a, b) for a, b in zip(frames, frames[1:])]
    return {"sample_count": len(frames), "step_angles_degrees_unsigned": steps,
            "return_to_initial_degrees_unsigned": rotation_angle_degrees(frames[0], frames[-1]),
            "status": "DESCRIPTIVE_ONLY_NOT_ANATOMICAL_MOTION_VALIDATION"}


def synthetic_report():
    """All numerical examples are invented fixture coordinates, never model data."""
    origins = {
        "scapula_clavicle_humerus": ((0, 0, 0), (0, 0, 1), (1, 0, 0)),
        "elbow_radius_ulna": ((0, 0, 0), (0, 1, 0), (0, 0, 1)),
        "pelvis_femur_tibia": ((0, 0, 0), (1, 0, 0), (0, 0, 1)),
        "ankle_hindfoot_forefoot": ((0, 0, 0), (0, 0, 1), (0, 1, 0)),
    }
    rows = []
    for label, pts in origins.items():
        frame = triad(*pts)
        shift = (0.03, -0.04, 0.08)
        moved = triad(*(tuple(a+b for a, b in zip(p, shift)) for p in pts))
        path = describe_path([frame, moved, frame])
        rows.append({"synthetic_region": label, "frame_type": frame["frame_type"],
                     "determinant": frame["determinant"], "plane_sine": frame["plane_sine"],
                     "translated_return_path": path})
    return {"status": "SYNTHETIC_NUMERIC_GUARDS_ONLY", "source": "INVENTED_FIXTURE_POINTS_NOT_NATIVE_MODELS",
            "regions": rows, "native_model_landmarks_used": 0, "isb_frames_approved": False,
            "anatomical_sides_approved": False, "generic_motion_tests_executed": 0,
            "skin_deformation_approved": False, "muscle_attachments_approved": False,
            "clinical_rom_limits_applied": False, "muscle_highlighting_implemented": False,
            "warnings": ["Generic frame z/x/y are not ISB axes or joint coordinates.",
                         "Unsigned angular separation is not an anatomical joint angle.",
                         "Mirroring landmarks requires new right-handed construction and independent side review.",
                         "A low return angle alone cannot prove no skin deformation, collisions, or exercise safety."]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    report = synthetic_report()
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "synthetic_frame_math_guards.json").write_text(json.dumps(report, indent=2) + "\n")
    lines = ["# Synthetic frame-math guards — NO anatomical calibration", "",
             "Only invented landmark triads were evaluated; native landmarks bound: **0**.",
             "ISB frame approval: **NO**; generic human movement tests: **0 executed**.", "",
             "| Synthetic case | Right-handed determinant | Return to initial (unsigned degrees) |",
             "|---|---:|---:|"]
    for row in report["regions"]:
        lines.append(f"| {row['synthetic_region']} | {row['determinant']:.6f} | {row['translated_return_path']['return_to_initial_degrees_unsigned']:.6f} |")
    lines += ["", "Translation invariance and numerical conditioning are software tests, not movement validation.",
              "No original models, skin, joints, muscle attachments or ROM limits were altered.", ""]
    (args.out / "synthetic_frame_math_guards.md").write_text("\n".join(lines))
    print(report["status"], len(report["regions"]), "synthetic cases")


if __name__ == "__main__":
    main()
