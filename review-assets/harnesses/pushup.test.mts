import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { generateClip } from '../../src/animation/generate';
import { sampleClip } from '../../src/animation/clip';
import { resolveFrame } from '../../src/animation/pipeline';
import { lockAnchors } from '../../src/constraints/locks';
import { pushUp } from '../../src/exercises/definitions/pushUp';
import { canonicalSkeleton, PoseEvaluation } from '../../src/rig/skeleton';
import { applyCharacterPose } from '../../src/character/pose';
import { retargetedCharacterSource } from '../../src/character/retargetSource';

/**
 * Where the push-up's wrist angle comes from.
 *
 * If the hand is flat on the floor, the wrist angle is whatever the forearm's
 * lean makes it: a vertical forearm gives about 90°, and every degree the
 * shoulder travels forward of the hand adds a degree of extension. So the
 * question is not "is the wrist bent" but "where is the shoulder relative to
 * the hand".
 */

const rig = canonicalSkeleton;
const DEG = 180 / Math.PI;

describe('push-up wrist geometry', () => {
  it('reports forearm lean and hand plane through the rep', async () => {
    const bytes = readFileSync(process.env.GLB!);
    const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const source = retargetedCharacterSource({ id: 'pushup', label: 'Push-up', data });
    const character = await source.build(rig);
    const mesh = character.meshes[0];
    const head = (name: string) => {
      const bone = mesh.skeleton.bones.find((each) => each.name === name)!;
      return new Vector3().setFromMatrixPosition(bone.matrixWorld);
    };

    const clip = generateClip(rig, pushUp);
    const evaluation = new PoseEvaluation(rig);
    const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
    const up = new Vector3(0, 1, 0);

    console.log('\nPUSH-UP WRIST GEOMETRY (left side)');
    console.log(
      '   time   forearm tilt   hand tilt   wrist angle   hand height   shoulder ahead of hand',
    );
    for (let step = 0; step <= 8; step += 1) {
      const time = (clip.duration * step) / 8;
      const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
      applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
      character.object.updateMatrixWorld(true);

      const elbow = head('DEF-forearmL');
      const wrist = head('DEF-handL');
      const knuckle = head('DEF-f_middle01L');
      const shoulder = head('DEF-upper_armL');

      const forearm = new Vector3().subVectors(wrist, elbow).normalize();
      const hand = new Vector3().subVectors(knuckle, wrist).normalize();
      // Tilt from the floor plane: 90° is vertical, 0° is flat.
      const forearmTilt = Math.asin(Math.abs(forearm.dot(up))) * DEG;
      const handTilt = Math.asin(Math.abs(hand.dot(up))) * DEG;
      const wristAngle = Math.acos(Math.min(1, Math.max(-1, forearm.dot(hand)))) * DEG;
      // Horizontal distance from the hand to the shoulder, in millimetres.
      const ahead = Math.hypot(shoulder.x - wrist.x, shoulder.z - wrist.z) * 1000;

      console.log(
        `  ${time.toFixed(2)}s   ${forearmTilt.toFixed(1).padStart(8)}°   ${handTilt.toFixed(1).padStart(7)}°   ` +
          `${wristAngle.toFixed(1).padStart(8)}°   ${(wrist.y * 1000).toFixed(1).padStart(8)} mm   ${ahead.toFixed(1).padStart(10)} mm`,
      );
    }

    expect(true).toBe(true);
    character.dispose();
  });
});
