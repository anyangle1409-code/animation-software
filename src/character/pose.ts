import { Euler, Matrix4, Quaternion, Vector3 } from 'three';
import type { PoseEvaluation, Skeleton } from '../rig/skeleton';
import type { Pose } from '../rig/types';
import { EULER_ORDER } from '../rig/types';
import type { BoneName, Finger } from '../rig/boneNames';
import { solvedGripFor } from './solvedGrip';
import type { CharacterBuild, CharacterPoseContext } from './types';

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
  context?: CharacterPoseContext,
): void {
  const posed = withSolvedGrip(character, pose, context);

  // A character that kept its own skeleton drives itself: the canonical bones
  // are not its bones, so its joint angles come through its own transfer.
  if (character.driver) {
    character.driver(posed, context);
    if (character.deformation && evaluation) {
      character.deformation.update({ rig, pose, evaluation, character });
    }
    return;
  }

  for (const rigBone of rig.bones) {
    const bone = character.boneByName.get(rigBone.name);
    if (!bone) continue;
    const rotation = posed.rotations[rigBone.name];
    scratch.euler.set(rotation?.x ?? 0, rotation?.y ?? 0, rotation?.z ?? 0, EULER_ORDER);
    scratch.quaternion
      .copy(rigBone.restLocalQuaternion)
      .multiply(scratch.local.setFromEuler(scratch.euler));
    bone.matrix.compose(scratch.offset.copy(rigBone.offset), scratch.quaternion, UNIT);

    if (rigBone.parent === null) {
      // The root additionally carries the rig's world placement, exactly as the
      // pose evaluation does — root motion is part of the animation.
      scratch.euler.set(posed.rootRotation.x, posed.rootRotation.y, posed.rootRotation.z, EULER_ORDER);
      scratch.placement.compose(
        scratch.offset.set(posed.rootPosition.x, posed.rootPosition.y, posed.rootPosition.z),
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

const FINGERS: Finger[] = ['thumb', 'index', 'middle', 'ring', 'pinky'];
const gripScratch: Pose = { rotations: {}, rootPosition: { x: 0, y: 0, z: 0 }, rootRotation: { x: 0, y: 0, z: 0 } };

/**
 * Swap in a character's solved grip where it has one.
 *
 * The canonical pose arrives with the authored profile already baked into its
 * finger rotations — one row of angles for all four fingers, closed by a single
 * scalar, which shuts the hand through the handle rather than onto it. A
 * character that carries a solved grip replaces those rotations with the
 * close-until-contact angles measured on its own hand.
 *
 * The incoming pose is shared with the canonical rig and the solver, so it is
 * never written to: only the finger bones are overridden, into a scratch pose
 * that borrows everything else by reference.
 */
function withSolvedGrip(
  character: CharacterBuild,
  pose: Pose,
  context?: CharacterPoseContext,
): Pose {
  const grip = context?.grip;
  if (!grip) return pose;
  const solved = solvedGripFor(character.gripSolutionId, grip.kind);
  if (!solved) return pose;

  const closure = Math.max(0, Math.min(1, grip.closure));
  const rotations: Pose['rotations'] = Object.create(null);
  Object.assign(rotations, pose.rotations);
  for (const side of ['l', 'r'] as const) {
    const sign = side === 'l' ? 1 : -1;
    for (const finger of FINGERS) {
      const row = solved.digits[finger];
      if (!row) continue;
      row.forEach((maximum, index) => {
        const bone = `${finger}_0${index + 1}_${side}` as BoneName;
        const existing = pose.rotations[bone];
        rotations[bone] = {
          x:
            finger === 'thumb' && index === 0
              ? (solved.thumbOppositionX * closure * Math.PI) / 180
              : existing?.x ?? 0,
          y: existing?.y ?? 0,
          z: (sign * maximum * closure * Math.PI) / 180,
        };
      });
    }
  }
  gripScratch.rotations = rotations;
  gripScratch.rootPosition = pose.rootPosition;
  gripScratch.rootRotation = pose.rootRotation;
  return gripScratch;
}
