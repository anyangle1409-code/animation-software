import { HUMANOID_BONES } from './humanoid';
import { Skeleton } from './skeleton';
import type { BoneDefinition } from './types';

/**
 * The rig as it was before the scapulae: the same bones in the same order,
 * with each upper arm hung from its clavicle again.
 *
 * It exists for one job — proving the 55-bone rig still moves exactly like the
 * 53-bone rig it replaced while the scapulae rest. It is derived from the live
 * definitions rather than kept as a copy, so every other bone is guaranteed to
 * be the one in use now, and the only difference between the two skeletons is
 * the one under test. Nothing outside equivalence tests should build on it.
 */
export function skeletonWithoutScapula(): Skeleton {
  const definitions: BoneDefinition[] = HUMANOID_BONES.filter(
    (bone) => bone.name !== 'scapula_l' && bone.name !== 'scapula_r',
  ).map((bone) => {
    if (bone.name === 'upperarm_l') return { ...bone, parent: 'clavicle_l' };
    if (bone.name === 'upperarm_r') return { ...bone, parent: 'clavicle_r' };
    return bone;
  });
  return new Skeleton(definitions);
}
