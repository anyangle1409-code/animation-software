import { resolveFrame } from '../animation/pipeline';
import type { StudioClip } from '../animation/clip';
import { measureGripFit } from '../equipment/gripDiagnostics';
import { FINGERS, type Finger, type Side } from '../rig/boneNames';
import { PoseEvaluation, type Skeleton } from '../rig/skeleton';

export interface GripDigitWorstPoint {
  reachUse: number;
  time: number;
}

export interface GripWorstPointSweep {
  instanceId: string;
  side: Side;
  digits: Record<Finger, GripDigitWorstPoint>;
  overall: GripDigitWorstPoint & { finger: Finger };
}

const emptyDigits = (): Record<Finger, GripDigitWorstPoint> => ({
  thumb: { reachUse: -Infinity, time: 0 },
  index: { reachUse: -Infinity, time: 0 },
  middle: { reachUse: -Infinity, time: 0 },
  ring: { reachUse: -Infinity, time: 0 },
  pinky: { reachUse: -Infinity, time: 0 },
});

/**
 * Scan every authored animation frame and retain the worst contact-reach point
 * for each digit on each single-hand equipment instance.
 *
 * This deliberately reuses the production frame pipeline and the established
 * grip envelope. It is an authoring diagnostic only: it never edits the grip,
 * equipment transform, wrist or accepted animation.
 */
export function scanGripWorstCases(
  skeleton: Skeleton,
  clip: StudioClip,
): GripWorstPointSweep[] {
  const handInstances = clip.equipment.filter((instance) => instance.attachment.mode === 'hand');
  if (handInstances.length === 0) return [];

  const sweeps = new Map<string, GripWorstPointSweep>();
  for (const instance of handInstances) {
    if (instance.attachment.mode !== 'hand') continue;
    sweeps.set(instance.id, {
      instanceId: instance.id,
      side: instance.attachment.side,
      digits: emptyDigits(),
      overall: { finger: 'thumb', reachUse: -Infinity, time: 0 },
    });
  }

  const evaluation = new PoseEvaluation(skeleton);
  const fps = clip.fps > 0 ? clip.fps : 30;
  const lastFrame = Math.max(1, Math.ceil(clip.duration * fps));

  for (let frameIndex = 0; frameIndex <= lastFrame; frameIndex += 1) {
    const time = Math.min(clip.duration, frameIndex / fps);
    const frame = resolveFrame(skeleton, evaluation, clip, time);
    evaluation.apply(frame.pose);

    for (const instance of handInstances) {
      if (instance.attachment.mode !== 'hand') continue;
      const transform = frame.equipment.get(instance.id);
      const sweep = sweeps.get(instance.id);
      if (!transform || !sweep) continue;

      const fit = measureGripFit(evaluation, transform, instance.attachment.side);
      for (const finger of FINGERS) {
        const reachUse = fit.digitReachUse[finger];
        if (reachUse > sweep.digits[finger].reachUse) {
          sweep.digits[finger] = { reachUse, time };
        }
        if (reachUse > sweep.overall.reachUse) {
          sweep.overall = { finger, reachUse, time };
        }
      }
    }
  }

  return [...sweeps.values()].filter((sweep) => Number.isFinite(sweep.overall.reachUse));
}
