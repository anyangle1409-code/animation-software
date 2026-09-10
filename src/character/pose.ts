import { Euler, Matrix4, Quaternion, Vector3 } from 'three';
import type { PoseEvaluation, Skeleton } from '../rig/skeleton';
import type { Pose } from '../rig/types';
import { EULER_ORDER } from '../rig/types';
import type { CharacterBuild } from './types';

const UNIT = new Vector3(1, 1, 1);
const scratch = {
  euler: new Euler(0, 0, 0, EULER_ORDER),
  quaternion: new Quaternion(),
  local: new Quaternion(),
  placement: new Matrix4(),
  offset: new Vector3(),
};

/**
 * Drive a built character from a canonical pose.
 *
 * Every character is posed here, whichever source built it, and the character's
 * own deformation stack runs immediately afterwards on the matrices this just
 * wrote. That is the whole of the skinning layer's per-frame work — the
 * viewport adds nothing of its own, so what the exporter bakes and what the
 * studio shows come from one piece of code.
 */
export function applyCharacterPose(
  character: CharacterBuild,
  rig: Skeleton,
  pose: Pose,
  evaluation?: PoseEvaluation,
): void {
  for (const rigBone of rig.bones) {
    const bone = character.boneByName.get(rigBone.name);
    if (!bone) continue;
    const rotation = pose.rotations[rigBone.name];
    scratch.euler.set(rotation?.x ?? 0, rotation?.y ?? 0, rotation?.z ?? 0, EULER_ORDER);
    scratch.quaternion
      .copy(rigBone.restLocalQuaternion)
      .multiply(scratch.local.setFromEuler(scratch.euler));
    bone.matrix.compose(scratch.offset.copy(rigBone.offset), scratch.quaternion, UNIT);

    if (rigBone.parent === null) {
      // The root additionally carries the rig's world placement, exactly as the
      // pose evaluation does — root motion is part of the animation.
      scratch.euler.set(pose.rootRotation.x, pose.rootRotation.y, pose.rootRotation.z, EULER_ORDER);
      scratch.placement.compose(
        scratch.offset.set(pose.rootPosition.x, pose.rootPosition.y, pose.rootPosition.z),
        scratch.quaternion.setFromEuler(scratch.euler),
        UNIT,
      );
      bone.matrix.premultiply(scratch.placement);
    }
  }
  character.root.updateMatrixWorld(true);

  if (character.deformation && evaluation) {
    character.deformation.update({ rig, pose, evaluation, character });
  }
}
