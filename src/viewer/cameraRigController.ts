import { Vector3 } from 'three';
import type { Camera } from 'three';
import type { CameraRecommendation } from '../exercises/types';
import type { BoneName } from '../rig/boneNames';
import type { PoseEvaluation } from '../rig/skeleton';
import type { CameraPresetId } from './cameraTypes';
import { resolveCamera } from './cameras';

export interface CameraOrbitPort {
  target: Vector3;
  update(): void;
}

interface CameraGoal {
  position: Vector3;
  target: Vector3;
  fov: number;
}

export interface CameraRigStep {
  delta: number;
  preset: CameraPresetId;
  selectedBone: BoneName | null;
  evaluation: PoseEvaluation;
  camera: Camera;
  controls: CameraOrbitPort | null;
}

/**
 * R3F-neutral camera preset/focus controller.
 *
 * The temporary host still injects its camera and orbit handle, but all camera
 * interpolation and focus-selected behavior lives here so a first-party host
 * can reuse it unchanged.
 */
export class StudioCameraRigController {
  private goal: CameraGoal | null = null;
  private readonly focusTarget = new Vector3();
  private readonly focusPosition = new Vector3();
  private readonly focusOffset = new Vector3();

  configure(preset: CameraPresetId, recommendation: CameraRecommendation): void {
    const setup = resolveCamera(preset, recommendation);
    this.goal = setup
      ? { position: setup.position.clone(), target: setup.target.clone(), fov: setup.fov }
      : null;
  }

  update({
    delta,
    preset,
    selectedBone,
    evaluation,
    camera,
    controls,
  }: CameraRigStep): void {
    if (!controls) return;

    const lens = camera as Camera & {
      fov?: number;
      updateProjectionMatrix?: () => void;
    };

    if (preset === 'focus' && selectedBone) {
      evaluation.head(selectedBone, this.focusTarget);
      const side = selectedBone.endsWith('_l') ? -1 : selectedBone.endsWith('_r') ? 1 : 1;
      this.focusOffset.set(side * 0.58, 0.20, 0.78);
      this.focusPosition.copy(this.focusTarget).add(this.focusOffset);
      const blend = Math.min(1, Math.max(0, delta) * 7);
      camera.position.lerp(this.focusPosition, blend);
      controls.target.lerp(this.focusTarget, blend);
      if (typeof lens.fov === 'number') {
        lens.fov += (32 - lens.fov) * blend;
        lens.updateProjectionMatrix?.();
      }
      controls.update();
      return;
    }

    const destination = this.goal;
    if (!destination) return;

    const blend = Math.min(1, Math.max(0, delta) * 6);
    camera.position.lerp(destination.position, blend);
    controls.target.lerp(destination.target, blend);
    if (typeof lens.fov === 'number') {
      lens.fov += (destination.fov - lens.fov) * blend;
      lens.updateProjectionMatrix?.();
    }
    controls.update();

    if (camera.position.distanceTo(destination.position) < 0.01) this.goal = null;
  }
}
