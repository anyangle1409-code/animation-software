import { HgVec3 } from '../core/linearMath';
import type { Vec3 } from '../rig/types';
import type { CameraRecommendation } from '../exercises/types';
import type { BoneName } from '../rig/boneNames';
import type { PoseEvaluation } from '../rig/skeleton';
import type { CameraPresetId } from './cameraTypes';
import { resolveCamera } from './cameras';

export interface CameraVectorPort {
  x: number;
  y: number;
  z: number;
}

export interface CameraOrbitPort {
  target: CameraVectorPort;
  update(): void;
}

export interface CameraPort {
  position: CameraVectorPort;
  fov?: number;
  updateProjectionMatrix?(): void;
}

interface CameraGoal {
  position: HgVec3;
  target: HgVec3;
  fov: number;
}

export interface CameraRigStep {
  delta: number;
  preset: CameraPresetId;
  selectedBone: BoneName | null;
  evaluation: PoseEvaluation;
  camera: CameraPort;
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
  private readonly focusTarget = new HgVec3();
  private readonly focusPosition = new HgVec3();
  private readonly focusOffset = new HgVec3();

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

    if (preset === 'focus' && selectedBone) {
      evaluation.firstPartyEvaluation.head(selectedBone, this.focusTarget);
      const side = selectedBone.endsWith('_l') ? -1 : selectedBone.endsWith('_r') ? 1 : 1;
      this.focusOffset.set(side * 0.58, 0.20, 0.78);
      this.focusPosition.copy(this.focusTarget).add(this.focusOffset);
      const blend = Math.min(1, Math.max(0, delta) * 7);
      lerpVector(camera.position, this.focusPosition, blend);
      lerpVector(controls.target, this.focusTarget, blend);
      if (typeof camera.fov === 'number') {
        camera.fov += (32 - camera.fov) * blend;
        camera.updateProjectionMatrix?.();
      }
      controls.update();
      return;
    }

    const destination = this.goal;
    if (!destination) return;

    const blend = Math.min(1, Math.max(0, delta) * 6);
    lerpVector(camera.position, destination.position, blend);
    lerpVector(controls.target, destination.target, blend);
    if (typeof camera.fov === 'number') {
      camera.fov += (destination.fov - camera.fov) * blend;
      camera.updateProjectionMatrix?.();
    }
    controls.update();

    if (distance(camera.position, destination.position) < 0.01) this.goal = null;
  }
}


function lerpVector(target: CameraVectorPort, destination: Vec3, t: number): void {
  target.x += (destination.x - target.x) * t;
  target.y += (destination.y - target.y) * t;
  target.z += (destination.z - target.z) * t;
}

function distance(a: CameraVectorPort, b: Vec3): number {
  return Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z);
}
