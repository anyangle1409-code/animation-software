"""Separate authored shallow costal blade; no measured anatomy/contact claim."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_functional_absolute_reach_blender as reach
from functional_shoulder_shapes import scapula_bowl_mesh

VERSION = 'PROVISIONAL_SCAPULA_BOWL_v1'


def build(rec):
    shoulder = reach.context.shoulder
    arm, shapes = shoulder.build(rec)
    for side in ('left', 'right'):
        landmarks = [tuple(x/1000 for x in p) for p in rec['candidate']['scapula_landmarks_world_mm'][side]]
        perimeter = [landmarks[i-1] for i in (3,4,5,6,7,8,9,12,13,15,18,1,2)]
        vertices, faces = scapula_bowl_mesh(perimeter, .008)
        ob = next(ob for ob in shapes if ob.name.split('.')[0] == 'scapula_blade_' + side)
        material = ob.data.materials[0]
        # Old vertex group contains only28 IDs; recreate full rigid weighting.
        ob.vertex_groups.clear()
        mesh = shoulder.bpy.data.meshes.new(ob.name + '_curved')
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        mesh.materials.append(material)
        ob.data = mesh
        group = ob.vertex_groups.new(name='scapula_' + side)
        group.add(list(range(len(vertices))), 1, 'REPLACE')
        ob['anatomy_approved'] = False
        ob['authored_costal_recession_m'] = .008
        ob['status'] = 'AUTHORED_CURVED_GUIDE_NOT_CONTACT_OR_ANATOMY_APPROVED'
    return arm, shapes


if __name__ == '__main__':
    reach.context.main(pose_fn=reach.pose_absolute, version=VERSION, angles=(0,90,160),
                       build_fn=build,
                       shape_notes=['Blade interior posterior recession8mm/normal thickness4mm are authored assumptions',
                                    'Border landmark midplanes and all joint/control centres unchanged; no rib-contact fit'],
                       motion_note='CURVED BLADE /8mm AUTHORED / CONTACT AND HUMAN MOTION NOT APPROVED')
