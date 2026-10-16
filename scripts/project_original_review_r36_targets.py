"""Area-constrained vertex redistribution on the broader R35 skin surface."""
import json
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
import fair_original_review_r36_targets as fair

def constrain(p, target, rest, faces, steps=450):
    P = p
    Q = target
    F = faces
    n = len(p)

    def area(points):
        return 0.5 * np.linalg.norm(np.cross(points[F[:, 1]] - points[F[:, 0]], points[F[:, 2]] - points[F[:, 0]]), axis=1)
    a0 = area(rest)
    ap = area(P)
    free = np.linalg.norm(Q - P, axis=1) > 1e-07
    limit = 1.85 * a0
    T = Q[F]
    tree = cKDTree(T.mean(1))
    ids = np.flatnonzero(free)

    def surface_project(q):
        _, cand = tree.query(q[ids], k=32)
        tri = T[cand].reshape(-1, 3, 3)
        p = np.repeat(q[ids], 32, axis=0)
        a, b, c = (tri[:, 0], tri[:, 1], tri[:, 2])
        ab = b - a
        ac = c - a
        n = np.cross(ab, ac)
        n /= np.maximum(np.linalg.norm(n, axis=1)[:, None], 1e-15)
        proj = p - n * ((p - a) * n).sum(1)[:, None]
        v = proj - a
        d00 = (ab * ab).sum(1)
        d01 = (ab * ac).sum(1)
        d11 = (ac * ac).sum(1)
        d20 = (v * ab).sum(1)
        d21 = (v * ac).sum(1)
        den = np.maximum(d00 * d11 - d01 * d01, 1e-25)
        u = (d11 * d20 - d01 * d21) / den
        v = (d00 * d21 - d01 * d20) / den
        inside = (u >= 0) & (v >= 0) & (u + v <= 1)
        options = [proj]
        dist = [np.where(inside, ((proj - p) ** 2).sum(1), np.inf)]
        for x, y in [(a, b), (b, c), (c, a)]:
            edge = y - x
            t = np.clip(((p - x) * edge).sum(1) / np.maximum((edge * edge).sum(1), 1e-25), 0, 1)
            r = x + t[:, None] * edge
            options.append(r)
            dist.append(((r - p) ** 2).sum(1))
        choice = np.argmin(np.stack(dist, axis=1), axis=1)
        nearest = np.stack(options, axis=1)[np.arange(len(p)), choice]
        distance = ((nearest - p) ** 2).sum(1).reshape(-1, 32)
        choice = np.argmin(distance, axis=1)
        q[ids] = nearest.reshape(-1, 32, 3)[np.arange(len(ids)), choice]
        return q

    def project(q, steps):
        for step in range(steps):
            tri = q[F]
            normal = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
            ar = 0.5 * np.linalg.norm(normal, axis=1)
            normal /= np.maximum(2 * ar[:, None], 1e-15)
            grad = 0.5 * np.stack([np.cross(tri[:, 1] - tri[:, 2], normal), np.cross(tri[:, 2] - tri[:, 0], normal), np.cross(tri[:, 0] - tri[:, 1], normal)], axis=1)
            movable = free[F]
            denom = (np.sum(grad * grad, axis=2) * movable).sum(1)
            weight = (np.maximum(ar - limit, 0) + np.minimum(ar - 0.2 * a0, 0)) / np.maximum(denom, 1e-20)
            changes = -weight[:, None, None] * grad * movable[:, :, None]
            v = np.zeros_like(q)
            count = np.zeros(n)
            for k in range(3):
                np.add.at(v, F[:, k], changes[:, k])
                np.add.at(count, F[:, k], (weight != 0) * movable[:, k])
            q += 0.8 * v / np.maximum(count[:, None], 1)
            if step % 5 == 4:
                q = surface_project(q)
            if step % 100 == 0:
                print('AREA_PROJECT', step, int((area(q) / a0 > 2).sum()), flush=True)
        return q
    q = project(Q.copy(), steps)
    tn = np.cross(target[F[:, 1]] - target[F[:, 0]], target[F[:, 2]] - target[F[:, 0]])
    qn = np.cross(q[F[:, 1]] - q[F[:, 0]], q[F[:, 2]] - q[F[:, 0]])
    inversions = int(((tn * qn).sum(1) <= 0).sum())
    max_slide = float(np.linalg.norm(q - target, axis=1).max() * 1000)
    if inversions or max_slide > 40:
        raise ValueError(('Unsafe surface correspondence', inversions, max_slide))
    return (q, {'orientation_inversions': inversions, 'max_displacement_from_r34_mm': float(np.linalg.norm(q - P, axis=1).max() * 1000), 'baseline_stretched': int((ap / a0 > 2).sum()), 'target_stretched': int((area(target) / a0 > 2).sum()), 'constrained_stretched': int((area(q) / a0 > 2).sum()), 'collapse_count': int((area(q) / a0 < 0.1).sum()), 'area_ratio_min': float((area(q) / a0).min()), 'max_slide_mm': float(np.linalg.norm(q - target, axis=1).max() * 1000)})

def transition_fill(p, rest, gh_l, gh_r, gain):
    def ease(u):
        u=np.clip(u,0,1)
        return u*u*(3-2*u)
    mirror=int(np.argmin(np.linalg.norm(rest-rest[18633]*np.array([-1,1,1]),axis=1)))
    distance=np.minimum(np.linalg.norm(p-p[18633],axis=1),np.linalg.norm(p-p[mirror],axis=1))
    protection=ease((distance-.015)/.03)
    delta=np.zeros_like(p)
    for gh,sign in ((gh_r,1),(gh_l,-1)):
        rel=p-gh
        amount=(gain*.002*np.exp(-.5*((rel[:,2]+.075)/.016)**2)
                *np.exp(-.5*((sign*rel[:,0]-.035)/.1)**2)
                *np.exp(-.5*(rel[:,1]/.15)**2)*ease(sign*p[:,0]/.1)*protection)
        delta[:,0]+=sign*amount
        delta[:,1]+=amount
    return delta


def build(source, destination):
    scratch = Path(str(destination) + '.fair.npz')
    fair.targets(source, scratch)
    z = np.load(source)
    d = np.load(scratch)
    rest = z['rest_evaluated'] if 'rest_evaluated' in z else z['rest']
    result = {}
    report = {}
    for ht in (120.0, 130.0, 145.0, 156.0, 166.0):
        p = z[f'all_{ht}']
        target = p + d[str(ht)]
        if ht == 166.0:
            result[str(ht)] = np.zeros_like(p)
            report[str(ht)] = {'unchanged': True}
            continue
        q, stats = constrain(p, target, rest, z['faces'])
        gain=1. if ht<156 else .4
        fill=transition_fill(q,z['rest'],z[f'gh_l_{ht}'],z[f'gh_r_{ht}'],gain)
        q+=fill
        def normal(points):
            f=z['faces']
            return np.cross(points[f[:,1]]-points[f[:,0]],points[f[:,2]]-points[f[:,0]])
        ratio=np.linalg.norm(normal(q),axis=1)/np.maximum(np.linalg.norm(normal(rest),axis=1),1e-20)
        inversions=int(((normal(q)*normal(target)).sum(1)<=0).sum())
        stats['transition_fill_max_mm']=float(np.linalg.norm(fill,axis=1).max()*1000)
        stats['after_fill_stretched']=int((ratio>2).sum())
        stats['after_fill_collapse']=int((ratio<.1).sum())
        stats['after_fill_inversions']=inversions
        if inversions or stats['after_fill_collapse'] or stats['after_fill_stretched']>stats['baseline_stretched']:
            raise ValueError(('Target rejected after transition fill',ht,stats))
        result[str(ht)] = q - p
        report[str(ht)] = stats
        print('R36_KEY_AREA', ht, json.dumps(stats), flush=True)
    np.savez_compressed(destination, **result)
    Path(str(destination) + '.json').write_text(json.dumps(report, indent=2) + '\n')
if __name__ == '__main__':
    build(*sys.argv[1:])
