import {
  boxPrimitiveData,
  octahedronPrimitiveData,
} from '../core/primitiveGeometry';
import { HgGroup } from '../core/sceneGraph';
import {
  HgPrimitiveMaterial,
  HgPrimitiveMesh,
} from '../core/sceneMesh';
import type { IKChainId } from '../ik/types';
import type { HgScenePointerRouter } from './scenePointerRouter';
import {
  buildHgIKHandleSceneModel,
  resolveHgIKHandleAppearance,
} from './ikHandleSceneModel';
import type { IKHandleKind } from './ikHandleScene';

export interface HgIKHandleSceneResources {
  readonly group: HgGroup;
  readonly handles: ReadonlyMap<string, HgPrimitiveMesh>;
  dispose(): void;
}

/** Project-owned interactive IK handle scene. */
export function createHgIKHandleScene(): HgIKHandleSceneResources {
  const group = new HgGroup();
  group.name = 'hgpt-ik-handles';
  const handles = new Map<string, HgPrimitiveMesh>();

  for (const visual of buildHgIKHandleSceneModel()) {
    const geometry = visual.geometry.kind === 'box'
      ? boxPrimitiveData(visual.geometry.size)
      : octahedronPrimitiveData(visual.geometry.radius);
    const material = new HgPrimitiveMaterial(
      visual.material.colour,
      'flat',
      {
        depthTest: visual.material.depthTest,
        depthWrite: false,
      },
    ).setOpacity(visual.material.opacity);
    const mesh = new HgPrimitiveMesh(geometry, material);
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
      handles.clear();
      group.clear();
    },
  };
}

export function updateHgIKHandleSelection(
  resources: HgIKHandleSceneResources,
  selection: { chain: IKChainId; kind: IKHandleKind } | null,
): void {
  for (const visual of buildHgIKHandleSceneModel()) {
    const mesh = resources.handles.get(visual.key);
    if (!mesh) continue;
    const appearance = resolveHgIKHandleAppearance(
      visual.chain,
      visual.kind,
      selection,
    );
    mesh.material
      .setColour(appearance.colour)
      .setEmissive(
        appearance.emissive,
        appearance.emissiveIntensity,
      );
  }
}

export function registerHgIKHandlePointers(
  resources: HgIKHandleSceneResources,
  pointers: Pick<HgScenePointerRouter, 'register'>,
  select: (selection: { chain: IKChainId; kind: IKHandleKind }) => void,
): () => void {
  const remove: Array<() => void> = [];
  for (const visual of buildHgIKHandleSceneModel()) {
    const mesh = resources.handles.get(visual.key);
    if (!mesh) continue;
    remove.push(pointers.register(mesh, {
      pointerdown(event) {
        event.stopPropagation();
        select({ chain: visual.chain, kind: visual.kind });
      },
    }));
  }
  return () => {
    for (const unregister of remove) unregister();
  };
}
