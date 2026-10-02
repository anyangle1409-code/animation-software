import { describe, expect, it } from 'vitest';
import { generateClip } from '../../animation/generate';
import { sampleClip } from '../../animation/clip';
import { HgVec3 } from '../../core/linearMath';
import { canonicalSkeleton, PoseEvaluation } from '../../rig/skeleton';
import { bilateralJoints } from '../mirror';
import { pushUp } from '../definitions/pushUp';

type Endpoint = 'start' | 'peak';

const measure = (
  endpoint: Endpoint,
  footX?: number,
  toeX?: number,
  rootDy = 0,
  rootDz = 0,
) => {
  const source = endpoint === 'start' ? pushUp.startPose : pushUp.peakPose;
  const root = source.root ?? {};
  const position = root.position ?? {};
  const leg = footX === undefined && toeX === undefined
    ? {}
    : bilateralJoints({
        ...(footX === undefined ? {} : { foot_l: { x: footX } }),
        ...(toeX === undefined ? {} : { toe_l: { x: toeX } }),
      });
  const fixed = {
    ...source,
    joints: { ...source.joints, ...leg },
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
  return { head, tail, flatness: Math.abs(tail.y - head.y) };
};

describe('push-up toe geometry diagnostic', () => {
  it('finds the least-invasive foot/toe split that makes the forefoot flat', () => {
    for (const endpoint of ['start', 'peak'] as const) {
      const baseline = measure(endpoint);
      let best: {
        footX: number;
        toeX: number;
        flatness: number;
        dy: number;
        dz: number;
        shift: number;
      } | null = null;

      const consider = (footX: number, toeX: number) => {
        const candidate = measure(endpoint, footX, toeX);
        if (candidate.flatness >= 0.001) return;
        const dy = baseline.tail.y - candidate.tail.y;
        const dz = baseline.tail.z - candidate.tail.z;
        const shift = Math.hypot(dy, dz);
        const record = { footX, toeX, flatness: candidate.flatness, dy, dz, shift };
        if (!best || record.shift < best.shift) best = record;
      };

      // Coarse sweep across the authored joint limits.
      for (let footX = -45; footX <= 35; footX += 2) {
        for (let toeX = -35; toeX <= 80; toeX += 2) consider(footX, toeX);
      }
      expect(best).not.toBeNull();

      // Refine only around the best coarse pair.
      const coarse = best!;
      for (let footX = coarse.footX - 2; footX <= coarse.footX + 2; footX += 0.25) {
        if (footX < -45 || footX > 35) continue;
        for (let toeX = coarse.toeX - 2; toeX <= coarse.toeX + 2; toeX += 0.25) {
          if (toeX < -35 || toeX > 80) continue;
          consider(footX, toeX);
        }
      }

      const adjusted = measure(endpoint, best!.footX, best!.toeX, best!.dy, best!.dz);
      expect(adjusted.flatness).toBeLessThan(0.001);
      console.log(
        `PUSH_UP_FOOT_TOE_DIAGNOSTIC ${endpoint} ${JSON.stringify({
          footX: best!.footX,
          toeX: best!.toeX,
          flatnessMm: adjusted.flatness * 1000,
          rootShiftMm: best!.shift * 1000,
          rootDyMm: best!.dy * 1000,
          rootDzMm: best!.dz * 1000,
          baselineToeHeadYmm: baseline.head.y * 1000,
          baselineToeTipYmm: baseline.tail.y * 1000,
        })}`,
      );
    }
  });
});
