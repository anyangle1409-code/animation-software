"""Phone/cloud Blender task. Initial task is read-only; never saves a blend."""
import hashlib,json,os,sys
from pathlib import Path
import bpy
MODEL=os.environ["MODEL"]
EXPECTED={"W8":"2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c","V14":"5969aa98122e267b6bdd94fdfaf6d2877a1b27f7ea8d11c6a8e078b467b0ff91","R120":"fb3b0acfc68bc59952b0fc6c45f7d7715717207fd9ba0b7f2b124e905ce2ddcb"}
def sha(p):
 with p.open("rb") as f:return hashlib.file_digest(f,"sha256").hexdigest()
files=list(Path(os.environ["INPUT_DIR"]).rglob("*.blend"))
assert len(files)==1,files
source=files[0]
assert sha(source)==EXPECTED[MODEL],"Source hash mismatch"
out=Path("phone-results")/MODEL
out.mkdir(parents=True,exist_ok=False)
bpy.context.preferences.filepaths.use_scripts_auto_execute=False
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
body=bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
rig=bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
m=body.data
m.calc_loop_triangles()
report={"model":MODEL,"source_sha256":sha(source),"blender":bpy.app.version_string,"saved_by":list(bpy.data.version),"vertices":len(m.vertices),"triangles":len(m.loop_triangles),"groups":len(body.vertex_groups),"shape_keys":len(m.shape_keys.key_blocks),"bones":len(rig.data.bones),"source_unchanged":sha(source)==EXPECTED[MODEL],"approved":False,"status":"READ_ONLY_CLOUD_SMOKE_TEST","known_v14_vertex_discrepancy":{"expected":238067,"actual":len(m.vertices)} if MODEL=="V14" else None,"run":os.environ.get("GITHUB_RUN_ID")}
assert report["source_unchanged"]
(out/"inventory.json").write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
