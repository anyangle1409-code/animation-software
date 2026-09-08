import { useFrame } from '@react-three/fiber';
import { useEffect, useMemo } from 'react';
import { Euler, Matrix4, MeshStandardMaterial, Quaternion, Vector3 } from 'three';
import { EULER_ORDER } from '../rig/types';
import { skeleton } from '../editor/store';
import { buildSkinnedRig } from '../body/skin';
import { useSceneState } from './sceneState';

export interface MannequinViewProps {
  opacity?: number;
  colour?: string;
  /**
   * A ghosted body must not write depth, or it hides the muscles inside it —
   * which is the one thing the muscle view exists to show.
   */
  depthWrite?: boolean;
}

const UNIT = new Vector3(1, 1, 1);

/**
 * The character: one skinned body, lofted from the body profiles and driven by
 * the same pose everything else reads.
 *
 * It is built by the same function the GLB exporter uses, so what the studio
 * shows and what the exported file contains are the same mesh, bound to the
 * same bones, with the same weights.
 */
export function MannequinView({
  opacity = 1,
  colour = '#c9d3e0',
  depthWrite = true,
}: MannequinViewProps) {
  const scene = useSceneState();
  const rig = useMemo(() => buildSkinnedRig(skeleton), []);

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
