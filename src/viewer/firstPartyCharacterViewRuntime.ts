import {
  applyCharacterPose,
  characterSource,
  type CharacterBuild,
  type CharacterSource,
  type CharacterVariant,
} from '../character';
import { suppressCorrectives } from '../character/correctiveDiagnostics';
import { configureCharacterPresentation } from '../character/build';
import { HgGroup } from '../core/sceneGraph';
import type { HandSpec } from '../exercises/types';
import type { Skeleton } from '../rig/skeleton';
import type { SceneState } from './sceneStateCore';
import { SCENE_FRAME_PRIORITY } from './sceneStateCore';
import {
  createHgCharacterMesh,
  updateHgCharacterMesh,
  type HgRenderableCharacterMesh,
} from './firstPartyCharacterScene';

export interface FirstPartyCharacterViewStudioState {
  document: { exercise: { hands: HandSpec } };
}

export interface FirstPartyCharacterViewStudioStorePort {
  getState(): FirstPartyCharacterViewStudioState;
}

export interface FirstPartyCharacterViewCharacterState {
  sourceId: string;
  correctivesPreview: boolean;
  active: CharacterBuild | null;
  setSourceStatus(status: { kind: 'idle' | 'loading' | 'error'; message?: string }): void;
  setActive(build: CharacterBuild | null): void;
}

export interface FirstPartyCharacterViewCharacterStorePort {
  getState(): FirstPartyCharacterViewCharacterState;
  subscribe(listener: () => void): () => void;
}

export interface FirstPartyCharacterViewRuntimeOptions {
  sceneState: SceneState;
  root: Pick<HgGroup, 'add' | 'remove'>;
  studioStore: FirstPartyCharacterViewStudioStorePort;
  characterStore: FirstPartyCharacterViewCharacterStorePort;
  skeleton: Skeleton;
  opacity?: number;
  colour?: string;
  depthWrite?: boolean;
  variant?: CharacterVariant;
  sourceForId?(id: string): CharacterSource;
}

export interface FirstPartyCharacterViewRuntime {
  readonly build: CharacterBuild | null;
  readonly visualRoot: HgGroup | null;
  dispose(): void;
}

/**
 * First-party visible-character adapter.
 *
 * Character posing/deformation continues to use the character source's own
 * runtime representation for now. The live scene receives only Home Gym PT
 * character-mesh snapshots, so the WebGL renderer never needs renderer-vendor
 * scene objects.
 */
export function createFirstPartyCharacterViewRuntime(
  options: FirstPartyCharacterViewRuntimeOptions,
): FirstPartyCharacterViewRuntime {
  const {
    sceneState,
    root,
    studioStore,
    characterStore,
    skeleton,
    opacity = 1,
    colour = '#ffffff',
    depthWrite = true,
    variant = 'skin',
    sourceForId = characterSource,
  } = options;

  let build: CharacterBuild | null = null;
  let visualRoot: HgGroup | null = null;
  let visualMeshes: ReturnType<typeof createHgCharacterMesh>[] = [];
  let requestedSourceId: string | null = null;
  let generation = 0;
  let disposed = false;

  const clearBuild = () => {
    const current = build;
    const currentVisual = visualRoot;
    build = null;
    visualRoot = null;
    visualMeshes = [];
    if (currentVisual) root.remove(currentVisual);
    if (current && characterStore.getState().active === current) {
      characterStore.getState().setActive(null);
    }
    current?.dispose();
  };

  const refreshVisual = () => {
    if (!build || !visualRoot) return;
    for (let index = 0; index < build.meshes.length; index += 1) {
      updateHgCharacterMesh(
        visualMeshes[index],
        build.meshes[index] as unknown as HgRenderableCharacterMesh,
      );
    }
  };

  const rebuild = async () => {
    const sourceId = characterStore.getState().sourceId;
    if (sourceId === requestedSourceId && build) return;

    requestedSourceId = sourceId;
    const token = ++generation;
    clearBuild();

    const source = sourceForId(sourceId);
    characterStore
      .getState()
      .setSourceStatus({ kind: 'loading', message: `Building ${source.label}…` });

    try {
      const next = await source.build(skeleton, { variant });
      if (
        disposed ||
        token !== generation ||
        characterStore.getState().sourceId !== sourceId
      ) {
        next.dispose();
        return;
      }

      configureCharacterPresentation(next, colour, opacity, depthWrite);
      const nextVisualRoot = new HgGroup();
      nextVisualRoot.name = 'hgpt-character-view';
      const nextVisualMeshes = next.meshes.map((mesh) =>
        createHgCharacterMesh(mesh as unknown as HgRenderableCharacterMesh));
      nextVisualRoot.add(...nextVisualMeshes);

      build = next;
      visualRoot = nextVisualRoot;
      visualMeshes = nextVisualMeshes;
      root.add(nextVisualRoot);
      characterStore.getState().setActive(next);
      characterStore.getState().setSourceStatus({ kind: 'idle' });
    } catch (error) {
      if (disposed || token !== generation) return;
      characterStore.getState().setSourceStatus({
        kind: 'error',
        message: (error as Error).message,
      });
    }
  };

  const unsubscribeCharacter = characterStore.subscribe(() => {
    if (characterStore.getState().sourceId !== requestedSourceId) {
      void rebuild();
    }
  });

  const removeFrame = sceneState.consumers.add(() => {
    const pose = sceneState.frame?.pose;
    if (!pose || !build) return;
    const hands = studioStore.getState().document.exercise.hands;
    applyCharacterPose(build, skeleton, pose, sceneState.evaluation, {
      contacts: sceneState.frame?.contacts,
      grip: { kind: hands.grip, closure: hands.closure },
    });
    if (!characterStore.getState().correctivesPreview) {
      suppressCorrectives(build.meshes);
    }
    refreshVisual();
  }, SCENE_FRAME_PRIORITY.character);

  void rebuild();

  return {
    get build() {
      return build;
    },
    get visualRoot() {
      return visualRoot;
    },
    dispose() {
      if (disposed) return;
      disposed = true;
      generation += 1;
      removeFrame();
      unsubscribeCharacter();
      clearBuild();
    },
  };
}
