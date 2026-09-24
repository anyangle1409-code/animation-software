import { Matrix4 } from 'three';
import type { Vec3 } from '../rig/types';
import { vec3 } from '../rig/types';
import type { EquipmentInstance } from './types';

/**
 * Placing equipment for a character that is the canonical rig's mirror image.
 *
 * The canonical rig is built with its left on world −X while facing +Z, which
 * is the mirror image of a real body. A real character is therefore driven by
 * reflecting every canonical frame into it (x → −x; `RetargetBinding
 * .mirrorSides`), and it performs each exercise as the mirror image of the
 * rig. Its named sides stay right: the rig's left arm drives its left arm.
 *
 * Anything the rig places in world space has to be reflected with it, or it is
 * left on the wrong side of the body. Held items already are, because they
 * follow the character's own hands. What is not is everything else: a bench,
 * a rack, a cable tower, and a two-handed handle or cable whose motion is baked
 * from the rig. For a bench on the midline the difference is invisible. For a
 * tower beside the lifter it is the whole exercise: a woodchop drawn this way
 * reaches away from the pulley it is pulling from.
 *
 * The reflection used is `S·M·S`, with `S` the reflection x → −x: the item is
 * placed where the mirror puts it, turned as the mirror turns it, and remains a
 * proper rotation. That draws the same item only if the item is its own mirror
 * image about its local x = 0. Every kind in the library is, except the EZ curl
 * bar and the lat pulldown bar, which no exercise uses yet (`mirror.test.ts`
 * holds both facts).
 */

const REFLECT = new Matrix4().makeScale(-1, 1, 1);

/** `S·M·S`: a placement in canonical world space, reflected into a mirrored character's. */
export function reflectPlacement(matrix: Matrix4, target = new Matrix4()): Matrix4 {
  // multiplyMatrices reads both operands before writing, so target may be matrix.
  return target.multiplyMatrices(REFLECT, matrix).multiply(REFLECT);
}

/**
 * Whether reflecting a static item would leave it exactly where it is: on the
 * midline, and turned about x alone or by a half turn. Such items are skipped,
 * so a symmetric set-up writes exactly the bytes it did before reflection.
 */
export function mirrorInvariant(instance: Pick<EquipmentInstance, 'position' | 'rotation'>): boolean {
  const halfTurns = (degrees: number) => degrees % 180 === 0;
  return instance.position.x === 0 && halfTurns(instance.rotation.y) && halfTurns(instance.rotation.z);
}

/** A static item's position and rotation (degrees, rig Euler order) reflected x → −x. */
export function reflectedStaticPlacement(
  instance: Pick<EquipmentInstance, 'position' | 'rotation'>,
): { position: Vec3; rotation: Vec3 } {
  // Reflection negates the turns about y and z and keeps the turn about x;
  // `+ 0` keeps a zero from becoming −0, which would change the written bytes.
  return {
    position: vec3(-instance.position.x + 0, instance.position.y, instance.position.z),
    rotation: vec3(instance.rotation.x, -instance.rotation.y + 0, -instance.rotation.z + 0),
  };
}

/** A baked position/quaternion track reflected x → −x, in place. */
export function reflectBakedTrack(track: { position: number[]; quaternion: number[] }): void {
  for (let index = 0; index < track.position.length; index += 3) track.position[index] = -track.position[index] + 0;
  // S·R·S for a quaternion (x, y, z, w) is (x, −y, −z, w).
  for (let index = 0; index < track.quaternion.length; index += 4) {
    track.quaternion[index + 1] = -track.quaternion[index + 1] + 0;
    track.quaternion[index + 2] = -track.quaternion[index + 2] + 0;
  }
}
