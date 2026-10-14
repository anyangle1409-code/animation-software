"""Shoulder root-cause diagnostic (14 Oct 2026; docs/CLAUDE_SHOULDER_DETACHED_ARM_ROOT_CAUSE_20261014.md). Diagnostic only."""
import pathlib as _pl
ROOT = str(_pl.Path(__file__).resolve().parents[2])
import sys, math
sys.path.insert(0, ROOT + "/scripts"); sys.path.insert(0, ROOT + "/scripts/anatomy_fit")
import bpy
bpy.ops.wm.open_mainfile(filepath=ROOT + "/ORIGINAL_V1_WORK/anatomy/audit/HGPT_ANATOMICAL_AUDIT_r95_a003.blend")
import build_functional_shoulder_correction_blender as correction
import build_functional_original_coupled_motion_blender as coupled
res = correction.build_corrected_scene(); rig = res["runtime"]; pb = rig.pose.bones
b = rig.data.bones["scapula_r"]
f = lambda v: [round(c, 2) for c in v]
print("AX scapula_r local axes in world: x", f(b.matrix_local.col[0][:3]), "y", f(b.matrix_local.col[1][:3]), "z", f(b.matrix_local.col[2][:3]))
print("PROFILE160", {k: round(v, 1) for k, v in __import__("functional_original_coupled_motion" if False else "build_functional_original_coupled_motion_blender").motion.pose_profile(160).items() if isinstance(v, (int, float))})
for comp in ("x", "y", "z"):
    for s in ("r",):
        for p in pb: p.matrix_basis.identity()
        pb["scapula_r"].matrix_basis = coupled._rotation(**{comp: 30.0})
        bpy.context.view_layer.update()
        print("AX", comp, "+30: scap tail", [round(c*1000) for c in pb["scapula_r"].tail], "(rest 138,111,1364) | upperarm head (glenoid side)", [round(c*1000) for c in pb["upperarm_r"].head], "(rest 215,30,1515)")
