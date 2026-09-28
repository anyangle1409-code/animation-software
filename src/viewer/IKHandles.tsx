import { useEffect, useMemo } from 'react';
import { Vector3 } from 'three';
import { IK_CHAINS, IK_CHAIN_IDS } from '../ik/chains';
import { useStudio } from '../editor/store';
import { SCENE_FRAME_PRIORITY, useSceneFrame, useSceneState } from './sceneState';
import { sampleClip } from '../animation/clip';
import {
  createIKHandleScene,
  registerIKHandlePointers,
  updateIKHandleSelection,
} from './ikHandleScene';
import { SceneObjectMount } from './SceneObjectMount';
import { useSceneHostBindings } from './sceneHostBindings';

/**
 * Draggable handle visuals for each limb.
 *
 * The meshes are owned directly by the shared scene host and selection clicks
 * use the project-owned pointer router. The separate transform gizmo still
 * performs handle dragging after selection.
 */
export function IKHandles() {
  const scene = useSceneState();
  const time = useStudio((state) => state.time);
  const clip = useStudio((state) => state.document.clip);
  const selection = useStudio((state) => state.selection.handle);
  const selectHandle = useStudio((state) => state.selectHandle);
  const { pointers } = useSceneHostBindings();
  const resources = useMemo(createIKHandleScene, []);

  useEffect(() => () => resources.dispose(), [resources]);

  useEffect(
    () => registerIKHandlePointers(resources, pointers, selectHandle),
    [resources, pointers, selectHandle],
  );

  useEffect(() => {
    updateIKHandleSelection(resources, selection);
  }, [resources, selection]);

  useSceneFrame(() => {
    const sample = sampleClip(clip, time);
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
        const effector = scene.evaluation.head(IK_CHAINS[chain].end, new Vector3());
        target.position.copy(effector);
      }
    }
  }, SCENE_FRAME_PRIORITY.ik);

  return <SceneObjectMount object={resources.group} />;
}
