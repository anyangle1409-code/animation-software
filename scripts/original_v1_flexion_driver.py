"""Evaluation-time driver of the forward-flexion shoulder corrective keys (HGPT_SHOULDER_FLEX_L/R), kept OUT of the frozen pose-definition section.

install(g) wraps g['drive_shoulder_corrective'] (defined in the pose script, frozen P3a section, untouched) so that, after the abduction keys are driven,
the flexion keys are driven too:  a_flex = C1 smoothstep((theta - theta0)/(theta1 - theta0)) * (1 - lam)
  theta = humerothoracic elevation, lam = abduction fraction (1 = abduction, 0 = flexion), computed exactly as in drive_shoulder_corrective().
It is a no-op when the scene carries no 'hgpt_flexion_corrective' config (every candidate up to r83). Used by the pose test (hooked after the metrics
marker, so the frozen definition hash is unchanged) and by validation tools that replay poses.
"""


def install(g):
    bpy, math, json, Vector = g["bpy"], g["math"], g["json"], g["Vector"]
    original = g["drive_shoulder_corrective"]
    if getattr(original, "_hgpt_flexion_wrapped", False):
        return

    def drive_with_flexion():
        changed = original()
        flex_spec = bpy.context.scene.get("hgpt_flexion_corrective")
        keys = g["body"].data.shape_keys
        if keys is None:
            return changed
        fcfg = json.loads(flex_spec) if flex_spec else None
        pose = g["rig"].pose.bones
        rig = g["rig"]
        down = -(pose["spine_03"].tail - pose["spine_03"].head).normalized()
        R = pose["spine_03"].matrix.to_3x3() @ rig.data.bones["spine_03"].matrix_local.to_3x3().inverted()
        lat_t, ant_t = R @ Vector((1, 0, 0)), R @ Vector((0, -1, 0))
        for side in (("l", "r") if fcfg else ()):
            h = (pose[f"upperarm_{side}"].tail - pose[f"upperarm_{side}"].head).normalized()
            t = min(1.0, max(0.0, (math.degrees(h.angle(down)) - fcfg["theta0_deg"]) / (fcfg["theta1_deg"] - fcfg["theta0_deg"])))
            hl, ha = h.dot(lat_t), h.dot(ant_t)
            nn = hl * hl + ha * ha
            lam = 1.0 if nn < 1e-6 else hl * hl / nn
            a = t * t * (3.0 - 2.0 * t) * (1.0 - lam)
            kb = keys.key_blocks.get(fcfg["keys"][side])
            if kb is not None and abs(kb.value - a) > 1e-9:
                kb.value = a
                changed = True
        scap_spec = bpy.context.scene.get("hgpt_scapular_corrective")      # optional third key pair (r95+): scapular rotation relative to the trunk
        if scap_spec:
            scfg = json.loads(scap_spec)
            from mathutils import Matrix
            def skin_rot(name):
                return (pose[name].matrix @ rig.data.bones[name].matrix_local.inverted()).to_3x3()
            Rt = skin_rot("spine_03")
            for side in ("l", "r"):
                Rrel = Rt.transposed() @ skin_rot(f"scapula_{side}")
                tr = Rrel[0][0] + Rrel[1][1] + Rrel[2][2]
                u = math.degrees(math.acos(min(1.0, max(-1.0, (tr - 1.0) / 2.0))))
                t = min(1.0, max(0.0, (u - scfg["u0_deg"]) / (scfg["u1_deg"] - scfg["u0_deg"])))
                a = t * t * (3.0 - 2.0 * t)
                kb = keys.key_blocks.get(scfg["keys"][side])
                if kb is not None and abs(kb.value - a) > 1e-9:
                    kb.value = a
                    changed = True
        return changed

    drive_with_flexion._hgpt_flexion_wrapped = True
    g["drive_shoulder_corrective"] = drive_with_flexion
