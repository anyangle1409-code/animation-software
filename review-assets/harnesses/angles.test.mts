import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { Matrix4, Quaternion } from 'three';
import { generateClip } from '../../src/animation/generate';
import { sampleClip } from '../../src/animation/clip';
import { resolveFrame } from '../../src/animation/pipeline';
import { lockAnchors } from '../../src/constraints/locks';
import { bicepCurl } from '../../src/exercises/definitions/bicepCurl';
import { pullUp } from '../../src/exercises/definitions/pullUp';
import { pushUp } from '../../src/exercises/definitions/pushUp';
import { shoulderPress } from '../../src/exercises/definitions/shoulderPress';
import { canonicalSkeleton, PoseEvaluation } from '../../src/rig/skeleton';
import { applyCharacterPose } from '../../src/character/pose';
import { retargetedCharacterSource } from '../../src/character/retargetSource';

/**
 * How far each repaired ring is actually asked to bend, per exercise.
 *
 * A weight repair can only soften a handover; it cannot rescue a joint that is
 * being driven past what the source rig can hold. Measuring the angle first
 * says which of the two we are looking at.
 */
describe('ring joint angles', () => {
  it('reports relative rotation across each handover', async () => {
    const bytes = readFileSync(process.env.GLB!);
    const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const source = retargetedCharacterSource({ id: 'angles', label: 'Angles', data });
    const rig = canonicalSkeleton;
    const character = await source.build(rig);
    const mesh = character.meshes[0];
    const byName = new Map(mesh.skeleton.bones.map((bone) => [bone.name, bone]));

    const pairs: [string, string][] = ['L', 'R'].flatMap((side) => [
      [`DEF-forearm${side}001`, `DEF-hand${side}`] as [string, string],
      [`DEF-hand${side}`, `DEF-f_index01${side}`] as [string, string],
      [`DEF-hand${side}`, `DEF-f_middle01${side}`] as [string, string],
      [`DEF-hand${side}`, `DEF-f_ring01${side}`] as [string, string],
      [`DEF-hand${side}`, `DEF-f_pinky01${side}`] as [string, string],
    ]);

    // Rest orientation of each pair, so the reported angle is the change from
    // bind rather than the authored anatomical offset.
    const restRelative = new Map<string, Quaternion>();
    character.object.updateMatrixWorld(true);
    for (const [parent, child] of pairs) {
      const a = byName.get(parent)!;
      const b = byName.get(child)!;
      const relative = new Matrix4().multiplyMatrices(
        new Matrix4().copy(a.matrixWorld).invert(),
        b.matrixWorld,
      );
      restRelative.set(`${parent}->${child}`, new Quaternion().setFromRotationMatrix(relative));
    }

    for (const definition of [bicepCurl, shoulderPress, pushUp, pullUp]) {
      const clip = generateClip(rig, definition);
      const evaluation = new PoseEvaluation(rig);
      const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
      const worst = new Map<string, number>();
      for (let step = 0; step <= 20; step += 1) {
        const frame = resolveFrame(rig, evaluation, clip, (clip.duration * step) / 20, { anchors });
        applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
        character.object.updateMatrixWorld(true);
        for (const [parent, child] of pairs) {
          const key = `${parent}->${child}`;
          const a = byName.get(parent)!;
          const b = byName.get(child)!;
          const relative = new Matrix4().multiplyMatrices(
            new Matrix4().copy(a.matrixWorld).invert(),
            b.matrixWorld,
          );
          const now = new Quaternion().setFromRotationMatrix(relative);
          const change = now.clone().multiply(restRelative.get(key)!.clone().invert());
          const degrees = (2 * Math.acos(Math.min(1, Math.abs(change.w))) * 180) / Math.PI;
          worst.set(key, Math.max(worst.get(key) ?? 0, degrees));
        }
      }
      console.log(`\n${definition.id}`);
      for (const [key, degrees] of worst) console.log(`  ${key.padEnd(44)} ${degrees.toFixed(1)}°`);
    }
    expect(pairs.length).toBe(10);
    character.dispose();
  });
});
