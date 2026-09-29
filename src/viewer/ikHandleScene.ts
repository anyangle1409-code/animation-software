import {
  BoxGeometry,
  Group,
  Mesh,
  MeshStandardMaterial,
  OctahedronGeometry,
} from './threeSceneBoundary';
import type { IKChainId } from '../ik/types';
import type { HgScenePointerRouter } from './scenePointerRouter';
import {
  buildHgIKHandleSceneModel,
  resolveHgIKHandleAppearance,
} from './ikHandleSceneModel';

export type IKHandleKind = 'target' | 'pole';

export interface IKHandleSceneResources {
  group: Group;
  handles: ReadonlyMap<string, Mesh>;
  dispose(): void;
}

export function createIKHandleScene(): IKHandleSceneResources {
  const group = new Group();
  group.name = 'hgpt-ik-handles';

  const targetGeometry = new BoxGeometry(0.045, 0.045, 0.045);
  const poleGeometry = new OctahedronGeometry(0.032);
  const handles = new Map<string, Mesh>();
  const materials: MeshStandardMaterial[] = [];

  for (const visual of buildHgIKHandleSceneModel()) {
    const material = new MeshStandardMaterial({
      color: visual.material.colour,
      emissive: '#000000',
      emissiveIntensity: 0,
      transparent: visual.material.transparent,
      opacity: visual.material.opacity,
      depthTest: visual.material.depthTest,
    });
    materials.push(material);

    const mesh = new Mesh(
      visual.geometry.kind === 'box' ? targetGeometry : poleGeometry,
      material,
    );
    mesh.name = `hgpt-ik-${visual.chain}-${visual.kind}`;
    mesh.visible = false;
    group.add(mesh);
    handles.set(visual.key, mesh);
  }

  let disposed = false;
  return {
    group,
    handles,
    dispose() {
      if (disposed) return;
      disposed = true;
      targetGeometry.dispose();
      poleGeometry.dispose();
      for (const material of materials) material.dispose();
      group.clear();
    },
  };
}

export function updateIKHandleSelection(
  resources: IKHandleSceneResources,
  selection: { chain: IKChainId; kind: IKHandleKind } | null,
): void {
  for (const visual of buildHgIKHandleSceneModel()) {
    const mesh = resources.handles.get(visual.key);
    if (!mesh) continue;
    const material = mesh.material as MeshStandardMaterial;
    const appearance = resolveHgIKHandleAppearance(
      visual.chain,
      visual.kind,
      selection,
    );
    material.color.set(appearance.colour);
    material.emissive.set(appearance.emissive);
    material.emissiveIntensity = appearance.emissiveIntensity;
  }
}

export function registerIKHandlePointers(
  resources: IKHandleSceneResources,
  pointers: Pick<HgScenePointerRouter, 'register'>,
  select: (selection: { chain: IKChainId; kind: IKHandleKind }) => void,
): () => void {
  const remove: Array<() => void> = [];
  for (const visual of buildHgIKHandleSceneModel()) {
    const mesh = resources.handles.get(visual.key);
    if (!mesh) continue;
    remove.push(
      pointers.register(mesh, {
        pointerdown: (event) => {
          event.stopPropagation();
          select({ chain: visual.chain, kind: visual.kind });
        },
      }),
    );
  }
  return () => {
    for (const unregister of remove) unregister();
  };
}
