"""Inspect native R53 capture without changing any model or accepting geometry."""
from pathlib import Path
import sys,json
import numpy as np
from original_review_r53_diagnostics import edge_weight_jumps

def main(root):
    root=Path(root);result={'diagnostic_only':True,'model_saved':False,'repair_complete':False,'modes':{}}
    for mode in ('r41','r52'):
        p=root/mode;r=json.loads((p/'diagnosis.json').read_text());w=np.load(p/'rest_weights.npz');clip=np.load(p/'clip.npz')
        rest,W,edges=w['rest'],w['weights'],w['edges'];names=r['group_names'];ids=w['shoulder_ids'];rows=[]
        selected=[19057,20913]
        jumps=edge_weight_jumps(W,edges)
        for vertex in selected:
            connected=np.flatnonzero((edges==vertex).any(axis=1));weights=[dict(group=names[i],weight=float(x)) for i,x in enumerate(W[vertex]) if x>1e-6]
            weights.sort(key=lambda x:-x['weight'])
            row=dict(vertex=vertex,rest_world_m=rest[vertex].tolist(),weights=weights,
                maximum_incident_l1_weight_jump=float(jumps[connected].max()),
                incident_edges=edges[connected].tolist())
            found=np.flatnonzero(ids==vertex)
            if len(found):
                j=int(found[0]);row['family_effects']={}
                for variant in r['muted_names']:
                    d=clip[variant][:,j];row['family_effects'][variant]=dict(maximum_mm=float(np.linalg.norm(d,axis=1).max()*1000),
                        t050_mm=(d[80]*1000).tolist(),t080_mm=(d[128]*1000).tolist())
            rows.append(row)
        # Report strongest topology weight jumps without asserting an anatomical defect.
        result['modes'][mode]=dict(vertices=rows,rest_extent_m=r['rest_extent_m'],modifiers=r['modifiers'],
            highest_weight_jump_edges=r['highest_weight_jump_edges'][:20],
            limitations=['Weight discontinuity alone does not prove a bad contour.','Ablations retain identical bones and elbow corrections.','No physical muscles are reconstructed from bone names.'])
    (root/'r53_weight_key_attribution.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main(sys.argv[1])
