import { describe, expect, it, vi } from 'vitest';
import { PerspectiveCamera, Vector3 } from 'three';
import { restPose } from '../rig/pose';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { StudioCameraRigController } from './cameraRigController';

const recommendation = { preset: 'three_quarter' as const };

function orbit() {
  return {
    target: new Vector3(0, 1, 0),
    update: vi.fn(),
  };
}

describe('R3F-neutral camera rig controller', () => {
  it('moves a camera and orbit target to a configured static preset', () => {
    const controller = new StudioCameraRigController();
    const camera = new PerspectiveCamera(38, 1, 0.05, 100);
    camera.position.set(2.3, 1.35, 2.7);
    const controls = orbit();
    const evaluation = new PoseEvaluation(canonicalSkeleton);
    evaluation.apply(restPose());

    controller.configure('front', recommendation);
    controller.update({
      delta: 1,
      preset: 'front',
      selectedBone: null,
      evaluation,
      camera,
      controls,
    });

    expect(camera.position.toArray()).toEqual([0, 1.05, 3.4]);
    expect(controls.target.toArray()).toEqual([0, 1, 0]);
    expect(camera.fov).toBe(40);
    expect(controls.update).toHaveBeenCalledTimes(1);
  });

  it('focuses a selected joint with the existing side-aware offset and FOV', () => {
    const controller = new StudioCameraRigController();
    const camera = new PerspectiveCamera(38, 1, 0.05, 100);
    camera.position.set(2.3, 1.35, 2.7);
    const controls = orbit();
    const evaluation = new PoseEvaluation(canonicalSkeleton);
    evaluation.apply(restPose());
    const target = evaluation.head('forearm_l', new Vector3()).clone();

    controller.configure('focus', recommendation);
    controller.update({
      delta: 1,
      preset: 'focus',
      selectedBone: 'forearm_l',
      evaluation,
      camera,
      controls,
    });

    expect(controls.target.distanceTo(target)).toBeLessThan(1e-12);
    expect(camera.position.distanceTo(target.clone().add(new Vector3(-0.58, 0.20, 0.78)))).toBeLessThan(1e-12);
    expect(camera.fov).toBe(32);
    expect(controls.update).toHaveBeenCalledTimes(1);
  });

  it('leaves the camera untouched in free mode', () => {
    const controller = new StudioCameraRigController();
    const camera = new PerspectiveCamera(38, 1, 0.05, 100);
    camera.position.set(2.3, 1.35, 2.7);
    const before = camera.position.clone();
    const controls = orbit();
    const evaluation = new PoseEvaluation(canonicalSkeleton);
    evaluation.apply(restPose());

    controller.configure('free', recommendation);
    controller.update({
      delta: 1,
      preset: 'free',
      selectedBone: null,
      evaluation,
      camera,
      controls,
    });

    expect(camera.position.toArray()).toEqual(before.toArray());
    expect(controls.update).not.toHaveBeenCalled();
  });
});
