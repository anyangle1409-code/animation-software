import {
  applyCharacterPose,
  characterSource,
  type CharacterBuild,
  type CharacterSource,
  type CharacterVariant,
} from '../character';
import { suppressCorrectives } from '../character/correctiveDiagnostics';
import { configureCharacterPresentation } from '../character/build';
import type { HandSpec } from '../exercises/types';
import type { Skeleton } from '../rig/skeleton';
import type { SceneState } from './sceneStateCore';
import { SCENE_FRAME_PRIORITY } from './sceneStateCore';

export interface CharacterViewStudioState {
  document: { exercise: { hands: HandSpec } };
}

export interface CharacterViewStudioStorePort {
  getState(): CharacterViewStudioState;
}

export interface CharacterViewCharacterState {
  sourceId: string;
  correctivesPreview: boolean;
  active: CharacterBuild | null;
  setSourceStatus(status: { kind: 'idle' | 'loading' | 'error'; message?: string }): void;
  setActive(build: CharacterBuild | null): void;
}

export interface CharacterViewCharacterStorePort {
  getState(): CharacterViewCharacterState;
  subscribe(listener: () => void): () => void;
}

export interface CharacterViewRuntimeOptions {
  sceneState: SceneState;
  root: {
    add(...objects: CharacterBuild['object'][]): unknown;
    remove(...objects: CharacterBuild['object'][]): unknown;
  };
  studioStore: CharacterViewStudioStorePort;
  characterStore: CharacterViewCharacterStorePort;
  skeleton: Skeleton;
  opacity?: number;
  colour?: string;
  depthWrite?: boolean;
  variant?: CharacterVariant;
  sourceForId?(id: string): CharacterSource;
}

export interface CharacterViewRuntime {
  readonly build: CharacterBuild | null;
  dispose(): void;
}

/**
 * Framework-neutral visible-character lifecycle.
 *
 * Owns async build cancellation/replacement, scene mounting, active-character
 * publication, presentation material settings and per-frame posing.
 */
export function createCharacterViewRuntime(
  options: CharacterViewRuntimeOptions,
): CharacterViewRuntime {
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
  let requestedSourceId: string | null = null;
  let generation = 0;
  let disposed = false;

  const clearBuild = () => {
    const current = build;
    if (!current) return;
    build = null;
    root.remove(current.object);
    if (characterStore.getState().active === current) {
      characterStore.getState().setActive(null);
    }
    current.dispose();
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
      build = next;
      root.add(next.object);
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
  }, SCENE_FRAME_PRIORITY.character);

  void rebuild();

  return {
    get build() {
      return build;
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
