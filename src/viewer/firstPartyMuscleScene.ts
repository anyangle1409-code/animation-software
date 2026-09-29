import { spherePrimitiveData } from '../core/primitiveGeometry';
import { HgGroup } from '../core/sceneGraph';
import {
  HgPrimitiveMaterial,
  HgPrimitiveMesh,
} from '../core/sceneMesh';
import type { MuscleInvolvement } from '../exercises/types';
import {
  ACTIVATION_STYLES,
  activationMap,
  activationOf,
} from '../muscles/activation';
import { MUSCLE_GROUPS } from '../muscles/groups';
import { MUSCLES } from '../muscles/model';
import type { MuscleFrameTransform } from './muscleFrameSnapshot';

export interface HgMuscleSceneResources {
  readonly group: HgGroup;
  readonly meshes: ReadonlyMap<string, HgPrimitiveMesh>;
  dispose(): void;
}

/** Project-owned muscle overlay scene, parallel to the retained Three adapter. */
export function createHgMuscleScene(
  involvement: MuscleInvolvement,
): HgMuscleSceneResources {
  const activation = activationMap(involvement);
  const group = new HgGroup();
  group.name = 'hgpt-muscle-view';
  const meshes = new Map<string, HgPrimitiveMesh>();

  for (const muscle of MUSCLES) {
    const level = activationOf(activation, muscle.group);
    const style = ACTIVATION_STYLES[level];
    const material = new HgPrimitiveMaterial(
      style.colour,
      'lit',
      {
        emissive: style.colour,
        emissiveIntensity: style.emissive,
        roughness: 0.62,
        metalness: 0.03,
      },
    ).setOpacity(style.opacity);
    const mesh = new HgPrimitiveMesh(
      spherePrimitiveData(1, 14, 10),
      material,
    );
    mesh.name = MUSCLE_GROUPS[muscle.group].label;
    mesh.userData.hgptMuscle = muscle.id;
    group.add(mesh);
    meshes.set(muscle.id, mesh);
  }

  let disposed = false;
  return {
    group,
    meshes,
    dispose() {
      if (disposed) return;
      disposed = true;
      meshes.clear();
      group.clear();
    },
  };
}

export function applyHgMuscleFrame(
  resources: HgMuscleSceneResources,
  snapshot: ReadonlyMap<string, MuscleFrameTransform>,
): void {
  for (const [id, transform] of snapshot) {
    const mesh = resources.meshes.get(id);
    if (!mesh) continue;
    mesh.position.set(...transform.position);
    mesh.quaternion.set(...transform.quaternion);
    mesh.scale.set(...transform.scale);
    mesh.matrixWorldNeedsUpdate = true;
  }
}
