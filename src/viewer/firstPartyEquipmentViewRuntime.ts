import type { EquipmentInstance } from '../equipment/types';
import type { HgObject3D } from '../core/sceneGraph';
import type { SceneState } from './sceneStateCore';
import { SCENE_FRAME_PRIORITY } from './sceneStateCore';
import {
  applyHgEquipmentDisplayTransforms,
  createHgEquipmentScene,
  registerHgEquipmentPointers,
  type HgEquipmentSceneResources,
} from './firstPartyEquipmentScene';
import {
  resolveEquipmentDisplayTransforms,
  type EquipmentDisplayCharacter,
} from './equipmentDisplayTransforms';
import type { HgScenePointerRouter } from './scenePointerRouter';

export interface FirstPartyEquipmentViewStudioState {
  document: { clip: { equipment: EquipmentInstance[] } };
  selectEquipment(id: string | null): void;
}
export interface FirstPartyEquipmentViewStorePort {
  getState(): FirstPartyEquipmentViewStudioState;
  subscribe(listener: () => void): () => void;
}
export interface FirstPartyEquipmentViewCharacterPort {
  getState(): { active: EquipmentDisplayCharacter | null };
}
export interface FirstPartyEquipmentViewRuntime {
  readonly resources: HgEquipmentSceneResources;
  dispose(): void;
}

export function createFirstPartyEquipmentViewRuntime(options: {
  sceneState: SceneState;
  root: Pick<HgObject3D, 'add' | 'remove'>;
  pointers: Pick<HgScenePointerRouter, 'register'>;
  store: FirstPartyEquipmentViewStorePort;
  characterStore: FirstPartyEquipmentViewCharacterPort;
}): FirstPartyEquipmentViewRuntime {
  const { sceneState, root, pointers, store, characterStore } = options;
  let activeInstances = store.getState().document.clip.equipment;
  let resources = createHgEquipmentScene(activeInstances);
  let removePointers = registerHgEquipmentPointers(
    resources, pointers, (id) => store.getState().selectEquipment(id),
  );
  root.add(resources.group);

  const rebuild = (instances: EquipmentInstance[]) => {
    removePointers();
    root.remove(resources.group);
    resources.dispose();
    activeInstances = instances;
    resources = createHgEquipmentScene(activeInstances);
    removePointers = registerHgEquipmentPointers(
      resources, pointers, (id) => store.getState().selectEquipment(id),
    );
    root.add(resources.group);
  };
  const unsubscribeStore = store.subscribe(() => {
    const next = store.getState().document.clip.equipment;
    if (next !== activeInstances) rebuild(next);
  });
  const removeFrame = sceneState.consumers.add(() => {
    const transforms = sceneState.frame?.equipment;
    if (!transforms) return;
    applyHgEquipmentDisplayTransforms(
      resources,
      resolveEquipmentDisplayTransforms(
        activeInstances,
        transforms,
        characterStore.getState().active,
      ),
    );
  }, SCENE_FRAME_PRIORITY.equipment);

  let disposed = false;
  return {
    get resources() { return resources; },
    dispose() {
      if (disposed) return;
      disposed = true;
      removeFrame();
      unsubscribeStore();
      removePointers();
      root.remove(resources.group);
      resources.dispose();
    },
  };
}
