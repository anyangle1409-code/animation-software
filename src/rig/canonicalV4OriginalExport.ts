import { HGPT_CANONICAL_V4_ORIGINAL_BONES, HGPT_CANONICAL_V4_ORIGINAL_ID } from './canonicalV4Original';

/** The sole numerical-rest source for the clean-room Blender armature. */
export function originalV4RigData() {
  return {
    identity: HGPT_CANONICAL_V4_ORIGINAL_ID,
    coordinate_system: 'project_x_right_y_up_z_forward',
    bones: HGPT_CANONICAL_V4_ORIGINAL_BONES.map(b => ({
      name: b.name,
      parent: b.parent,
      head: [b.head.x, b.head.y, b.head.z],
      tail: [b.tail.x, b.tail.y, b.tail.z],
    })),
  };
}
