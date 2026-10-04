import json, runpy, sys, tempfile
from pathlib import Path
import numpy as np

# Small symmetric synthetic mesh: verifies mirror closure and that only strict min-ratio regression targets seed the declaration.
with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    rest=np.array([[-1.,0,0],[-.5,0,0],[.5,0,0],[1.,0,0]])
    edges=np.array([[0,1],[2,3]])
    ev=np.array([rest.copy()])
    ev[0,1,0]=-.9; ev[0,2,0]=.9
    np.savez(td/"d.npz",rest=rest,edges=edges,region=np.array([0,0,0,0]),region_names=np.array(["arm"]),
             poses=np.array(["press_top"]),evaluated=ev)
    cmp={"comparison_tolerances":{"region_min_ratio_drop":.02},"regressions":[
        {"name":"press_top","region":"arm","metric":"region_min_ratio","baseline":1.0,"candidate":.2}]}
    (td/"c.json").write_text(json.dumps(cmp))
    old=sys.argv
    sys.argv=["x",str(td/"d.npz"),str(td/"c.json"),str(td/"o.json"),"--targets","press_top/arm","--top-edges","1","--rings","0"]
    runpy.run_path(str(Path(__file__).with_name("declare_original_v1_p3b1_minratio_zone.py")),run_name="__main__")
    sys.argv=old
    o=json.loads((td/"o.json").read_text())
    assert o["zone_vertices"]==4
    assert len(o["left_owned_vertex_ids"])==2 and len(o["mirror_of_strict_left_vertex_ids"])==2
print("PASS")
