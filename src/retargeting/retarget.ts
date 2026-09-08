import { Box3, Euler, Object3D, Quaternion, Vector3 } from 'three';
import type { Bone, SkinnedMesh } from 'three';
import type { BoneName } from '../rig/boneNames';
import { boneFrame, canonicalSkeleton } from '../rig/skeleton';
import type { Skeleton } from '../rig/skeleton';
import type { Pose } from '../rig/types';
import { EULER_ORDER } from '../rig/types';
import { RIG_HEIGHT } from '../rig/humanoid';
import type { BoneMapping } from './boneMap';

/** A character imported from a GLB, measured once at load time. */
export interface TargetCharacter {
  root: Object3D;
  bones: Map<string, Bone>;
  boneNames: string[];
  /** World position and rotation of each bone in the character's rest pose. */
  restWorldPosition: Map<string, Vector3>;
  restWorld: Map<string, Quaternion>;
  restLocal: Map<string, Quaternion>;
  height: number;
  meshes: SkinnedMesh[];
}

interface BoundBone {
  canonical: BoneName;
  bone: Bone;
  restLocal: Quaternion;
  /**
   * Change of basis from the canonical bone frame to this bone's own frame.
   * Joint angles are transferred through it, so a canonical elbow flexion
   * becomes an elbow flexion on the target however its bones are oriented.
   */
  correction: Quaternion;
}

export interface RetargetBinding {
  character: TargetCharacter;
  mapping: BoneMapping;
  bones: BoundBone[];
  hips: Bone | null;
  hipsRest: Vector3;
  /** Target height divided by the canonical rig's height. */
  scale: number;
}

/**
 * Work out, once, how each of the character's bones relates to ours.
 *
 * Transferring a world-space rotation only works when both rigs share a rest
 * pose — do it to a T-posed import of an A-posed animation and elbow flexion
 * arrives as a forearm twist. So each target bone gets its own anatomical frame
 * built the same way ours are (+Y along the bone, +Z forward), and joint angles
 * are carried through the difference between the two frames. An elbow then
 * flexes by the same number of degrees whatever pose the character was
 * modelled in.
 */
export function bindRetarget(
  character: TargetCharacter,
  mapping: BoneMapping,
  rig: Skeleton = canonicalSkeleton,
): RetargetBinding {
  const forward = detectForward(character, mapping);
  const bones: BoundBone[] = [];

  for (const rigBone of rig.bones) {
    const targetName = mapping.bones[rigBone.name];
    if (!targetName) continue;
    const bone = character.bones.get(targetName);
    const head = character.restWorldPosition.get(targetName);
    const restWorld = character.restWorld.get(targetName);
    if (!bone || !head || !restWorld) continue;

    const tail = restTail(rigBone.name, character, mapping, rig, head);
    if (!tail) continue;

    const targetFrame = boneFrame(head, tail, forward);
    bones.push({
      canonical: rigBone.name,
      bone,
      restLocal: bone.quaternion.clone(),
      correction: restWorld.clone().invert().multiply(targetFrame),
    });
  }

  const hipsName = mapping.bones.pelvis;
  const hips = hipsName ? character.bones.get(hipsName) ?? null : null;
  const hipsRest =
    (hipsName && character.restWorldPosition.get(hipsName)?.clone()) || new Vector3();

  return {
    character,
    mapping,
    bones,
    hips,
    hipsRest,
    scale: character.height / RIG_HEIGHT,
  };
}

const scratchEuler = new Euler(0, 0, 0, EULER_ORDER);
const scratchRotation = new Quaternion();
const scratchConjugate = new Quaternion();

/**
 * Apply a canonical pose to a bound character. The pose is read directly — no
 * forward kinematics needed, because every rotation is already expressed in the
 * joint's own frame.
 */
export function applyRetarget(binding: RetargetBinding, pose: Pose): void {
  for (const entry of binding.bones) {
    const rotation = pose.rotations[entry.canonical];
    scratchEuler.set(rotation?.x ?? 0, rotation?.y ?? 0, rotation?.z ?? 0, EULER_ORDER);
    scratchRotation.setFromEuler(scratchEuler);

    // correction · rotation · correction⁻¹ re-expresses the joint angle in the
    // target bone's own basis.
    scratchConjugate.copy(entry.correction).multiply(scratchRotation);
    scratchConjugate.multiply(scratchRotation.copy(entry.correction).invert());
    entry.bone.quaternion.copy(entry.restLocal).multiply(scratchConjugate);
  }

  if (binding.hips) {
    // Root motion scales with the character, so a taller model squats to the
    // same depth relative to its own legs rather than sinking into the floor.
    binding.hips.position.set(
      binding.hipsRest.x + pose.rootPosition.x * binding.scale,
      binding.hipsRest.y + pose.rootPosition.y * binding.scale,
      binding.hipsRest.z + pose.rootPosition.z * binding.scale,
    );
  }

  binding.character.root.updateMatrixWorld(true);
}

/**
 * The far end of a target bone at rest, taken from whichever bone our own rig
 * says comes next. Using our topology rather than the character's avoids being
 * confused by twist bones and other rig-specific extras.
 */
function restTail(
  canonical: BoneName,
  character: TargetCharacter,
  mapping: BoneMapping,
  rig: Skeleton,
  head: Vector3,
): Vector3 | null {
  const rigBone = rig.bone(canonical);
  for (const childName of rigBone.children) {
    const mapped = mapping.bones[childName];
    const position = mapped ? character.restWorldPosition.get(mapped) : undefined;
    if (position && position.distanceTo(head) > 1e-4) return position;
  }

  // A leaf, or a bone whose children are unmapped: follow the character's own
  // hierarchy, and failing that extend along the canonical bone's direction.
  const targetName = mapping.bones[canonical];
  const bone = targetName ? character.bones.get(targetName) : undefined;
  for (const child of bone?.children ?? []) {
    const position = character.restWorldPosition.get(child.name);
    if (position && position.distanceTo(head) > 1e-4) return position;
  }

  const direction = rigBone.restTail.clone().sub(rigBone.restHead);
  if (direction.lengthSq() < 1e-9) return null;
  return head.clone().add(direction);
}

/**
 * Which way the character faces, taken from its feet. A model exported facing
 * away from us would otherwise get every flexion angle backwards.
 */
function detectForward(character: TargetCharacter, mapping: BoneMapping): Vector3 {
  const forward = new Vector3(0, 0, 1);
  const pairs: [BoneName, BoneName][] = [
    ['foot_l', 'toe_l'],
    ['foot_r', 'toe_r'],
  ];
  const direction = new Vector3();
  let found = 0;

  for (const [footName, toeName] of pairs) {
    const foot = mapping.bones[footName] && character.restWorldPosition.get(mapping.bones[footName]!);
    const toe = mapping.bones[toeName] && character.restWorldPosition.get(mapping.bones[toeName]!);
    if (!foot || !toe) continue;
    direction.add(toe).sub(foot);
    found += 1;
  }

  if (found === 0) return forward;
  direction.y = 0;
  if (direction.lengthSq() < 1e-6) return forward;
  return direction.normalize();
}

/** Read a loaded GLB scene into the structure the retargeter works with. */
export function readCharacter(root: Object3D): TargetCharacter {
  const bones = new Map<string, Bone>();
  const meshes: SkinnedMesh[] = [];
  const boneNames: string[] = [];

  root.updateMatrixWorld(true);
  root.traverse((object) => {
    if ((object as Bone).isBone) {
      bones.set(object.name, object as Bone);
      boneNames.push(object.name);
    }
    if ((object as SkinnedMesh).isSkinnedMesh) meshes.push(object as SkinnedMesh);
  });

  const restWorld = new Map<string, Quaternion>();
  const restLocal = new Map<string, Quaternion>();
  const restWorldPosition = new Map<string, Vector3>();
  for (const [name, bone] of bones) {
    restWorld.set(name, bone.getWorldQuaternion(new Quaternion()));
    restLocal.set(name, bone.quaternion.clone());
    restWorldPosition.set(name, new Vector3().setFromMatrixPosition(bone.matrixWorld));
  }

  const box = new Box3().setFromObject(root);
  const height = Math.max(0.5, box.max.y - box.min.y);

  return { root, bones, boneNames, restWorld, restLocal, restWorldPosition, height, meshes };
}

/** Put a character back into the rest pose it was imported in. */
export function resetCharacter(character: TargetCharacter): void {
  for (const [name, bone] of character.bones) {
    const rest = character.restLocal.get(name);
    if (rest) bone.quaternion.copy(rest);
  }
  character.root.updateMatrixWorld(true);
}
