# base for an S5 rebuild on a re-bound parent: the parent with its S5 keys (and S7, if any) and their angle props removed
import sys
sys.path.insert(0, "/home/user/p5/scripts"); sys.path.insert(0, "/home/user/p5/scripts/anatomy_fit")
import bpy
import original_v1_review_candidate_drives
src, dst = sys.argv[-2], sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]; rig = body.find_armature()
gone = [kb.name for kb in body.data.shape_keys.key_blocks[1:] if kb.name.startswith(("HGPT_S5_BAKE_", "HGPT_S7_DELT_"))]
for n in gone: body.shape_key_remove(body.data.shape_keys.key_blocks[n])
for s in "lr":
    for p in ("hgpt_s5_angles", "hgpt_s7_angles"):
        if f"{p}_{s}" in rig: del rig[f"{p}_{s}"]
print("DROPPED", len(gone))
bpy.ops.wm.save_as_mainfile(filepath=dst, copy=True)
