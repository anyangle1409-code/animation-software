import {
  BoxGeometry,
  Group,
  Mesh,
  MeshStandardMaterial,
  OctahedronGeometry,
} from './threeSceneBoundary';
import { IK_CHAIN_IDS } from '../ik/chains';
import type { IKChainId } from '../ik/types';
import type { HgScenePointerRouter } from './scenePointerRouter';

export type IKHandleKind = 'target' | 'pole';

const TARGET_COLOUR = '#4fd6a0';
const POLE_COLOUR = '#6aa9ff';
const SELECTED_COLOUR = '#ffb43a';

export interface IKHandleSceneResources {
  group: Group;
  handles: ReadonlyMap<string, Mesh>;
  dispose(): void;
}

const keyOf = (chain: IKChainId, kind: IKHandleKind) => `${chain}:${kind}`;

export function createIKHandleScene(): IKHandleSceneResources {
  const group = new Group();
  group.name = 'hgpt-ik-handles';

  const targetGeometry = new BoxGeometry(0.045, 0.045, 0.045);
  const poleGeometry = new OctahedronGeometry(0.032);
  const handles = new Map<string, Mesh>();
  const materials: MeshStandardMaterial[] = [];

  for (const chain of IK_CHAIN_IDS) {
    for (const kind of ['target', 'pole'] as const) {
      const colour = kind === 'target' ? TARGET_COLOUR : POLE_COLOUR;
      const material = new MeshStandardMaterial({
        color: colour,
        emissive: '#000000',
        emissiveIntensity: 0,
        transparent: true,
        opacity: 0.9,
        depthTest: false,
      });
      materials.push(material);

      const mesh = new Mesh(kind === 'target' ? targetGeometry : poleGeometry, material);
      mesh.name = `hgpt-ik-${chain}-${kind}`;
      mesh.visible = false;
      group.add(mesh);
      handles.set(keyOf(chain, kind), mesh);
    }
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
  for (const chain of IK_CHAIN_IDS) {
    for (const kind of ['target', 'pole'] as const) {
      const mesh = resources.handles.get(keyOf(chain, kind));
      if (!mesh) continue;
      const material = mesh.material as MeshStandardMaterial;
      const selected = selection?.chain === chain && selection.kind === kind;
      const colour = selected
        ? SELECTED_COLOUR
        : kind === 'target'
          ? TARGET_COLOUR
          : POLE_COLOUR;
      material.color.set(colour);
      material.emissive.set(selected ? SELECTED_COLOUR : '#000000');
      material.emissiveIntensity = selected ? 0.5 : 0;
    }
  }
}

export function registerIKHandlePointers(
  resources: IKHandleSceneResources,
  pointers: Pick<HgScenePointerRouter, 'register'>,
  select: (selection: { chain: IKChainId; kind: IKHandleKind }) => void,
): () => void {
  const remove: Array<() => void> = [];
  for (const chain of IK_CHAIN_IDS) {
    for (const kind of ['target', 'pole'] as const) {
      const mesh = resources.handles.get(keyOf(chain, kind));
      if (!mesh) continue;
      remove.push(
        pointers.register(mesh, {
          pointerdown: (event) => {
            event.stopPropagation();
            select({ chain, kind });
          },
        }),
      );
    }
  }
  return () => {
    for (const unregister of remove) unregister();
  };
}
