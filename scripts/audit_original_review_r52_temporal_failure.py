"""Read-only reproduction of R52's dense motion failure; writes no model."""
from pathlib import Path
import argparse, hashlib, json
import numpy as np


def audit(root):
    source = np.load(root/'source.npz')
    dense = np.load(root/'dense_motion.json.points.npz')
    coarse = np.load(root/'native_final.json.points.npz')['points']
    baseline, current, ids = (dense[k] for k in ('baseline','current','back_vertex_ids'))
    before = np.linalg.norm(np.diff(baseline,n=2,axis=0),axis=2)*1000
    after = np.linalg.norm(np.diff(current,n=2,axis=0),axis=2)*1000
    excess = after-before
    i,j = np.unravel_index(excess.argmax(),excess.shape)
    t = np.arange(161)/160
    # Existing v4 press path in the R41/R52 evidence: start70, lockout166.
    ht = 70+96*(3*t*t-2*t*t*t)
    outward = (current-baseline)[:,:,0]*np.sign(source['rest'][ids,0])[None]*1000
    early = np.where(ht[:,None]<110,outward,-np.inf)
    ei,ej = np.unravel_index(early.argmax(),early.shape)
    controls = np.load(root/'solved.npz')['dense_delta']
    vertex = int(ids[j])
    report = dict(control_118_curvature_mm=float(np.linalg.norm(controls[24,vertex]-2*controls[23,vertex]+controls[22,vertex])*1000),control_118_119_step_mm=float(np.linalg.norm(controls[24,vertex]-controls[23,vertex])*1000),model_modified=False,model_saved=False,source_sha256=hashlib.sha256((root/'source.npz').read_bytes()).hexdigest(),
        coarse_baseline_match_max_mm=float(np.linalg.norm(baseline[::4]-source['base'][:41,ids],axis=2).max()*1000),
        coarse_current_match_max_mm=float(np.linalg.norm(current[::4]-coarse[:41,ids],axis=2).max()*1000),
        original41_motion_excess_mm=float((np.linalg.norm(np.diff(current[::4],n=2,axis=0),axis=2)-np.linalg.norm(np.diff(baseline[::4],n=2,axis=0),axis=2)).max()*1000),
        worst_dense=dict(vertex=int(ids[j]),center_frame=int(i+1),t=float(t[i+1]),ht_deg=float(ht[i+1]),
            baseline_second_difference_mm=float(before[i,j]),r52_second_difference_mm=float(after[i,j]),
            excess_mm=float(excess[i,j]),normalized_excess_mm=float(excess[i,j]*16),
            local_times=t[i:i+3].tolist(),added_world_increment_mm=((current-baseline)[i:i+3,j]*1000).tolist()),
        early_outward=dict(vertex=int(ids[ej]),frame=int(ei),t=float(t[ei]),ht_deg=float(ht[ei]),outward_increment_mm=float(early[ei,ej])),
        conclusion='At the worst measured back point, the added R52 corrective creates the abrupt change. Original41 sampling misses its severity. This does not independently validate every skeleton bone or exclude baseline issues elsewhere.')
    return report,(t,baseline[:,j],current[:,j],int(ids[j]),ht)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--response',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    report,values=audit(args.response);args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'r52_temporal_failure.json').write_text(json.dumps(report,indent=2)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    t,b,p,v,ht=values
    fig,axes=plt.subplots(2,1,figsize=(10,7),layout='constrained')
    sign=np.sign(b[80,0]);axes[0].plot(t,sign*b[:,0]*1000,label='R41 baseline');axes[0].plot(t,sign*p[:,0]*1000,label='R52 actual skin')
    axes[0].set(xlabel='Press progress',ylabel='Distance from centre, mm',title=f'Actual back skin trajectory: vertex {v}');axes[0].legend();axes[0].grid(alpha=.25)
    mask=(t>=.475)&(t<=.525);change=(p-b)*1000
    for k,label in enumerate(('Side-to-side','Front-to-back','Vertical')):axes[1].plot(t[mask],change[mask,k],marker='o',label=label)
    axes[1].axvline(.5,color='black',ls=':',alpha=.5);axes[1].set(xlabel='Press progress',ylabel='Added skin correction, mm',title='Mid-press: correction changes direction sharply near 118 degrees');axes[1].legend();axes[1].grid(alpha=.25)
    fig.suptitle('R52 diagnosis — measured geometry, no model changes',fontsize=15);fig.savefig(args.out/'r52_back_motion_diagnosis.png',dpi=160)
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
