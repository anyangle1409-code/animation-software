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

/**
 * Resolve the exact camera for offline/local review evidence.
 *
 * Full-body presets reuse the Studio's existing camera definitions. The hands
 * close-up is explicit instead of using the interactive Focus camera, whose
 * target depends on selection and animated interpolation.
 */
export function resolveReviewCamera(
  view: ReferenceReviewView,
  recommendation: CameraRecommendation,
  landmarks: ReviewLandmarks = {},
): DeterministicCameraSetup {
  if (view.target === 'hands') {
    const left = landmarks.hand_l;
    const right = landmarks.hand_r;
    if (!left || !right) {
      throw new Error('Hands review camera requires hand_l and hand_r landmarks');
    }
    const target = average(left, right);
    return {
      target,
      position: {
        x: target.x + 0.7,
        y: target.y + 0.25,
        z: target.z + 0.9,
      },
      fov: 32,
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
