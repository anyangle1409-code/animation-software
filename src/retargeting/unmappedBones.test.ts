import { existsSync, readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { Matrix4, Vector3 } from 'three';
import type { SkinnedMesh } from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { skeletonWithoutScapula } from '../rig/withoutScapula';
import { generateClip } from '../animation/generate';
import { resolveFrame } from '../animation/pipeline';
import { lockAnchors } from '../constraints/locks';
import { sampleClip } from '../animation/clip';
import { applyCharacterPose } from '../character/pose';
import { retargetedCharacterSource } from '../character/retargetSource';
import { posedVertex } from '../character/posedMesh';
import { EXERCISES } from '../exercises/library';
import { createMapping, guessMapping } from './boneMap';
import { bindRetarget, readCharacter } from './retarget';

/**
 * The canonical rig carries bones no imported character has — the scapulae —
 * and the production character's deform hierarchy is flattened, so its
 * clavicles and upper arms hang from the armature root. Together those are the
 * case that broke: a retargeter that looked only at a bone's direct canonical
 * parent and children turned the clavicles 6.75° and left both upper arms
 * unattached. Here the production character is held, bone for bone and vertex
 * for vertex, to what the 53-bone rig made of it.
 */
const ASSET =
  process.env.REAL_CHARACTER_GLB ?? 'review-assets/characters/HomeGymPT_Male_CORNER_FINAL_SHORTS.glb';
const legacy = skeletonWithoutScapula();
/** Rounding: the extra bone changes the last bits of the arm chain, no more. */
const NUMERIC = 1e-9;

const load = () => {
  const bytes = readFileSync(ASSET);
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
};

describe.skipIf(!existsSync(ASSET))('retargeting through bones the character does not have', () => {
  it('binds the production character exactly as the 53-bone rig did', async () => {
    const scene = (await new GLTFLoader().parseAsync(load(), '')).scene;
    scene.updateMatrixWorld(true);
    const character = readCharacter(scene);
    const mapping = createMapping('production', 'production');
    mapping.bones = guessMapping(character.boneNames);
    expect(mapping.bones.scapula_l).toBeUndefined();

    const now = bindRetarget(character, mapping, canonicalSkeleton);
    const then = bindRetarget(character, mapping, legacy);
    expect(now.bones.map((entry) => entry.canonical)).toEqual(then.bones.map((entry) => entry.canonical));
    for (const [index, entry] of now.bones.entries()) {
      // The clavicle's shaft still runs to the upper arm, through the
      // unmapped scapula; the 6.75° this once was is far outside rounding.
      // Compared component by component: the character's glTF rotations are
      // float32 and not exactly unit length, so a dot product would report
      // their norm, not a difference.
      const was = then.bones[index].correction;
      const difference = Math.max(
        Math.abs(entry.correction.x - was.x),
        Math.abs(entry.correction.y - was.y),
        Math.abs(entry.correction.z - was.z),
        Math.abs(entry.correction.w - was.w),
      );
      expect(difference, entry.canonical).toBeLessThan(NUMERIC);
    }
    const attachments = (binding: typeof now) =>
      [...binding.attachments].map(([bone, attachment]) => `${bone.name}→${attachment.parent.name}`).sort();
    expect(attachments(now)).toEqual(attachments(then));
    // Named outright, because this is the pair that came loose.
    expect(attachments(now)).toContain('DEF-upper_armL→DEF-shoulderL');
    expect(attachments(now)).toContain('DEF-upper_armR→DEF-shoulderR');
  });

  it('drives every bone, grip and vertex as before through all seven exercises', async () => {
    const data = load();
    const now = await retargetedCharacterSource({ id: ASSET, label: ASSET, data: data.slice(0) }).build(canonicalSkeleton);
    const then = await retargetedCharacterSource({ id: ASSET, label: ASSET, data: data.slice(0) }).build(legacy);
    const bodyNow = (now.meshes as SkinnedMesh[]).find((mesh) => /freeman/i.test(mesh.name))!;
    const bodyThen = (then.meshes as SkinnedMesh[]).find((mesh) => /freeman/i.test(mesh.name))!;
    const vertices = bodyNow.geometry.getAttribute('position').count;
    const here = new Vector3();
    const there = new Vector3();

    for (const exercise of EXERCISES) {
      const a = { evaluation: new PoseEvaluation(canonicalSkeleton), clip: generateClip(canonicalSkeleton, exercise) };
      const b = { evaluation: new PoseEvaluation(legacy), clip: generateClip(legacy, exercise) };
      const anchorsA = lockAnchors(a.evaluation, sampleClip(a.clip, 0).pose, a.clip.locks);
      const anchorsB = lockAnchors(b.evaluation, sampleClip(b.clip, 0).pose, b.clip.locks);
      let worstBone = 0;
      let worstGrip = 0;
      let worstVertex = 0;

      for (let step = 0; step <= 20; step += 1) {
        const time = (step / 20) * a.clip.duration;
        const frameA = resolveFrame(canonicalSkeleton, a.evaluation, a.clip, time, { anchors: anchorsA });
        const frameB = resolveFrame(legacy, b.evaluation, b.clip, time, { anchors: anchorsB });
        applyCharacterPose(now, canonicalSkeleton, frameA.pose, a.evaluation, { contacts: frameA.contacts });
        applyCharacterPose(then, legacy, frameB.pose, b.evaluation, { contacts: frameB.contacts });
        bodyNow.skeleton.update();
        bodyThen.skeleton.update();

        bodyNow.skeleton.bones.forEach((bone, index) => {
          const x = bone.matrixWorld.elements;
          const y = bodyThen.skeleton.bones[index].matrixWorld.elements;
          for (let k = 0; k < 16; k += 1) worstBone = Math.max(worstBone, Math.abs(x[k] - y[k]));
        });
        for (const side of ['l', 'r'] as const) {
          const x = now.handMatrix!(side, new Matrix4())!.elements;
          const y = then.handMatrix!(side, new Matrix4())!.elements;
          for (let k = 0; k < 16; k += 1) worstGrip = Math.max(worstGrip, Math.abs(x[k] - y[k]));
        }
        if (step % 5 === 0) {
          for (let vertex = 0; vertex < vertices; vertex += 1) {
            posedVertex(bodyNow, vertex, here);
            posedVertex(bodyThen, vertex, there);
            worstVertex = Math.max(worstVertex, here.distanceTo(there));
          }
        }
      }
      expect(worstBone, `${exercise.id} character bones`).toBeLessThan(NUMERIC);
      expect(worstGrip, `${exercise.id} hand/grip frames`).toBeLessThan(NUMERIC);
      expect(worstVertex, `${exercise.id} posed surface`).toBeLessThan(NUMERIC);
    }
    now.dispose?.();
    then.dispose?.();
  }, 120_000);
});
