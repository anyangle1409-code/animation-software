import { HUMANOID_BONES } from './humanoid';
import { Skeleton } from './skeleton';
import type { AxisLimit, BoneDefinition } from './types';

/**
 * The canonical rig as it was at each earlier skeleton version, derived from
 * the live definitions rather than kept as copies.
 *
 *   v1  53 bones  hgpt_canonical_v1  before the scapulae
 *   v2  55 bones  hgpt_canonical_v2  scapulae; before the metacarpals and the
 *                                    thumb base's third axis
 *
 * They exist for one job: proving the current rig still moves exactly as the
 * earlier ones did while the bones added since stay at rest. Deriving them
 * means every other bone is guaranteed to be the one in use now, so the only
 * differences between the skeletons are the ones under test. Each reproduces
 * its version's recorded baseline bit for bit. Nothing outside equivalence
 * tests should build on them.
 */

const label = (min: number, max: number, positive: string, negative: string): AxisLimit => ({
  min,
  max,
  positive,
  negative,
});

/** The thumb base as it was before it had an axial axis. */
function earlierThumb(bone: BoneDefinition): BoneDefinition {
  const mirrored = bone.name.endsWith('_r');
  return {
    ...bone,
    limits: {
      x: label(-14, 14, 'Spread towards thumb', 'Spread towards little finger'),
      y: null,
      z: mirrored ? label(-60, 25, 'Extension', 'Flexion') : label(-25, 60, 'Flexion', 'Extension'),
    },
  };
}

function derive(keepScapulae: boolean): Skeleton {
  const definitions: BoneDefinition[] = HUMANOID_BONES.filter(
    (bone) => !bone.name.startsWith('metacarpal_') && (keepScapulae || !bone.name.startsWith('scapula_')),
  ).map((bone) => {
    if (/^thumb_01_[lr]$/.test(bone.name)) return earlierThumb(bone);
    if (bone.parent?.startsWith('metacarpal_')) return { ...bone, parent: `hand_${bone.name.slice(-1)}` } as BoneDefinition;
    if (!keepScapulae && bone.parent?.startsWith('scapula_')) {
      return { ...bone, parent: `clavicle_${bone.name.slice(-1)}` } as BoneDefinition;
    }
    return bone;
  });
  return new Skeleton(definitions);
}

/** The 53-bone rig, `hgpt_canonical_v1`. */
export const skeletonV1 = (): Skeleton => derive(false);
/** The 55-bone rig, `hgpt_canonical_v2`. */
export const skeletonV2 = (): Skeleton => derive(true);
