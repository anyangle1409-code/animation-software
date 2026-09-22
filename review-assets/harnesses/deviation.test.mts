import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { generateClip } from '../../src/animation/generate';
import { sampleClip } from '../../src/animation/clip';
import { resolveFrame } from '../../src/animation/pipeline';
import { lockAnchors } from '../../src/constraints/locks';
import { pullUp } from '../../src/exercises/definitions/pullUp';
import { pushUp } from '../../src/exercises/definitions/pushUp';
import { canonicalSkeleton, PoseEvaluation } from '../../src/rig/skeleton';
import { applyCharacterPose } from '../../src/character/pose';
import { retargetedCharacterSource } from '../../src/character/retargetSource';

/**
 * Which way the wrist deviates, named rather than signed.
 *
 * Radial deviation tips the hand toward the thumb, ulnar deviation toward the
 * little finger, so the direction is read straight off the metacarpals instead
 * of from the sign of a quaternion component.
 */

const rig = canonicalSkeleton;
const DEG = 180 / Math.PI;

describe('wrist deviation direction', () => {
  it('names radial or ulnar from the hand itself', async () => {
    const bytes = readFileSync(process.env.GLB!);
    const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const source = retargetedCharacterSource({ id: 'dev', label: 'Deviation', data });
    const character = await source.build(rig);
    const mesh = character.meshes[0];
    const head = (name: string) => {
      const bone = mesh.skeleton.bones.find((each) => each.name === name)!;
      return new Vector3().setFromMatrixPosition(bone.matrixWorld);
    };

    for (const definition of [pushUp, pullUp]) {
      const clip = generateClip(rig, definition);
      const evaluation = new PoseEvaluation(rig);
      const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
      console.log(`\n${definition.id} — deviation of the hand from the forearm axis`);

      for (let step = 0; step <= 8; step += 1) {
        const time = (clip.duration * step) / 8;
        const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
        applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
        character.object.updateMatrixWorld(true);

        const report: string[] = [];
        for (const side of ['L', 'R'] as const) {
          const forearm = new Vector3()
            .subVectors(head(`DEF-hand${side}`), head(`DEF-forearm${side}`))
            .normalize();
          const hand = new Vector3()
            .subVectors(head(`DEF-f_middle01${side}`), head(`DEF-hand${side}`))
            .normalize();
          const towardPinky = new Vector3()
            .subVectors(head(`DEF-f_pinky01${side}`), head(`DEF-f_index01${side}`))
            .normalize();
          // Split the forearm axis out of both, so what is left is sideways.
          const sideways = towardPinky.clone().addScaledVector(forearm, -towardPinky.dot(forearm)).normalize();
          const handSideways = hand.clone().addScaledVector(forearm, -hand.dot(forearm));
          const amount = Math.atan2(handSideways.length(), hand.dot(forearm)) * DEG;
          const along = handSideways.lengthSq() < 1e-12 ? 0 : handSideways.clone().normalize().dot(sideways);
          const ulnar = amount * along;
          report.push(
            `${side}: ${Math.abs(ulnar).toFixed(1).padStart(5)}° ${ulnar >= 0 ? 'ulnar ' : 'radial'}`,
          );
        }
        console.log(`  t=${time.toFixed(2)}s  ${report.join('   ')}`);
      }
    }

    expect(true).toBe(true);
    character.dispose();
  });
});
