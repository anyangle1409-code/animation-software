# copy a blend with the shoulder corrective shape-key families removed (review measurement only)
import sys
sys.path.insert(0, "/home/user/p5/scripts"); sys.path.insert(0, "/home/user/p5/scripts/anatomy_fit")
import bpy
import original_v1_review_candidate_drives
src, dst = sys.argv[-2], sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
PRE = ("HGPT_SHOULDER_", "HGPT_C1_ARMTRUNK_", "HGPT_S1_", "HGPT_S2_", "HGPT_S3_", "HGPT_S4_", "HGPT_S5_", "HGPT_S6_", "HGPT_S7_")
gone = [kb.name for kb in body.data.shape_keys.key_blocks[1:] if kb.name.startswith(PRE)]
for n in gone:
    body.shape_key_remove(body.data.shape_keys.key_blocks[n])
print("REMOVED", len(gone))
bpy.ops.wm.save_as_mainfile(filepath=dst, copy=True)
