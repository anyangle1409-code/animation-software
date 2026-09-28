import type { PoseEvaluation } from '../rig/skeleton';
import {
  MUSCLES,
  createMuscleTransform,
  resolveMuscle,
} from '../muscles/model';
import type { MuscleInstance } from '../muscles/model';

export interface MuscleFrameTransform {
  readonly position: [number, number, number];
  readonly quaternion: [number, number, number, number];
  readonly scale: [number, number, number];
  readonly stretch: number;
}

/**
 * Copy the resolved muscle-overlay frame into renderer-neutral numeric data.
 * The current muscle solver still uses Three internally; this boundary keeps
 * those objects from becoming part of the future scene-consumer contract.
 */
export function captureMuscleFrame(
  evaluation: PoseEvaluation,
  muscles: readonly MuscleInstance[] = MUSCLES,
): Map<string, MuscleFrameTransform> {
  const out = new Map<string, MuscleFrameTransform>();
  const scratch = createMuscleTransform();

  for (const muscle of muscles) {
    resolveMuscle(evaluation, muscle, scratch);
    out.set(muscle.id, {
      position: [scratch.position.x, scratch.position.y, scratch.position.z],
      quaternion: [
        scratch.quaternion.x,
        scratch.quaternion.y,
        scratch.quaternion.z,
        scratch.quaternion.w,
      ],
      scale: [scratch.scale.x, scratch.scale.y, scratch.scale.z],
      stretch: scratch.stretch,
    });
  }

  return out;
}
