import type { CharacterSource } from '../character';
import { characterSource } from '../character';
import type { CharacterState } from '../editor/characterStoreCore';
import type { StudioState, ViewMode } from '../editor/storeCore';
import type { ObservableStore } from '../core/observableStore';
import type { Skeleton } from '../rig/skeleton';
import type { SceneHostBindings } from './sceneHostTypes';
import type { SceneState } from './sceneStateCore';
import { createStaticStageRuntime } from './staticStageRuntime';
import { createSkeletonViewRuntime, type SkeletonViewRuntime } from './skeletonViewRuntime';
import { createMuscleViewRuntime, type MuscleViewRuntime } from './muscleViewRuntime';
import { createEquipmentViewRuntime, type EquipmentViewRuntime } from './equipmentViewRuntime';
import { createIKHandlesRuntime, type IKHandlesRuntime } from './ikHandlesRuntime';
import { createCharacterViewRuntime, type CharacterViewRuntime } from './characterViewRuntime';
import { createOrbitControlsRuntime, type OrbitControlsRuntime } from './orbitControlsRuntime';
import { createCameraRigRuntime, type CameraRigRuntime } from './cameraRigRuntime';
import {
  createStudioHandleGizmoRuntime,
  createStudioSelectionGizmoRuntime,
  type StudioEditRuntime,
} from './studioEditRuntimes';

type StorePort<T> = Pick<ObservableStore<T>, 'getState' | 'subscribe'>;

export interface StudioSceneControllerOptions {
  sceneState: SceneState;
  bindings: SceneHostBindings;
  studioStore: StorePort<StudioState>;
  characterStore: StorePort<CharacterState>;
  skeleton: Skeleton;
  characterSourceForId?(id: string): CharacterSource;
}

export interface StudioSceneController {
  dispose(): void;
}

interface CharacterPresentation {
  variant: 'skin' | 'ecorche';
  opacity: number;
  depthWrite: boolean;
}

const muscleVisible = (mode: ViewMode): boolean =>
  mode === 'muscles' || mode === 'combined';

const characterPresentation = (
  mode: ViewMode,
  sourceId: string,
  sourceForId: (id: string) => CharacterSource,
): CharacterPresentation | null => {
  if (mode === 'character') return { variant: 'skin', opacity: 1, depthWrite: true };
  if (mode === 'muscles') return { variant: 'skin', opacity: 0.24, depthWrite: false };
  if (mode === 'anatomy') {
    return {
      variant: sourceForId(sourceId).capabilities.anatomy ? 'ecorche' : 'skin',
      opacity: 1,
      depthWrite: true,
    };
  }
  return null;
};

/**
 * Framework-neutral composition of the complete Studio scene.
 *
 * React may continue to render the reference path while this controller is
 * parity-tested, but all lifecycle/state ownership here is plain TypeScript.
 */
export function createStudioSceneController(
  options: StudioSceneControllerOptions,
): StudioSceneController {
  const {
    sceneState,
    bindings,
    studioStore,
    characterStore,
    skeleton,
    characterSourceForId = characterSource,
  } = options;
  const { scene: root, camera, element, pointers } = bindings;

  const stage = createStaticStageRuntime(root, studioStore);
  const orbit: OrbitControlsRuntime = createOrbitControlsRuntime(
    camera,
    element,
    sceneState,
  );
  const cameraRig: CameraRigRuntime = createCameraRigRuntime({
    sceneState,
    camera,
    store: studioStore,
    controls: () => orbit.handle,
  });
  const selectionGizmo: StudioEditRuntime = createStudioSelectionGizmoRuntime({
    sceneState,
    root,
    pointers,
    camera,
    store: studioStore,
    skeleton,
    controls: () => orbit.handle,
  });
  const handleGizmo: StudioEditRuntime = createStudioHandleGizmoRuntime({
    sceneState,
    root,
    pointers,
    camera,
    store: studioStore,
    skeleton,
    controls: () => orbit.handle,
  });

  let skeletonRuntime: SkeletonViewRuntime | null = null;
  let skeletonKey: 'solid' | 'ghosted' | null = null;
  let muscleRuntime: MuscleViewRuntime | null = null;
  let equipmentRuntime: EquipmentViewRuntime | null = null;
  let ikRuntime: IKHandlesRuntime | null = null;
  let characterRuntime: CharacterViewRuntime | null = null;
  let characterKey: string | null = null;
  let disposed = false;

  const sync = () => {
    if (disposed) return;
    const studio = studioStore.getState();
    const character = characterStore.getState();

    const nextSkeletonKey =
      studio.viewMode === 'skeleton'
        ? 'solid'
        : studio.viewMode === 'combined'
          ? 'ghosted'
          : null;
    if (nextSkeletonKey !== skeletonKey) {
      skeletonRuntime?.dispose();
      skeletonRuntime = null;
      skeletonKey = nextSkeletonKey;
      if (nextSkeletonKey) {
        skeletonRuntime = createSkeletonViewRuntime({
          sceneState,
          root,
          pointers,
          store: studioStore,
          skeleton,
          ghosted: nextSkeletonKey === 'ghosted',
        });
      }
    }

    const wantMuscles = muscleVisible(studio.viewMode);
    if (wantMuscles && !muscleRuntime) {
      muscleRuntime = createMuscleViewRuntime({
        sceneState,
        root,
        store: studioStore,
      });
    } else if (!wantMuscles && muscleRuntime) {
      muscleRuntime.dispose();
      muscleRuntime = null;
    }

    if (studio.showEquipment && !equipmentRuntime) {
      equipmentRuntime = createEquipmentViewRuntime({
        sceneState,
        root,
        pointers,
        store: studioStore,
        characterStore,
      });
    } else if (!studio.showEquipment && equipmentRuntime) {
      equipmentRuntime.dispose();
      equipmentRuntime = null;
    }

    if (studio.showIkHandles && !ikRuntime) {
      ikRuntime = createIKHandlesRuntime({
        sceneState,
        root,
        pointers,
        store: studioStore,
      });
    } else if (!studio.showIkHandles && ikRuntime) {
      ikRuntime.dispose();
      ikRuntime = null;
    }

    const presentation = characterPresentation(
      studio.viewMode,
      character.sourceId,
      characterSourceForId,
    );
    const nextCharacterKey = presentation
      ? `${presentation.variant}:${presentation.opacity}:${presentation.depthWrite}`
      : null;

    if (nextCharacterKey !== characterKey) {
      const previousCharacter = characterRuntime;
      characterRuntime = null;
      characterKey = nextCharacterKey;
      previousCharacter?.dispose();
      if (presentation) {
        characterRuntime = createCharacterViewRuntime({
          sceneState,
          root,
          studioStore,
          characterStore,
          skeleton,
          opacity: presentation.opacity,
          depthWrite: presentation.depthWrite,
          variant: presentation.variant,
          sourceForId: characterSourceForId,
        });
      }
    }
  };

  const unsubscribeStudio = studioStore.subscribe(sync);
  const unsubscribeCharacter = characterStore.subscribe(sync);
  sync();

  return {
    dispose() {
      if (disposed) return;
      disposed = true;
      unsubscribeStudio();
      unsubscribeCharacter();
      characterRuntime?.dispose();
      ikRuntime?.dispose();
      equipmentRuntime?.dispose();
      muscleRuntime?.dispose();
      skeletonRuntime?.dispose();
      handleGizmo.dispose();
      selectionGizmo.dispose();
      cameraRig.dispose();
      orbit.dispose();
      stage.dispose();
    },
  };
}
