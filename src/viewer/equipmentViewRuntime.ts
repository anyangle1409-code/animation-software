import type { EquipmentInstance } from '../equipment/types';
import type { SceneState } from './sceneStateCore';
import { SCENE_FRAME_PRIORITY } from './sceneStateCore';
import {
  applyEquipmentDisplayTransforms,
  createEquipmentScene,
  registerEquipmentPointers,
  type EquipmentSceneResources,
} from './equipmentScene';
import { resolveEquipmentDisplayTransforms } from './equipmentDisplayTransforms';
import type { EquipmentDisplayCharacter } from './equipmentDisplayTransforms';
import type { HgScenePointerRouter } from './scenePointerRouter';

export interface EquipmentViewStudioState {
  document: { clip: { equipment: EquipmentInstance[] } };
  selectEquipment(id: string | null): void;
}

export interface EquipmentViewStorePort {
  getState(): EquipmentViewStudioState;
  subscribe(listener: () => void): () => void;
}

export interface EquipmentViewCharacterPort {
  getState(): { active: EquipmentDisplayCharacter | null };
}

export interface EquipmentViewRootPort {
  add(object: EquipmentSceneResources['group']): unknown;
  remove(object: EquipmentSceneResources['group']): unknown;
}

export interface EquipmentViewRuntimeOptions {
  sceneState: SceneState;
  root: EquipmentViewRootPort;
  pointers: Pick<HgScenePointerRouter, 'register'>;
  store: EquipmentViewStorePort;
  characterStore: EquipmentViewCharacterPort;
}

export interface EquipmentViewRuntime {
  readonly resources: EquipmentSceneResources;
  dispose(): void;
}

/**
 * Framework-neutral live equipment controller.
 *
 * Owns scene resources, pointer registration, exercise-equipment rebuilds and
 * per-frame character-aware placement without React lifecycle/state hooks.
 */
export function createEquipmentViewRuntime(
  options: EquipmentViewRuntimeOptions,
): EquipmentViewRuntime {
  const { sceneState, root, pointers, store, characterStore } = options;

  let activeInstances = store.getState().document.clip.equipment;
  let resources = createEquipmentScene(activeInstances);
  let removePointers = registerEquipmentPointers(
    resources,
    pointers,
    (id) => store.getState().selectEquipment(id),
  );
  root.add(resources.group);

  const rebuild = (instances: EquipmentInstance[]) => {
    removePointers();
    root.remove(resources.group);
    resources.dispose();

    activeInstances = instances;
    resources = createEquipmentScene(activeInstances);
    removePointers = registerEquipmentPointers(
      resources,
      pointers,
      (id) => store.getState().selectEquipment(id),
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
    applyEquipmentDisplayTransforms(
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
    get resources() {
      return resources;
    },
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
