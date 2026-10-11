"""Absolute humerothoracic direction, not validated GH/SC/ST joint kinematics.

Scapular-plane40deg follows the experimental plane in Ludewig2009
doi10.2106/JBJS.G.01483; no cohort angles or subject surfaces copied.
The retained clavicle/scapula response remains artist-authored.
"""
import math
import sys
from pathlib import Path
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_functional_thorax_context_blender as context

VERSION = 'PROVISIONAL_ABSOLUTE_SCAPULAR_REACH_v1'


def pose_absolute(arm, rec, angle):
    if type(angle) not in (int, float) or not 0 <= angle <= 160:
        raise ValueError('finite absolute HT elevation0..160 required')
    context.shoulder.pose(arm, rec, angle)
    elevation, plane = math.radians(angle), math.radians(40)
    for side, sign in [('left', 1), ('right', -1)]:
        bone = arm.pose.bones['humerus_' + side]
        pivot = bone.head.copy()
        current = (bone.tail - bone.head).normalized()
        target = Vector((sign * math.sin(elevation) * math.cos(plane),
                         -math.sin(elevation) * math.sin(plane), -math.cos(elevation)))
        # Shortest-arc pose correction fixes shaft direction, NOT clinical axial
        # rotation: epicondylar landmarks/local anatomical frame remain missing.
        rotation = current.rotation_difference(target).to_matrix().to_4x4()
        bone.matrix = Matrix.Translation(pivot) @ rotation @ Matrix.Translation(-pivot) @ bone.matrix
        bpy.context.view_layer.update()


if __name__ == '__main__':
    context.main(pose_fn=pose_absolute, version=VERSION, angles=(0, 90, 160),
                 motion_note='ABSOLUTE HT / SCAPULAR PLANE40deg / COUPLING AUTHORED / NO HUMAN MOTION PASS')
