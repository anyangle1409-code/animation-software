import type { CharacterSource } from '../character';
import { characterSource } from '../character';
import type { CharacterState } from '../editor/characterStoreCore';
import type { StudioState, ViewMode } from '../editor/storeCore';
import type { ObservableStore } from '../core/observableStore';
import type { Skeleton } from '../rig/skeleton';
import type { SceneState } from './sceneStateCore';
import type { FirstPartySceneHostBindings } from './firstPartySceneHostTypes';
import { createFirstPartyStaticStageRuntime } from './firstPartyStaticStageRuntime';
import {
  createFirstPartySkeletonViewRuntime,
  type FirstPartySkeletonViewRuntime,
} from './firstPartySkeletonViewRuntime';
import {
  createFirstPartyMuscleViewRuntime,
  type FirstPartyMuscleViewRuntime,
} from './firstPartyMuscleViewRuntime';
import {
  createFirstPartyEquipmentViewRuntime,
  type FirstPartyEquipmentViewRuntime,
} from './firstPartyEquipmentViewRuntime';
import {
  createFirstPartyIKHandlesRuntime,
  type FirstPartyIKHandlesRuntime,
} from './firstPartyIKHandlesRuntime';
import {
  createFirstPartyCharacterViewRuntime,
  type FirstPartyCharacterViewRuntime,
} from './firstPartyCharacterViewRuntime';
import {
  createOrbitControlsRuntime,
  type OrbitControlsRuntime,
} from './orbitControlsRuntime';
import {
  createCameraRigRuntime,
  type CameraRigRuntime,
} from './cameraRigRuntime';
import {
  createFirstPartyStudioHandleGizmoRuntime,
  createFirstPartyStudioSelectionGizmoRuntime,
  type FirstPartyStudioEditRuntime,
} from './firstPartyStudioEditRuntimes';

type StorePort<T> = Pick<ObservableStore<T>, 'getState' | 'subscribe'>;

export interface FirstPartyStudioSceneControllerOptions {
  sceneState: SceneState;
  bindings: FirstPartySceneHostBindings;
  studioStore: StorePort<StudioState>;
  characterStore: StorePort<CharacterState>;
  skeleton: Skeleton;
  characterSourceForId?(id: string): CharacterSource;
}

export interface FirstPartyStudioSceneController {
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
 * Complete Studio scene composition on the Home Gym PT scene graph.
 *
 * This mirrors the live controller's state/lifecycle contract while using only
 * first-party stage, overlay, character-snapshot and gizmo scene resources.
 * It remains parallel to the live controller until renderer/visual parity is
 * certified, so the eventual cutover is one dependency swap rather than a
 * broad behavior rewrite.
 */
export function createFirstPartyStudioSceneController(
  options: FirstPartyStudioSceneControllerOptions,
): FirstPartyStudioSceneController {
  const {
    sceneState,
    bindings,
    studioStore,
    characterStore,
    skeleton,
    characterSourceForId = characterSource,
  } = options;
  const { scene: root, camera, element, pointers } = bindings;

  const stage = createFirstPartyStaticStageRuntime(root, studioStore);
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
  const selectionGizmo: FirstPartyStudioEditRuntime =
    createFirstPartyStudioSelectionGizmoRuntime({
      sceneState,
      root,
      pointers,
      camera,
      store: studioStore,
      skeleton,
      controls: () => orbit.handle,
    });
  const handleGizmo: FirstPartyStudioEditRuntime =
    createFirstPartyStudioHandleGizmoRuntime({
      sceneState,
      root,
      pointers,
      camera,
      store: studioStore,
      skeleton,
      controls: () => orbit.handle,
    });

  let skeletonRuntime: FirstPartySkeletonViewRuntime | null = null;
  let skeletonKey: 'solid' | 'ghosted' | null = null;
  let muscleRuntime: FirstPartyMuscleViewRuntime | null = null;
  let equipmentRuntime: FirstPartyEquipmentViewRuntime | null = null;
  let ikRuntime: FirstPartyIKHandlesRuntime | null = null;
  let characterRuntime: FirstPartyCharacterViewRuntime | null = null;
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
        skeletonRuntime = createFirstPartySkeletonViewRuntime({
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
      muscleRuntime = createFirstPartyMuscleViewRuntime({
        sceneState,
        root,
        store: studioStore,
      });
    } else if (!wantMuscles && muscleRuntime) {
      muscleRuntime.dispose();
      muscleRuntime = null;
    }

    if (studio.showEquipment && !equipmentRuntime) {
      equipmentRuntime = createFirstPartyEquipmentViewRuntime({
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
      ikRuntime = createFirstPartyIKHandlesRuntime({
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
        characterRuntime = createFirstPartyCharacterViewRuntime({
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
