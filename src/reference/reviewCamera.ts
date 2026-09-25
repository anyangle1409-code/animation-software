import type { BoneName } from '../rig/boneNames';
import type { Vec3 } from '../rig/types';
import type { CameraRecommendation } from '../exercises/types';
import { resolveCamera } from '../viewer/cameras';
import type { ReferenceReviewView } from './types';

export interface DeterministicCameraSetup {
  position: Vec3;
  target: Vec3;
  fov: number;
}

export type ReviewLandmarks = Partial<Record<BoneName, Vec3>>;

const average = (a: Vec3, b: Vec3): Vec3 => ({
  x: (a.x + b.x) / 2,
  y: (a.y + b.y) / 2,
  z: (a.z + b.z) / 2,
});

const add = (a: Vec3, b: Vec3): Vec3 => ({
  x: a.x + b.x,
  y: a.y + b.y,
  z: a.z + b.z,
});

function pair(
  landmarks: ReviewLandmarks,
  left: BoneName,
  right: BoneName,
  label: string,
): Vec3 {
  const a = landmarks[left];
  const b = landmarks[right];
  if (!a || !b) throw new Error(`${label} review camera requires ${left} and ${right} landmarks`);
  return average(a, b);
}

/**
 * Resolve the exact camera for offline/local review evidence.
 *
 * Full-body presets reuse the Studio's existing camera definitions. Semantic
 * close-ups are explicit rather than using the interactive Focus camera, whose
 * target depends on selection and animated interpolation.
 */
export function resolveReviewCamera(
  view: ReferenceReviewView,
  recommendation: CameraRecommendation,
  landmarks: ReviewLandmarks = {},
): DeterministicCameraSetup {
  if (view.target === 'hands') {
    const target = pair(landmarks, 'hand_l', 'hand_r', 'Hands');
    return {
      target,
      position: add(target, { x: 0.7, y: 0.25, z: 0.9 }),
      fov: 32,
    };
  }

  if (view.target === 'shoulders') {
    const target = pair(landmarks, 'upperarm_l', 'upperarm_r', 'Shoulders');
    return {
      target,
      position: add(target, { x: 0.95, y: 0.18, z: 1.05 }),
      fov: 34,
    };
  }

  if (view.target === 'feet') {
    const feet = pair(landmarks, 'foot_l', 'foot_r', 'Feet');
    const knees = pair(landmarks, 'shin_l', 'shin_r', 'Feet');
    const target = average(feet, knees);
    return {
      target,
      position: add(target, { x: 1.05, y: 0.2, z: 1.25 }),
      fov: 36,
    };
  }

  const setup = resolveCamera(view.preset, recommendation);
  if (!setup) {
    throw new Error(`Review view "${view.id}" uses non-deterministic camera preset "${view.preset}"`);
  }
  return {
    position: { x: setup.position.x, y: setup.position.y, z: setup.position.z },
    target: { x: setup.target.x, y: setup.target.y, z: setup.target.z },
    fov: setup.fov,
  };
}
