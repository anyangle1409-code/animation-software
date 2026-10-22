"""Integrate reviewed attachments and visual belly proxies; no scene mutations."""
from .kernel import resolve_path, path_length, belly_axes, sphere_clearance, scalar, vec
from .registry import binding_errors


def evaluate(muscle, transforms, activation, obstacles, source_sha256, visual_gain=0):
    errors=binding_errors(muscle,set(transforms))
    if errors: raise ValueError(errors)
    b=muscle['binding']
    if b['source_sha256']!=source_sha256: raise ValueError('Binding belongs to a different source model')
    path=resolve_path(b['anchors'],transforms)
    length=path_length(path)
    tissue=muscle['tissue']
    tendons=tissue.get('tendon_lengths_m')
    if not isinstance(tendons,list) or len(tendons)!=2: raise ValueError('Two authored tendon lengths required')
    belly_length=length-sum(scalar(x,0) for x in tendons)
    axes=belly_axes(tissue.get('rest_volume_m3'),belly_length,activation,visual_gain)
    clearances=[]
    for obstacle in obstacles:
        bone=obstacle['bone']
        if bone not in transforms: raise ValueError('Missing obstacle bone')
        # Spherical obstacles require rigid world transforms: scaling would make
        # their radii invalid. Reject rather than silently rescale a sphere.
        matrix=transforms[bone]
        if len(matrix)!=4 or any(len(row)!=4 for row in matrix): raise ValueError('Invalid obstacle transform')
        matrix=tuple(tuple(scalar(x) for x in row) for row in matrix)
        if matrix[3]!=(0.,0.,0.,1.): raise ValueError('Invalid affine obstacle transform')
        for i in range(3):
            for j in range(3):
                dot=sum(matrix[k][i]*matrix[k][j] for k in range(3))
                if abs(dot-(1 if i==j else 0))>1e-6: raise ValueError('Obstacle requires rigid transform')
        local=vec(obstacle['center_local_m'])
        center=vec(tuple(sum(matrix[i][j]*local[j] for j in range(3))+matrix[i][3] for i in range(3)))
        clearance=sphere_clearance(path,center,obstacle['radius_m'])-max(axes)
        clearances.append(clearance)
        if clearance<0: raise ValueError('Muscle proxy penetrates obstacle; author via points or wrap solution')
    return {'status':'PROXY_EVALUATED_NOT_ANATOMY_VALIDATED','path_world_m':path,
            'path_length_m':length,'belly_length_m':belly_length,'belly_axes_m':axes,
            'activation':scalar(activation,0,1),'obstacle_clearances_m':clearances,
            'contact_scope':'conservative spherical envelope only; tissue/skin triangles NOT tested'}
