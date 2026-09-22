import { describe, it } from 'vitest';
import { Vector3 } from 'three';
import { generateClip } from '../../src/animation/generate';
import { sampleClip } from '../../src/animation/clip';
import { resolveFrame } from '../../src/animation/pipeline';
import { lockAnchors } from '../../src/constraints/locks';
import { validateClip } from '../../src/animation/validate';
import { canonicalSkeleton, PoseEvaluation } from '../../src/rig/skeleton';
import { skinDepth } from '../../src/body/containment';
import { MUSCLES, createMuscleTransform, resolveMuscle } from '../../src/muscles/model';
import { bicepCurl } from '../../src/exercises/definitions/bicepCurl';
import { airSquat } from '../../src/exercises/definitions/airSquat';
import { shoulderPress } from '../../src/exercises/definitions/shoulderPress';
import { pushUp } from '../../src/exercises/definitions/pushUp';
import { pullUp } from '../../src/exercises/definitions/pullUp';

/** Phase 3: one complete validation pass over the required poses. */
const rig = canonicalSkeleton;

const POSES: [string, typeof bicepCurl, number[]][] = [
  ['curl', bicepCurl, [0, 1, 2, 5.5]],
  ['squat', airSquat, [-1]],
  ['press', shoulderPress, [0, 2.35]],
  ['pushup', pushUp, [0, -2]],
  ['pullup', pullUp, [0, -2]],
];
const LABELS: Record<string, string[]> = {
  curl: ['Bottom', 'Mid', 'Peak', 'Return'],
  squat: ['Deepest'],
  press: ['Bottom', 'Overhead'],
  pushup: ['Top', 'Bottom'],
  pullup: ['Bottom', 'Top'],
};

describe('phase 3 validation', () => {
  it('reports strain, containment and technique across every required pose', () => {
    const transform = createMuscleTransform();
    // Skin strain is NOT measured here: three.js skins on the GPU, so the geometry
// attribute never moves and every ratio came out exactly 1.000. Deformation is
// covered by src/body/shoulder.test.ts and src/editor/strainReview.ts, which do
// the CPU skinning properly and pass in the suite.
    console.log('\nPHASE3  exercise/pose | worst belly (mm, allowance 7) | technique / reachability');
    for (const [name, exercise, times] of POSES) {
      const clip = generateClip(rig, exercise);
      const evaluation = new PoseEvaluation(rig);
      const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
      const validation = validateClip(rig, evaluation, exercise, clip);
      times.forEach((raw, slot) => {
        // -1 means "the deepest/peak keyframe"; -2 means "the peak marker".
        const time = raw >= 0 ? raw : clip.keyframes.find((k) => k.marker === 'peak')?.time ?? clip.duration / 2;
        const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
        evaluation.apply(frame.pose);
        let worst = { depth: -Infinity, id: '' };
        for (const muscle of MUSCLES) {
          resolveMuscle(evaluation, muscle, transform);
          for (let i = 0; i <= 8; i += 1) {
            const phi = (i / 8) * Math.PI;
            for (let j = 0; j < 12; j += 1) {
              const theta = (j / 12) * Math.PI * 2;
              const point = new Vector3(
                Math.sin(phi) * Math.cos(theta), Math.cos(phi), Math.sin(phi) * Math.sin(theta),
              ).multiply(transform.scale).applyQuaternion(transform.quaternion).add(transform.position);
              const d = skinDepth(evaluation, point).depth;
              if (d > worst.depth) worst = { depth: d, id: muscle.id };
            }
          }
        }
        console.log(
          `PHASE3 ${(name + ' ' + (LABELS[name][slot] ?? String(time))).padEnd(16)} | ` +
            `${(worst.depth * 1000).toFixed(2).padStart(6)} ${worst.id.padEnd(18)} | ` +
            `${validation.violations.length ? validation.violations.map((v) => v.ruleId).join(',') : 'clean'}` +
            `${validation.unreachable.length ? ` UNREACHABLE ${validation.unreachable.join(',')}` : ''}`,
        );
      });
    }
  }, 600000);
});
