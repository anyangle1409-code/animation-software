import { describe, expect, it } from 'vitest';
import { Euler, Quaternion, Vector3 } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { skeletonWithoutScapula } from '../rig/withoutScapula';
import { EULER_ORDER } from '../rig/types';
import type { Skeleton } from '../rig/skeleton';
import { generateClip } from '../animation/generate';
import { resolveFrame } from '../animation/pipeline';
import { lockAnchors } from '../constraints/locks';
import { sampleClip } from '../animation/clip';
import { EXERCISES } from '../exercises/library';
import { ANATOMICAL_SKIN_BONES, buildAnatomicalBodyGeometry } from './anatomical';
import { ANATOMICAL_SKIN_INDICES } from './anatomicalSkinIndices';
import { buildSkinnedRig } from './skin';

/**
 * The mannequin's baked skin numbers its bones by their position in the rig it
 * was generated against, and the scapulae moved every bone below the clavicles
 * along by one. Read positionally, 8,387 of its 13,952 vertices would have been
 * bound to the wrong bone. The skin is resolved by name instead, and held here
 * to the names it was baked with, on the 55-bone rig and the 53-bone rig alike.
 */
const legacy = skeletonWithoutScapula();

const baked = (() => {
  const decoded = atob(ANATOMICAL_SKIN_INDICES);
  const bytes = new Uint8Array(decoded.length);
  for (let index = 0; index < decoded.length; index += 1) bytes[index] = decoded.charCodeAt(index);
  return new Uint16Array(bytes.buffer);
})();

describe('the mannequin skin, resolved by bone name', () => {
  it('names the 53 bones it was baked against, in their baked order', () => {
    expect(ANATOMICAL_SKIN_BONES).toEqual(legacy.bones.map((bone) => bone.name));
    expect(Math.max(...baked)).toBeLessThan(ANATOMICAL_SKIN_BONES.length);
  });

  it.each([
    ['55-bone rig', canonicalSkeleton],
    ['53-bone rig', legacy],
  ] as [string, Skeleton][])('binds every influence to its baked bone on the %s', (_label, rig) => {
    // Without repairs: those rewrite weights on purpose, and this is about the
    // baked binding itself.
    const geometry = buildAnatomicalBodyGeometry(rig, { repair: false }).geometry;
    const slots = geometry.getAttribute('skinIndex');
    for (let entry = 0; entry < baked.length; entry += 1) {
      const vertex = Math.floor(entry / 4);
      const lane = entry % 4;
      expect(rig.bones[slots.getComponent(vertex, lane)].name).toBe(ANATOMICAL_SKIN_BONES[baked[entry]]);
    }
  });

  it('deforms exactly as it did on the 53-bone rig through every exercise', () => {
    const pose = (rig: Skeleton, built: ReturnType<typeof buildSkinnedRig>, rotations: Record<string, { x: number; y: number; z: number } | undefined>) => {
      for (const bone of rig.bones) {
        const node = built.boneByName.get(bone.name)!;
        const rotation = rotations[bone.name] ?? { x: 0, y: 0, z: 0 };
        node.quaternion
          .copy(bone.restLocalQuaternion)
          .multiply(new Quaternion().setFromEuler(new Euler(rotation.x, rotation.y, rotation.z, EULER_ORDER)));
      }
      built.root.updateMatrixWorld(true);
      built.skeleton.update();
    };
    const now = buildSkinnedRig(canonicalSkeleton);
    const then = buildSkinnedRig(legacy);
    const count = now.mesh.geometry.getAttribute('position').count;
    const here = new Vector3();
    const there = new Vector3();
    let worst = 0;
    for (const exercise of EXERCISES) {
      const evaluation = new PoseEvaluation(canonicalSkeleton);
      const clip = generateClip(canonicalSkeleton, exercise);
      const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
      for (const fraction of [0, 0.25, 0.5, 0.75]) {
        const frame = resolveFrame(canonicalSkeleton, evaluation, clip, clip.duration * fraction, { anchors });
        pose(canonicalSkeleton, now, frame.pose.rotations);
        pose(legacy, then, frame.pose.rotations);
        for (let vertex = 0; vertex < count; vertex += 1) {
          now.mesh.applyBoneTransform(vertex, here.fromBufferAttribute(now.mesh.geometry.getAttribute('position'), vertex));
          then.mesh.applyBoneTransform(vertex, there.fromBufferAttribute(then.mesh.geometry.getAttribute('position'), vertex));
          worst = Math.max(worst, here.distanceTo(there));
        }
      }
    }
    expect(worst).toBeLessThan(1e-12);
  }, 60_000);
});
