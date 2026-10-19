"""Read-only diagnostic arithmetic; no acceptance limits or production changes."""
import numpy as np

PREFIXES = tuple(f'HGPT_S{i}_' for i in range(1, 8))

def verify_clip_identity(reports, matrices):
    expected={'runtime','anatomy','basis','polygons','groups','weights','protected_keys'}
    names=reports['r41']['bone_names']
    if not names or reports['r52']['bone_names']!=names:raise ValueError('Different bone inventory/order')
    for mode in ('r41','r52'):
        r=reports[mode];a=matrices[mode]
        if r['samples']!=161 or set(r['protected_identity'])!=expected or not all(r['protected_identity'].values()):
            raise ValueError('Incomplete protected identity')
        if a.shape!=(161,len(names),4,4) or not np.isfinite(a).all():raise ValueError('Incomplete/nonfinite bone motion')
    difference=float(np.abs(matrices['r41']-matrices['r52']).max())
    if difference!=0:raise ValueError('Different bone motion')
    return difference

def family(name):
    return next((f'S{i}' for i, p in enumerate(PREFIXES, 1) if name.startswith(p)), None)

def muted_names(names, mode):
    if mode == 'all_shoulder_off':
        return [n for n in names if family(n)]
    if mode.startswith('no_S') and mode[3:] in tuple(f'S{i}' for i in range(1,8)):
        return [n for n in names if family(n) == mode[3:]]
    raise ValueError(mode)

def edge_weight_jumps(weights, edges):
    w, e = np.asarray(weights), np.asarray(edges, dtype=int)
    if w.ndim != 2 or not np.isfinite(w).all() or (w < 0).any():
        raise ValueError('Invalid weights')
    return np.abs(w[e[:, 0]] - w[e[:, 1]]).sum(axis=1)

def relative_rotation_degrees(matrices, parent):
    """Within-clip rotation magnitude from first sample, NOT ISB angles."""
    m = np.asarray(matrices, dtype=float)
    r = m[:, :3, :3]
    if parent is not None:
        r = np.linalg.solve(np.asarray(parent)[:, :3, :3], r)
    u, _, vt = np.linalg.svd(r)
    q = u @ vt
    change = np.einsum('ij,tjk->tik', q[0].T, q)
    return np.degrees(np.arccos(np.clip((np.trace(change, axis1=1, axis2=2)-1)/2, -1, 1)))

def geometry_metrics(rest, points, faces, edges, vertex_mask):
    r,p,f,e = map(np.asarray, (rest,points,faces,edges))
    ef = vertex_mask[e].any(axis=1); ff = vertex_mask[f].any(axis=1)
    rl=np.linalg.norm(r[e[:,1]]-r[e[:,0]],axis=1)
    pl=np.linalg.norm(p[e[:,1]]-p[e[:,0]],axis=1)
    ra=np.linalg.norm(np.cross(r[f[:,1]]-r[f[:,0]],r[f[:,2]]-r[f[:,0]]),axis=1)
    pa=np.linalg.norm(np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]]),axis=1)
    edge=pl[ef]/np.maximum(rl[ef],1e-12); area=pa[ff]/np.maximum(ra[ff],1e-12)
    return dict(edge_ratio_min=float(edge.min()),edge_ratio_max=float(edge.max()),
                area_ratio_min=float(area.min()),area_ratio_max=float(area.max()),
                note='Descriptive ratios to rest, not native acceptance or fold/intersection certification')
