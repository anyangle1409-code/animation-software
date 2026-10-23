"""Capture read-only rig axes/pose configuration; never interpret as anatomical JCS.

Blender bone-local axes/roll, rest directions, pose rotation modes and
constraint metadata are not human joint centres/axes without external review.
No bpy.ops, assignment to rig or save operation.
"""
import math

def xyz(v):
    values = [round(float(x), 8) for x in v]
    if len(values) != 3 or not all(math.isfinite(v) for v in values):
        raise ValueError("bad rig coordinate vector")
    return values

def rest_axes_in_body(bone, rig_to_body):
    mat = rig_to_body @ bone.matrix_local
    rot = mat.to_3x3()
    result = []
    for j in range(3):
        column = rot.col[j]
        length = column.length
        if not math.isfinite(float(length)) or length <= 1e-10:
            raise ValueError(f"{bone.name}: degenerate axis {j}")
        result.append(xyz(column / length))
    dot_products = [
        abs(sum(a * b for a, b in zip(result[i], result[j])))
        for i, j in ((0, 1), (0, 2), (1, 2))
    ]
    return result, round(max(dot_products), 7)

def inspect(rig, body):
    conversion = body.matrix_world.inverted() @ rig.matrix_world
    bones = []
    pose_bones = rig.pose.bones
    for bone in rig.data.bones:
        axes, max_noncircularity = rest_axes_in_body(bone, conversion)
        pose = pose_bones.get(bone.name)
        if pose is None:
            raise ValueError(f"pose bone missing: {bone.name}")
        constraints = []
        for constraint in pose.constraints:
            target = getattr(constraint, "target", None)
            constraints.append({
                "name": constraint.name, "type": constraint.type,
                "influence_as_loaded": round(float(constraint.influence), 6),
                "target_object_name": target.name if target is not None else None,
                "target_bone": getattr(constraint, "subtarget", None),
            })
        bones.append({
            "name": bone.name, "parent": bone.parent.name if bone.parent else None,
            "rest_head_body_local_m": xyz(conversion @ bone.head_local),
            "rest_tail_body_local_m": xyz(conversion @ bone.tail_local),
            "rest_local_X_Y_Z_unit_in_body_coordinates": axes,
            "axis_noncircularity_dot_max": max_noncircularity,
            "roll_radians_stored": None,
            "roll_note": "Bone does not expose EditBone.roll outside Edit Mode; orientation retained in rest_local_X_Y_Z_unit_in_body_coordinates",
            "use_deform": bool(bone.use_deform),
            "connected_to_parent": bool(bone.use_connect),
            "pose_rotation_mode": pose.rotation_mode,
            "pose_constraint_metadata": constraints,
        })
    modifier_rows = []
    for mod in body.modifiers:
        target = getattr(mod, "object", None)
        modifier_rows.append({
            "name": mod.name, "type": mod.type,
            "target_object_name": target.name if target is not None else None,
            "enabled_in_viewport": bool(mod.show_viewport),
            "enabled_for_render": bool(mod.show_render),
        })
    return {
        "status": "BLENDER_LOCAL_BONE_AXIS_INVENTORY_ONLY_ANATOMICAL_MAPPING_NOT_APPROVED",
        "bone_count": len(bones), "bones": bones,
        "body_object": body.name, "rig_object": rig.name,
        "body_modifier_metadata": modifier_rows,
        "coordinate_description": "body object-local metres, rest-pose bone LOCAL X/Y/Z directions",
        "model_motion_axes_calibrated_to_ISB": False,
        "actual_anatomical_joint_centres_verified": False,
        "anatomical_side_mapped": False,
        "native_human_ROM_limits_validated": False,
        "any_bones_rotated_or_keyframed": False,
        "limitations": [
            "A Blender bone-local X/Y/Z basis is NOT automatically the ISB joint-coordinate system",
            "Bone head/tail are authored rig controls, NOT necessarily anatomical joint centres",
            "Bone roll, constraint and saved pose metadata are descriptive, not physiological validity",
            "Side names and measured X sign alone do not certify anatomical left/right",
            "Clinical ROM group means are not numeric safety clamps on these bone rotations",
            "Skin, muscle paths and contact still require independently validated movement tests",
        ],
    }

def validate(report):
    errors = []
    if report.get("status") != "BLENDER_LOCAL_BONE_AXIS_INVENTORY_ONLY_ANATOMICAL_MAPPING_NOT_APPROVED":
        errors.append("invalid read-only anatomy status")
    for key in ("model_motion_axes_calibrated_to_ISB", "actual_anatomical_joint_centres_verified",
                "anatomical_side_mapped", "native_human_ROM_limits_validated",
                "any_bones_rotated_or_keyframed"):
        if report.get(key) is not False:
            errors.append("unearned calibration or model modification: " + key)
    bones = report.get("bones", [])
    if not bones or report.get("bone_count") != len(bones):
        errors.append("bone inventory missing/count mismatch")
    names = [b.get("name") for b in bones]
    if any(not isinstance(name, str) or not name for name in names) or len(names) != len(set(names)):
        errors.append("duplicate or invalid bone names")
    nameset = set(names)
    for bone in bones:
        if bone.get("parent") is not None and bone["parent"] not in nameset:
            errors.append("unknown rig parent: " + str(bone.get("name")))
        if bone.get("parent") == bone.get("name"):
            errors.append("self parented bone")
        for field in ("rest_head_body_local_m", "rest_tail_body_local_m"):
            v = bone.get(field, [])
            if (len(v) != 3 or not all(isinstance(x, (int, float)) and
                                       not isinstance(x, bool) and math.isfinite(x) for x in v)):
                errors.append("bad rest coordinate: " + str(bone.get("name")))
        axes = bone.get("rest_local_X_Y_Z_unit_in_body_coordinates", [])
        if len(axes) != 3 or any(len(v) != 3 for v in axes):
            errors.append("invalid axis basis")
            continue
        for axis in axes:
            if not all(isinstance(x, (int, float)) and math.isfinite(x) for x in axis):
                errors.append("nonfinite axis")
            elif abs(sum(x*x for x in axis)-1) > 0.002:
                errors.append("axis was not unit length")
        if not isinstance(bone.get("pose_rotation_mode"), str) or not bone["pose_rotation_mode"]:
            errors.append("missing pose rotation mode")
    return errors
