import { useFrame } from '@react-three/fiber';
import { useEffect, useMemo } from 'react';
import { Color, Euler, Matrix4, MeshStandardMaterial, Quaternion, Vector3 } from 'three';
import { EULER_ORDER } from '../rig/types';
import { skeleton } from '../editor/store';
import { buildSkinnedRig } from '../body/skin';
import { useSceneState } from './sceneState';
import { useStudio } from '../editor/store';
import { MUSCLE_GROUP_IDS } from '../muscles/groups';
import { ACTIVATION_STYLES, activationMap, activationOf } from '../muscles/activation';

export interface MannequinViewProps {
  opacity?: number;
  /** Multiplies the body's own vertex colours; white leaves them as authored. */
  colour?: string;
  /**
   * A ghosted body must not write depth, or it hides the muscles inside it —
   * which is the one thing the muscle view exists to show.
   */
  depthWrite?: boolean;
  /** Paint exercise activation directly onto the anatomical skin surface. */
  highlightMuscles?: boolean;
}

const UNIT = new Vector3(1, 1, 1);

/**
 * The character: one anatomical skinned body driven by the same pose everything
 * else reads.
 *
 * It is built by the same function the GLB exporter uses, so what the studio
 * shows and what the exported file contains are the same mesh, bound to the
 * same bones, with the same weights.
 */
export function MannequinView({
  opacity = 1,
  colour = '#ffffff',
  depthWrite = true,
  highlightMuscles = false,
}: MannequinViewProps) {
  const scene = useSceneState();
  const rig = useMemo(() => buildSkinnedRig(skeleton), []);
  const involvement = useStudio((state) => state.document.exercise.muscles);
  const activation = useMemo(() => activationMap(involvement), [involvement]);
  const baseColours = useMemo(
    () => new Float32Array((rig.mesh.geometry.getAttribute('color').array as ArrayLike<number>)),
    [rig],
  );

  const scratch = useMemo(
    () => ({
      euler: new Euler(0, 0, 0, EULER_ORDER),
      quaternion: new Quaternion(),
      local: new Quaternion(),
      placement: new Matrix4(),
      offset: new Vector3(),
    }),
    [],
  );

  useEffect(() => {
    for (const bone of rig.bones) bone.matrixAutoUpdate = false;
  }, [rig]);

  useEffect(() => {
    const material = rig.mesh.material as MeshStandardMaterial;
    material.color.set(colour);
    material.opacity = opacity;
    material.transparent = opacity < 1;
    material.depthWrite = depthWrite;
    material.needsUpdate = true;
  }, [rig, colour, opacity, depthWrite]);

  useEffect(() => {
    const attribute = rig.mesh.geometry.getAttribute('color');
    const groups = rig.mesh.geometry.getAttribute('muscleGroup');
    const colourValue = new Color();
    for (let vertex = 0; vertex < attribute.count; vertex += 1) {
      const groupNumber = groups?.getX(vertex) ?? 0;
      if (!highlightMuscles || groupNumber === 0) {
        attribute.setXYZ(
          vertex,
          baseColours[vertex * 3],
          baseColours[vertex * 3 + 1],
          baseColours[vertex * 3 + 2],
        );
        continue;
      }
      const group = MUSCLE_GROUP_IDS[groupNumber - 1];
      const level = activationOf(activation, group);
      if (level === 'inactive') {
        colourValue.set('#b8bdc2');
      } else {
        colourValue.set(ACTIVATION_STYLES[level].colour);
      }
      attribute.setXYZ(vertex, colourValue.r, colourValue.g, colourValue.b);
    }
    attribute.needsUpdate = true;
  }, [rig, baseColours, highlightMuscles, activation]);

  useEffect(() => () => {
    (rig.mesh.material as MeshStandardMaterial).dispose();
  }, [rig]);

  useFrame(() => {
    const pose = scene.frame?.pose;
    if (!pose) return;

    for (const rigBone of skeleton.bones) {
      const bone = rig.boneByName.get(rigBone.name);
      if (!bone) continue;
      const rotation = pose.rotations[rigBone.name];
      scratch.euler.set(rotation?.x ?? 0, rotation?.y ?? 0, rotation?.z ?? 0, EULER_ORDER);
      scratch.quaternion
        .copy(rigBone.restLocalQuaternion)
        .multiply(scratch.local.setFromEuler(scratch.euler));
      bone.matrix.compose(scratch.offset.copy(rigBone.offset), scratch.quaternion, UNIT);

      if (rigBone.parent === null) {
        // The root additionally carries the rig's world placement, exactly as
        // the pose evaluation does — root motion is part of the animation.
        scratch.euler.set(
          pose.rootRotation.x,
          pose.rootRotation.y,
          pose.rootRotation.z,
          EULER_ORDER,
        );
        scratch.placement.compose(
          scratch.offset.set(pose.rootPosition.x, pose.rootPosition.y, pose.rootPosition.z),
          scratch.quaternion.setFromEuler(scratch.euler),
          UNIT,
        );
        bone.matrix.premultiply(scratch.placement);
      }
    }
    rig.root.updateMatrixWorld(true);
  });

  return <primitive object={rig.mesh} />;
}
