import { useFrame } from '@react-three/fiber';
import { useEffect, useMemo } from 'react';
import { Euler, Matrix4, MeshStandardMaterial, Quaternion, Vector3 } from 'three';
import { EULER_ORDER } from '../rig/types';
import { skeleton, useStudio } from '../editor/store';
import { buildSkinnedRig } from '../body/skin';
import { applyActivation, buildEcorcheGeometry, createEcorcheMaterial } from '../body/ecorche';
import { applyElbowCorrective, buildElbowCorrective, elbowFlexion } from '../body/elbow';

/**
 * On. The widened skin blend rounds the crease but leaves the inside of the
 * elbow passing through itself at high flexion, so the pose-space correction is
 * carrying that part.
 */
const ELBOW_CORRECTIVE = true;
import { useSceneState } from './sceneState';

/** The character's own surface, or the same body read as an écorché. */
export type BodyVariant = 'skin' | 'ecorche';

export interface MannequinViewProps {
  opacity?: number;
  /** Multiplies the body's own vertex colours; white leaves them as authored. */
  colour?: string;
  /**
   * A ghosted body must not write depth, or it hides the muscles inside it —
   * which is the one thing the muscle view exists to show.
   */
  depthWrite?: boolean;
  variant?: BodyVariant;
}

const UNIT = new Vector3(1, 1, 1);

/**
 * The character: one skinned body driven by the same pose everything else
 * reads.
 *
 * It is built by the same function the GLB exporter uses, so what the studio
 * shows and what the exported file contains are the same mesh, bound to the
 * same bones, with the same weights.
 */
export function MannequinView({
  opacity = 1,
  colour = '#ffffff',
  depthWrite = true,
  variant = 'skin',
}: MannequinViewProps) {
  const scene = useSceneState();
  const involvement = useStudio((state) => state.document.exercise.muscles);
  const rig = useMemo(
    () =>
      variant === 'ecorche'
        ? buildSkinnedRig(skeleton, {
            geometry: buildEcorcheGeometry(skeleton),
            material: createEcorcheMaterial(),
          })
        : buildSkinnedRig(skeleton),
    [variant],
  );

  // Which muscles the exercise works is data, and it can change under the view,
  // so the scalar the shader reads is rebuilt rather than baked once.
  useEffect(() => {
    if (variant !== 'ecorche') return;
    applyActivation(rig.mesh.geometry, involvement);
  }, [rig, variant, involvement]);

  // The elbow correction is bind-pose data, so it belongs to the geometry and is
  // rebuilt only when the geometry is.
  const elbow = useMemo(
    () => (variant === 'ecorche' && ELBOW_CORRECTIVE ? buildElbowCorrective(rig.mesh.geometry, skeleton) : null),
    [rig, variant],
  );
  const flexion = useMemo<[number, number]>(() => [-1, -1], [elbow]);

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

    if (elbow) {
      const left = elbowFlexion(scene.evaluation, 'l');
      const right = elbowFlexion(scene.evaluation, 'r');
      // Rewriting the bind pose uploads a buffer, so only do it when the angle
      // has actually moved.
      if (Math.abs(left - flexion[0]) > 0.002 || Math.abs(right - flexion[1]) > 0.002) {
        flexion[0] = left;
        flexion[1] = right;
        applyElbowCorrective(rig.mesh.geometry, elbow, flexion);
      }
    }

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
