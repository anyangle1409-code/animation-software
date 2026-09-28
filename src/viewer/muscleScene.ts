import { Group, Mesh, MeshStandardMaterial, SphereGeometry } from 'three';
import { MUSCLES } from '../muscles/model';
import { ACTIVATION_STYLES, activationMap, activationOf } from '../muscles/activation';
import { MUSCLE_GROUPS } from '../muscles/groups';

export interface MuscleSceneResources {
  group: Group;
  meshes: ReadonlyMap<string, Mesh<SphereGeometry, MeshStandardMaterial>>;
  dispose(): void;
}

/** Build the muscle overlay as owned Three objects, independent of R3F JSX. */
export function createMuscleScene(
  involvement: Parameters<typeof activationMap>[0],
): MuscleSceneResources {
  const activation = activationMap(involvement);
  const group = new Group();
  group.name = 'hgpt-muscle-view';
  const meshes = new Map<string, Mesh<SphereGeometry, MeshStandardMaterial>>();

  for (const muscle of MUSCLES) {
    const level = activationOf(activation, muscle.group);
    const style = ACTIVATION_STYLES[level];
    const geometry = new SphereGeometry(1, 14, 10);
    const material = new MeshStandardMaterial({
      color: style.colour,
      emissive: style.colour,
      emissiveIntensity: style.emissive,
      transparent: style.opacity < 1,
      opacity: style.opacity,
      roughness: 0.62,
      metalness: 0.03,
    });
    const mesh = new Mesh(geometry, material);
    mesh.name = MUSCLE_GROUPS[muscle.group].label;
    mesh.castShadow = true;
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
      for (const mesh of meshes.values()) {
        mesh.geometry.dispose();
        mesh.material.dispose();
      }
      group.clear();
    },
  };
}
