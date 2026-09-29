import type { BoneName } from '../rig/boneNames';
import { isFingerBone } from '../rig/boneNames';
import type { Skeleton } from '../rig/skeleton';
import type { SceneState } from './sceneStateCore';
import { SCENE_FRAME_PRIORITY } from './sceneStateCore';
import {
  createSkeletonScene,
  registerSkeletonPointers,
  updateSkeletonAppearance,
} from './skeletonScene';
import type { SkeletonSceneResources } from './skeletonScene';
import type { HgScenePointerRouter } from './scenePointerRouter';

export interface SkeletonViewState {
  selection: { bone: BoneName | null };
  showJoints: boolean;
  selectBone(bone: BoneName | null): void;
}

export interface SkeletonViewStorePort {
  getState(): SkeletonViewState;
  subscribe(listener: () => void): () => void;
}

export interface SkeletonViewRootPort {
  add(object: SkeletonSceneResources['group']): unknown;
  remove(object: SkeletonSceneResources['group']): unknown;
}

export interface SkeletonViewRuntimeOptions {
  sceneState: SceneState;
  root: SkeletonViewRootPort;
  pointers: Pick<HgScenePointerRouter, 'register'>;
  store: SkeletonViewStorePort;
  skeleton: Skeleton;
  ghosted?: boolean;
  includeFingers?: boolean;
}

export interface SkeletonViewRuntime {
  resources: SkeletonSceneResources;
  dispose(): void;
}

/**
 * Framework-neutral live skeleton controller.
 *
 * Owns the same lifecycle React previously coordinated: scene insertion,
 * pointer registration, store-driven appearance, frame transforms and disposal.
 */
export function createSkeletonViewRuntime(
  options: SkeletonViewRuntimeOptions,
): SkeletonViewRuntime {
  const {
    sceneState,
    root,
    pointers,
    store,
    skeleton,
    ghosted = false,
    includeFingers = false,
  } = options;

  const bones = skeleton.names.filter(
    (name) => includeFingers || !isFingerBone(name),
  ) as BoneName[];
  const resources = createSkeletonScene(skeleton, bones, ghosted);

  root.add(resources.group);

  const removePointers = registerSkeletonPointers(
    resources,
    pointers,
    (bone) => store.getState().selectBone(bone),
  );

  const syncAppearance = () => {
    const state = store.getState();
    updateSkeletonAppearance(resources, state.selection.bone, state.showJoints);
  };
  syncAppearance();

  const unsubscribeStore = store.subscribe(syncAppearance);
  const removeFrame = sceneState.consumers.add(() => {
    for (const [name, objects] of resources.bones) {
      objects.group.matrix.copy(sceneState.evaluation.matrix(name));
      objects.group.matrixWorldNeedsUpdate = true;
    }
  }, SCENE_FRAME_PRIORITY.bone);

  let disposed = false;
  return {
    resources,
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
