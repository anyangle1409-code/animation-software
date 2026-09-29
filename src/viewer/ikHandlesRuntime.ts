import { HgVec3 } from '../core/linearMath';
import { sampleClip, type StudioClip } from '../animation/clip';
import { IK_CHAINS, IK_CHAIN_IDS } from '../ik/chains';
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
    for (const chain of IK_CHAIN_IDS) {
      const goal = sample.ik[chain];
      const target = resources.handles.get(`${chain}:target`);
      const pole = resources.handles.get(`${chain}:pole`);
      const active = Boolean(goal?.enabled);

      if (target) {
        target.visible = active;
        if (goal) target.position.set(goal.target.x, goal.target.y, goal.target.z);
      }
      if (pole) {
        pole.visible = active;
        if (goal) pole.position.set(goal.pole.x, goal.pole.y, goal.pole.z);
      }
      if (!active && target) {
        sceneState.evaluation.firstPartyEvaluation.head(IK_CHAINS[chain].end, scratch);
        target.position.set(scratch.x, scratch.y, scratch.z);
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
