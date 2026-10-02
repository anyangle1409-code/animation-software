import { describe, expect, it } from 'vitest';
import { generateClip } from '../../animation/generate';
import { sampleClip } from '../../animation/clip';
import { HgVec3 } from '../../core/linearMath';
import { canonicalSkeleton, PoseEvaluation } from '../../rig/skeleton';
import { bilateralJoints } from '../mirror';
import { pushUp } from '../definitions/pushUp';

type Endpoint = 'start' | 'peak';

const measure = (endpoint: Endpoint, toeX?: number, rootDy = 0, rootDz = 0) => {
  const source = endpoint === 'start' ? pushUp.startPose : pushUp.peakPose;
  const root = source.root ?? {};
  const position = root.position ?? {};
  const fixed = {
    ...source,
    ...(toeX === undefined
      ? {}
      : { joints: { ...source.joints, ...bilateralJoints({ toe_l: { x: toeX } }) } }),
    root: {
      ...root,
      position: {
        ...position,
        y: (position.y ?? 0) + rootDy,
        z: (position.z ?? 0) + rootDz,
      },
    },
  };
  const exercise = { ...pushUp, startPose: fixed, peakPose: fixed };
  const pose = sampleClip(generateClip(canonicalSkeleton, exercise), 0).pose;
  const evaluation = new PoseEvaluation(canonicalSkeleton);
  evaluation.apply(pose);
  const head = evaluation.head('toe_l', new HgVec3());
  const tail = evaluation.tail('toe_l', new HgVec3());
  return {
    head,
    tail,
    flatness: Math.abs(tail.y - head.y),
  };
};

describe('push-up toe geometry diagnostic', () => {
  it('measures the toe rotation/root compensation that flattens the forefoot', () => {
    for (const endpoint of ['start', 'peak'] as const) {
      const baseline = measure(endpoint);
      let best: { toeX: number; flatness: number; dy: number; dz: number; adjustedFlatness: number } | null = null;

      for (let toeX = -35; toeX <= 80; toeX += 0.5) {
        const candidate = measure(endpoint, toeX);
        const dy = baseline.tail.y - candidate.tail.y;
        const dz = baseline.tail.z - candidate.tail.z;
        const adjusted = measure(endpoint, toeX, dy, dz);
        const record = { toeX, flatness: candidate.flatness, dy, dz, adjustedFlatness: adjusted.flatness };
        if (!best || record.flatness < best.flatness) best = record;
      }

      expect(best).not.toBeNull();
      expect(best!.adjustedFlatness).toBeLessThan(0.001);
      console.log(
        `PUSH_UP_TOE_DIAGNOSTIC ${endpoint} ${JSON.stringify({
          toeX: best!.toeX,
          flatnessMm: best!.adjustedFlatness * 1000,
          rootDyMm: best!.dy * 1000,
          rootDzMm: best!.dz * 1000,
          baselineToeHeadYmm: baseline.head.y * 1000,
          baselineToeTipYmm: baseline.tail.y * 1000,
        })}`,
      );
    }
  });
});
