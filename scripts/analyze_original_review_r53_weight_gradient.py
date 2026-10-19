"""Native-checked linear skinning edge decomposition; never edits weights or models."""
import sys,json
from pathlib import Path
import numpy as np

def main(capture,probe):
    capture,probe=Path(capture),Path(probe);mode='r41'
    report=json.loads((capture/mode/'diagnosis.json').read_text());pr=json.loads((probe/mode/'origin_probe.json').read_text())
    if report['bone_names']!=pr['bone_names']:raise ValueError('Bone order mismatch')
    if any(not n.startswith(tuple('HGPT_S'+str(i)+'_' for i in range(1,8))) for n in report['active_keys'][160]):raise ValueError('Non-shoulder active keys')
    z=np.load(capture/mode/'rest_weights.npz');rest=z['rest'];groups=report['group_names'];names=report['bone_names'];weights=z['weights']
    rb=np.load(probe/mode/'rest_bones.npz');clip=np.load(capture/mode/'clip.npz');snap=np.load(capture/mode/'snapshots.npz')
    T=clip['bone_matrices'][160]@np.linalg.inv(rb['matrices'])@np.linalg.inv(rb['rig_matrix_world'])@rb['body_matrix_world']
    W=np.stack([weights[:,groups.index(n)] if n in groups else np.zeros(len(rest)) for n in names],axis=1)
    if not np.allclose(W.sum(1),1,atol=1e-6):raise ValueError('Missing deform weights')
    A=np.einsum('nb,bij->nij',W,T);h=np.column_stack((rest,np.ones(len(rest))))
    predicted=np.einsum('nij,nj->ni',A,h)[:,:3];native=snap['all_shoulder_off_160']
    error=float(np.linalg.norm(predicted-native,axis=1).max()*1000)
    if error>.01:raise ValueError(('Unvalidated reconstruction',error))
    a,b=18081,21057;dr=h[b]-h[a];fixed=(A[a]@dr)[:3];gradient=((A[b]-A[a])@h[b])[:3]
    actual=native[b]-native[a];added=(snap['baseline_160'][b]-snap['baseline_160'][a])-actual
    result=dict(diagnostic_only=True,model_saved=False,repair_complete=False,frame=160,edge=[a,b],full_body_native_LBS_reconstruction_max_error_mm=error,
        rest_edge_length_mm=float(np.linalg.norm(dr[:3])*1000),raw_native_edge_length_mm=float(np.linalg.norm(actual)*1000),corrected_native_edge_length_mm=float(np.linalg.norm(snap['baseline_160'][b]-snap['baseline_160'][a])*1000),
        fixed_weight_edge_term_mm=(fixed*1000).tolist(),weight_gradient_term_mm=(gradient*1000).tolist(),raw_edge_reconstruction_error_mm=float(np.linalg.norm(fixed+gradient-actual)*1000),corrective_added_edge_vector_mm=(added*1000).tolist(),
        weights={str(v):{groups[i]:float(x) for i,x in enumerate(weights[v]) if x>1e-6} for v in (a,b)},limitations=['Vector norms cannot be added as scalar lengths.','Exact attribution for this edge/pose, not a complete whole-outline diagnosis.','No counterfactual weights are applied.','Candidate still requires all original safety and acceptance tests.'])
    (probe/'r53_weight_gradient_decomposition.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main(*sys.argv[1:3])
