import type { BoneName } from '../rig/boneNames';
import type { SceneFrameSnapshot } from './sceneFrameSnapshot';

export interface SceneMatrixObject {
  readonly parent: unknown;
  readonly matrix: { fromArray(elements: number[]): unknown };
  matrixAutoUpdate: boolean;
  matrixWorldNeedsUpdate: boolean;
}

/** A temporary flat scene adapter; matrices in a snapshot are world-space. */
export interface SceneFrameTargets {
  readonly root: unknown;
  readonly bones: ReadonlyMap<BoneName, SceneMatrixObject>;
  readonly equipment: ReadonlyMap<string, SceneMatrixObject>;
}

export function applySceneFrameObjects(snapshot: SceneFrameSnapshot, targets: SceneFrameTargets): void {
  const assignments: Array<{ object: SceneMatrixObject; matrix: number[] }> = [];
  const append = (kind: string, id: string, matrix: number[], object: SceneMatrixObject | undefined) => {
    if (!object) throw new Error(`Missing ${kind} scene object: ${id}`);
    if (object.parent !== targets.root) throw new Error(`${kind} ${id} must be a flat child of the scene root`);
    if (matrix.length !== 16 || matrix.some((value) => !Number.isFinite(value))) {
      throw new Error(`Invalid ${kind} world matrix: ${id}`);
    }
    assignments.push({ object, matrix });
  };
  for (const [name, matrix] of snapshot.bones) append('bone', name, matrix, targets.bones.get(name));
  for (const [id, matrix] of snapshot.equipment) append('equipment', id, matrix, targets.equipment.get(id));

  // Validate the whole frame before changing any object.
  for (const { object, matrix } of assignments) {
    object.matrixAutoUpdate = false;
    object.matrix.fromArray(matrix);
    object.matrixWorldNeedsUpdate = true;
  }
}
