import { HgVec3 } from '../core/linearMath';
import { sampleClip, type StudioClip } from '../animation/clip';
import { IK_CHAINS } from '../ik/chains';
import type { IKChainId } from '../ik/types';
import type { SceneState } from './sceneStateCore';
import { SCENE_FRAME_PRIORITY } from './sceneStateCore';
import {
  createIKHandleScene,
  registerIKHandlePointers,
  updateIKHandleSelection,
  type IKHandleKind,
  type IKHandleSceneResources,
} from './ikHandleScene';
import type { HgScenePointerRouter } from './scenePointerRouter';
import { resolveIKHandleStates } from './ikHandleSnapshot';

export interface IKHandlesState {
  time: number;
  document: { clip: StudioClip };
  selection: { handle: { chain: IKChainId; kind: IKHandleKind } | null };
  selectHandle(handle: { chain: IKChainId; kind: IKHandleKind } | null): void;
}

export interface IKHandlesStorePort {
  getState(): IKHandlesState;
  subscribe(listener: () => void): () => void;
}

export interface IKHandlesSceneRootPort {
  add(object: IKHandleSceneResources['group']): unknown;
  remove(object: IKHandleSceneResources['group']): unknown;
}

export interface IKHandlesRuntimeOptions {
  sceneState: SceneState;
  root: IKHandlesSceneRootPort;
  pointers: Pick<HgScenePointerRouter, 'register'>;
  store: IKHandlesStorePort;
}

export interface IKHandlesRuntime {
  resources: IKHandleSceneResources;
  dispose(): void;
}

/** Framework-neutral IK-handle scene lifecycle and frame controller. */
export function createIKHandlesRuntime(
  options: IKHandlesRuntimeOptions,
): IKHandlesRuntime {
  const { sceneState, root, pointers, store } = options;
  const resources = createIKHandleScene();
  root.add(resources.group);

  const removePointers = registerIKHandlePointers(
    resources,
    pointers,
    (handle) => store.getState().selectHandle(handle),
  );

  const syncSelection = () => {
    updateIKHandleSelection(resources, store.getState().selection.handle);
  };
  syncSelection();
  const unsubscribeStore = store.subscribe(syncSelection);

  const scratch = new HgVec3();
  const removeFrame = sceneState.consumers.add(() => {
    const state = store.getState();
    const sample = sampleClip(state.document.clip, state.time);
    const snapshot = resolveIKHandleStates(
      sample.ik,
      (chain) => {
        sceneState.evaluation.firstPartyEvaluation.head(IK_CHAINS[chain].end, scratch);
        return { x: scratch.x, y: scratch.y, z: scratch.z };
      },
    );

    for (const [chain, handles] of snapshot) {
      const target = resources.handles.get(`${chain}:target`);
      const pole = resources.handles.get(`${chain}:pole`);
      if (target) {
        target.visible = handles.target.visible;
        target.position.set(
          handles.target.position.x,
          handles.target.position.y,
          handles.target.position.z,
        );
      }
      if (pole) {
        pole.visible = handles.pole.visible;
        pole.position.set(
          handles.pole.position.x,
          handles.pole.position.y,
          handles.pole.position.z,
        );
      }
    }
  }, SCENE_FRAME_PRIORITY.ik);

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
