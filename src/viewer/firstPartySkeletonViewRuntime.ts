import type { BoneName } from '../rig/boneNames';
import { isFingerBone } from '../rig/boneNames';
import type { Skeleton } from '../rig/skeleton';
import type { HgObject3D } from '../core/sceneGraph';
import type { SceneState } from './sceneStateCore';
import { SCENE_FRAME_PRIORITY } from './sceneStateCore';
import {
  createHgSkeletonScene,
  registerHgSkeletonPointers,
  updateHgSkeletonAppearance,
  type HgSkeletonSceneResources,
} from './firstPartySkeletonScene';
import type { HgScenePointerRouter } from './scenePointerRouter';

export interface FirstPartySkeletonViewState {
  selection: { bone: BoneName | null };
  showJoints: boolean;
  selectBone(bone: BoneName | null): void;
}
export interface FirstPartySkeletonViewStorePort {
  getState(): FirstPartySkeletonViewState;
  subscribe(listener: () => void): () => void;
}
export interface FirstPartySkeletonViewRuntime {
  resources: HgSkeletonSceneResources;
  dispose(): void;
}

export function createFirstPartySkeletonViewRuntime(options: {
  sceneState: SceneState;
  root: Pick<HgObject3D, 'add' | 'remove'>;
  pointers: Pick<HgScenePointerRouter, 'register'>;
  store: FirstPartySkeletonViewStorePort;
  skeleton: Skeleton;
  ghosted?: boolean;
  includeFingers?: boolean;
}): FirstPartySkeletonViewRuntime {
  const {
    sceneState, root, pointers, store, skeleton,
    ghosted = false, includeFingers = false,
  } = options;
  const bones = skeleton.names.filter(
    (name) => includeFingers || !isFingerBone(name),
  ) as BoneName[];
  const resources = createHgSkeletonScene(skeleton, bones, ghosted);
  root.add(resources.group);
  const removePointers = registerHgSkeletonPointers(
    resources, pointers, (bone) => store.getState().selectBone(bone),
  );
  const syncAppearance = () => {
    const state = store.getState();
    updateHgSkeletonAppearance(resources, state.selection.bone, state.showJoints);
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
