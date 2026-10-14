"""Shoulder root-cause diagnostic (14 Oct 2026; docs/CLAUDE_SHOULDER_DETACHED_ARM_ROOT_CAUSE_20261014.md). Diagnostic only."""
import pathlib as _pl
ROOT = str(_pl.Path(__file__).resolve().parents[2])
import sys, math
sys.path.insert(0, ROOT + "/scripts"); sys.path.insert(0, ROOT + "/scripts/anatomy_fit")
import bpy
from mathutils import Quaternion
bpy.ops.wm.open_mainfile(filepath=ROOT + "/ORIGINAL_V1_WORK/anatomy/audit/HGPT_ANATOMICAL_AUDIT_r95_a003.blend")
import build_functional_shoulder_correction_blender as correction
import original_v1_review_candidate_drives as drives
res = correction.build_corrected_scene(); rig = res["runtime"]
def st(child, parent):
    q = drives._rel_quat(rig, child, parent)
    if q.w < 0: q.negate()
    tw = Quaternion((q.w, 0, q.y, 0)).normalized(); sw = q @ tw.inverted()
    if sw.w < 0: sw.negate()
    t = math.degrees(2 * math.atan2(tw.y, tw.w)); t = (t + 180) % 360 - 180
    return round(math.degrees(q.angle), 1), round(math.degrees(sw.angle), 1), round(t, 1)
pb = rig.pose.bones
for ht in (0, 45, 90, 120, 145, 160):
    correction.apply_corrected_pose(res, ht)
    arm = (pb["upperarm_r"].tail - pb["upperarm_r"].head).normalized()
    down = -(pb["spine_03"].tail - pb["spine_03"].head).normalized()
    print("ST", ht, "HT measured", round(math.degrees(arm.angle(down)), 1), "| arm vs scapula total/swing/twist", st("upperarm_r", "scapula_r"),
          "| scapula vs thorax", st("scapula_r", "spine_03"), "| clavicle vs thorax", st("clavicle_r", "spine_03"))
print("PARENTS", rig.data.bones["upperarm_r"].parent.name, rig.data.bones["scapula_r"].parent.name, rig.data.bones["clavicle_r"].parent.name)
