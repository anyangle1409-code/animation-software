import { readFileSync } from 'node:fs';
import { describe, it } from 'vitest';
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
 * Forearm girth along its own axis, bind pose against posed.
 *
 * "Flattened strap" is a visual claim; this makes it a number. For every vertex
 * the forearm chain owns, the perpendicular distance from the elbow-to-wrist
 * axis is binned along that axis. A collapse shows up as the posed radius
 * falling below the bind radius in the same bin.
 */
const rig = canonicalSkeleton;
const BINS = 6;

describe('phase 4 forearm girth', () => {
  it('compares posed forearm girth with the bind pose', async () => {
    const bytes = readFileSync(process.env.GLB!);
    const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const character = await retargetedCharacterSource({ id: 'g', label: 'G', data }).build(rig);
    const mesh = character.meshes[0];
    const joints = mesh.geometry.getAttribute('skinIndex');
    const weights = mesh.geometry.getAttribute('skinWeight');
    const count = mesh.geometry.getAttribute('position').count;
    const owned: number[] = [];
    for (let v = 0; v < count; v += 1) {
      let held = 0;
      for (let lane = 0; lane < 4; lane += 1) {
        const w = weights.getComponent(v, lane);
        if (w <= 0) continue;
        const raw = mesh.skeleton.bones[joints.getComponent(v, lane)]?.name ?? '';
        if (/^DEF-forearmL/i.test(raw)) held += w;
      }
      if (held > 0.6) owned.push(v);
    }

    const profile = (label: string) => {
      const elbow = mesh.skeleton.bones.find((b) => b.name === 'DEF-forearmL')!;
      const wrist = mesh.skeleton.bones.find((b) => b.name === 'DEF-handL')!;
      mesh.skeleton.update();
      mesh.updateWorldMatrix(true, false);
      const a = new Vector3().setFromMatrixPosition(elbow.matrixWorld);
      const b = new Vector3().setFromMatrixPosition(wrist.matrixWorld);
      const axis = new Vector3().subVectors(b, a);
      const length = axis.length();
      axis.normalize();
      const sums = new Array(BINS).fill(0);
      const counts = new Array(BINS).fill(0);
      const scratch = new Vector3();
      for (const v of owned) {
        mesh.getVertexPosition(v, scratch);
        const p = scratch.clone().applyMatrix4(mesh.matrixWorld).sub(a);
        const t = p.dot(axis) / length;
        if (t < 0 || t >= 1) continue;
        const radial = p.clone().sub(axis.clone().multiplyScalar(p.dot(axis))).length();
        const bin = Math.min(BINS - 1, Math.floor(t * BINS));
        sums[bin] += radial;
        counts[bin] += 1;
      }
      const mean = sums.map((s, i) => (counts[i] ? (s / counts[i]) * 1000 : NaN));
      console.log(`GIRTH ${label.padEnd(12)} ${mean.map((m) => (Number.isNaN(m) ? '  --' : m.toFixed(1).padStart(5))).join(' ')} mm  (${owned.length} vertices)`);
      return mean;
    };

    profile('bind');
    const clip = generateClip(rig, pushUp);
    const evaluation = new PoseEvaluation(rig);
    const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
    const bottom = clip.keyframes.find((k) => k.marker === 'peak')?.time ?? clip.duration / 2;
    for (const [label, time] of [['posed Top', 0], ['posed Bottom', bottom]] as [string, number][]) {
      const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
      evaluation.apply(frame.pose);
      applyCharacterPose(character, rig, frame.pose, evaluation, {
        contacts: frame.contacts,
        grip: { kind: pushUp.hands.grip, closure: pushUp.hands.closure },
      });
      profile(label);
    }
  }, 300000);
});
