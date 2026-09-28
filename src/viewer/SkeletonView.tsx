import { useEffect, useMemo } from 'react';
import type { BoneName } from '../rig/boneNames';
import { isFingerBone } from '../rig/boneNames';
import { skeleton, useStudio } from '../editor/store';
import { SCENE_FRAME_PRIORITY, useSceneFrame, useSceneState } from './sceneState';
import {
  createSkeletonScene,
  registerSkeletonPointers,
  updateSkeletonAppearance,
} from './skeletonScene';
import { SceneObjectMount } from './SceneObjectMount';
import { useSceneHostBindings } from './sceneHostBindings';

export interface SkeletonViewProps {
  /** Dim the skeleton when it sits behind the muscle or character layer. */
  ghosted?: boolean;
  includeFingers?: boolean;
}

/**
 * Project-owned skeleton scene.
 *
 * Bone groups and visible geometry mount directly through the shared scene
 * port. Joint selection is routed by the first-party pointer router.
 */
export function SkeletonView({ ghosted = false, includeFingers = false }: SkeletonViewProps) {
  const scene = useSceneState();
  const selected = useStudio((state) => state.selection.bone);
  const selectBone = useStudio((state) => state.selectBone);
  const showJoints = useStudio((state) => state.showJoints);
  const { pointers } = useSceneHostBindings();

  const bones = useMemo(
    () => skeleton.names.filter((name) => includeFingers || !isFingerBone(name)),
    [includeFingers],
  );
  const resources = useMemo(
    () => createSkeletonScene(skeleton, bones as BoneName[], ghosted),
    [bones, ghosted],
  );

  useEffect(() => () => resources.dispose(), [resources]);

  useEffect(
    () => registerSkeletonPointers(resources, pointers, selectBone),
    [resources, pointers, selectBone],
  );

  useEffect(() => {
    updateSkeletonAppearance(resources, selected, showJoints);
  }, [resources, selected, showJoints]);

  useSceneFrame(() => {
    for (const [name, objects] of resources.bones) {
      objects.group.matrix.copy(scene.evaluation.matrix(name));
      objects.group.matrixWorldNeedsUpdate = true;
    }
  }, SCENE_FRAME_PRIORITY.bone);

  return <SceneObjectMount object={resources.group} />;
}
