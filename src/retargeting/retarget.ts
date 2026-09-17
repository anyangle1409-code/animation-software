import { Box3, Euler, Matrix4, Object3D, Quaternion, Vector3 } from 'three';
import type { Bone, SkinnedMesh } from 'three';
import type { BoneName } from '../rig/boneNames';
import { boneFrame, canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import type { Skeleton } from '../rig/skeleton';
import { EULER_ORDER } from '../rig/types';
import type { Pose } from '../rig/types';
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
  restPosition: Map<string, Vector3>;
  height: number;
  meshes: SkinnedMesh[];
}

interface BoundBone {
  canonical: BoneName;
  bone: Bone;
  restLocal: Quaternion;
  /**
   * Change of basis from the target bone's authored frame to its anatomical
   * frame. In the rest pose: actualWorld * correction = anatomicalFrame.
   *
   * That relation is kept when posing: the canonical rig supplies the desired
   * anatomical frame in world space, then correction^-1 takes it back into the
   * source bone's own authored basis. This is what lets an A-posed/open-hand
   * character reproduce an arms-down/closed-hand canonical pose absolutely,
   * instead of merely adding deltas to whatever rest pose the asset shipped in.
   */
  correction: Quaternion;
}

export interface RetargetBinding {
  character: TargetCharacter;
  mapping: BoneMapping;
  bones: BoundBone[];
  hips: Bone | null;
  hipsRest: Vector3;
  /** Scene transform when rest-world measurements were captured. */
  restRootWorld: Matrix4;
  /** Target height divided by the canonical rig's height. */
  scale: number;
  /** Canonical forward kinematics reused for every transferred frame. */
  evaluation: PoseEvaluation;
  /** Rotate canonical world frames into the direction the imported character faces. */
  worldAlignment: Quaternion;
  mirrorSides: boolean;
  /** Virtual attachments drive disconnected exported branches without rebinding. */
  attachments: Map<Bone, { parent: Bone; offset: Vector3 }>;
  followers: { bone: Bone; parent: Bone; offset: Matrix4 }[];
  /**
   * Deform twist helpers that must carry a share of their chain's axial twist.
   *
   * A Rigify deform forearm is two bones so that pronation winds gradually from
   * elbow to wrist. A connected helper otherwise just rides its parent, and
   * measured on the push-up that is exactly what happened: `DEF-forearmL` and
   * `DEF-forearmL001` both read 9.1 degrees of long-axis twist at the bottom
   * while the hand read 57.7, so the whole 48.6 degree step landed in the wrist
   * and the forearm surface collapsed into a flattened strap instead of winding.
   *
   * Each entry gives the helper a fraction of the axial twist between its
   * driven parent and the distal bone. The distal bone is driven afterwards in
   * canonical order and its world orientation is set absolutely, so its final
   * transform is unchanged by this — only the surface between them winds.
   */
  twistHelpers: TwistHelper[];
}

export interface TwistHelper {
  bone: Bone;
  /** The driven bone above it, whose twist it shares. */
  proximal: BoneName;
  /** The driven bone below it, which defines the twist to share. */
  distal: BoneName;
  /** Authored local rotation, which the share is composed onto. */
  restLocal: Quaternion;
  /** The helper's own long axis, in its local frame. */
  axis: Vector3;
  /** Distal-relative-to-proximal orientation in the bind pose. */
  restRelative: Quaternion;
  fraction: number;
}

/**
 * How much of the forearm's axial twist its deform helper carries.
 *
 * Swept at 0.25, 0.50 and 0.75. The helper's measured twist scales linearly
 * with it (15.0, 21.0, 26.9 degrees at push-up Bottom against 9.1 on the
 * proximal bone) and the hand's final orientation is 57.7 degrees in every
 * case, so the choice is about the gradient alone.
 *
 * 0.5 is retained: it is the anatomical convention for a two-bone deform
 * forearm, and it measurably improves the distal taper toward the bind profile
 * (the outer girth bins go 35.6 and 30.5 mm at share 0 to 37.4 and 32.9 mm,
 * against 33.5 mm in the bind pose) without the larger deviation 0.75 adds.
 */
export const FOREARM_TWIST_SHARE = 0.5;

/** Recognised Rigify detail branches whose constraints are absent in glTF. */
function detailParent(name: string): BoneName | null {
  if (/^DEF[-_](?:jaw|chin|lip|tongue|teeth|nose|cheek|brow|forehead|lid|eye|ear|temple)/i.test(name)) return 'head';
  if (/^DEF[-_]breast/i.test(name)) return 'spine_03';
  if (/^DEF[-_]pelvis/i.test(name)) return 'pelvis';
  return null;
}

const WORLD_FORWARD = new Vector3(0, 0, 1);

/**
 * Work out, once, how each of the character's bones relates to ours.
 *
 * Each target bone gets an anatomical frame built the same way as the canonical
 * rig (+Y along the bone, +Z forward). The binding remembers how that frame
 * relates to the bone's authored frame. At runtime we transfer the canonical
 * *world anatomical frame* onto the target, not a rotation delta from the
 * target's rest pose. That distinction matters for real assets: an A-posed arm
 * must come down when the exercise says the arm is down, and an open/spread
 * rest hand must still close when the exercise asks for a grip.
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

    let targetFrame = boneFrame(head, tail, forward);
    // Hands can be rolled relative to the body's forward axis in the authored
    // rest pose. Knuckle spread supplies their actual palm plane.
    if (/^(hand|thumb|index|middle|ring|pinky)_/.test(rigBone.name)) {
      const side = rigBone.name.endsWith('_l') ? 'l' : 'r';
      const index = mapping.bones[`index_01_${side}`];
      const pinky = mapping.bones[`pinky_01_${side}`];
      const indexPosition = index && character.restWorldPosition.get(index);
      const pinkyPosition = pinky && character.restWorldPosition.get(pinky);
      if (indexPosition && pinkyPosition && indexPosition.distanceTo(pinkyPosition) > 1e-4) {
        const width = indexPosition.clone().sub(pinkyPosition);
        const rigWidth = rig.bone(`index_01_${side}`).restHead.clone()
          .sub(rig.bone(`pinky_01_${side}`).restHead);
        const rigPalmFrame = boneFrame(rigBone.restHead, rigBone.restTail, rigWidth);
        targetFrame = boneFrame(head, tail, width)
          .multiply(rigPalmFrame.invert()).multiply(rigBone.restWorldQuaternion);
      }
    }
    bones.push({
      canonical: rigBone.name,
      bone,
      restLocal: bone.quaternion.clone(),
      correction: restWorld.clone().invert().multiply(targetFrame),
    });
  }

  // Twist helpers: a source bone sitting between a driven bone and its driven
  // child, which the export leaves as a passive rider. Only the forearm is
  // wired up — the upper arm has one too, but nothing measured requires it, and
  // the decision is explicit that this stays evidence-driven.
  const twistHelpers: TwistHelper[] = [];
  for (const side of ['l', 'r'] as const) {
    const proximal = `forearm_${side}` as BoneName;
    const distal = `hand_${side}` as BoneName;
    const parentName = mapping.bones[proximal];
    const childName = mapping.bones[distal];
    if (!parentName || !childName) continue;
    const parentBone = character.bones.get(parentName);
    const childBone = character.bones.get(childName);
    if (!parentBone || !childBone) continue;
    // The helper is the child's parent, when that is not the driven bone itself.
    const helper = childBone.parent as Bone | null;
    if (!helper || helper === parentBone || helper.parent !== parentBone) continue;
    parentBone.updateWorldMatrix(true, true);
    const axis = childBone.getWorldPosition(new Vector3());
    helper.worldToLocal(axis);
    if (axis.lengthSq() < 1e-12) continue;
    const proximalRest = character.restWorld.get(parentName);
    const distalRest = character.restWorld.get(childName);
    if (!proximalRest || !distalRest) continue;
    twistHelpers.push({
      bone: helper,
      proximal,
      distal,
      restLocal: helper.quaternion.clone(),
      axis: axis.normalize(),
      restRelative: proximalRest.clone().invert().multiply(distalRest),
      fraction: FOREARM_TWIST_SHARE,
    });
  }

  const hipsName = mapping.bones.pelvis;
  const hips = hipsName ? character.bones.get(hipsName) ?? null : null;
  const hipsRest =
    (hipsName && character.restWorldPosition.get(hipsName)?.clone()) || new Vector3();

  // Some deform-only exports omit Rigify constraints: thighs, shoulders and
  // upper arms then become armature siblings, as do face bones. Reconstruct
  // only their runtime attachment, retaining the exported hierarchy/bind data.
  const attachments = new Map<Bone, { parent: Bone; offset: Vector3 }>();
  const byCanonical = new Map(bones.map(b => [b.canonical, b]));
  const hasAncestor = (bone: Bone, parent: Bone) => {
    let walk = bone.parent;
    while (walk) { if (walk === parent) return true; walk = walk.parent; }
    return false;
  };
  for (const entry of bones) {
    const parentName = rig.bone(entry.canonical).parent;
    const parent = parentName ? byCanonical.get(parentName)?.bone : undefined;
    if (parent && !hasAncestor(entry.bone, parent)) {
      attachments.set(entry.bone, {
        parent,
        offset: character.restWorldPosition.get(entry.bone.name)!.clone()
          .applyMatrix4(parent.matrixWorld.clone().invert()),
      });
    }
  }
  const followers: RetargetBinding['followers'] = [];
  const mapped = new Set(bones.map(b => b.bone));
  for (const bone of character.bones.values()) {
    if (mapped.has(bone)) continue;
    const parentName = detailParent(bone.name);
    const parent = parentName ? byCanonical.get(parentName)?.bone : undefined;
    if (!parent || hasAncestor(bone, parent)) continue;
    if (followers.some(f => hasAncestor(bone, f.bone))) continue;
    followers.push({ bone, parent,
      offset: parent.matrixWorld.clone().invert().multiply(bone.matrixWorld) });
  }
  const left = mapping.bones.thigh_l && character.restWorldPosition.get(mapping.bones.thigh_l);
  const right = mapping.bones.thigh_r && character.restWorldPosition.get(mapping.bones.thigh_r);
  const alignedRight = new Vector3(1, 0, 0).applyQuaternion(new Quaternion().setFromUnitVectors(WORLD_FORWARD, forward));
  const mirrorSides = !!(left && right && left.clone().sub(right).dot(alignedRight) > 0);

  return {
    character,
    mapping,
    bones,
    hips,
    hipsRest,
    restRootWorld: character.root.matrixWorld.clone(),
    attachments, followers, twistHelpers, mirrorSides,
    scale: character.height / RIG_HEIGHT,
    evaluation: new PoseEvaluation(rig),
    worldAlignment: new Quaternion().setFromUnitVectors(WORLD_FORWARD, forward),
  };
}

const scratchDesiredFrame = new Quaternion();
const scratchDesiredWorld = new Quaternion();
const scratchParentWorld = new Quaternion();
const scratchLocal = new Quaternion();
const scratchInverseCorrection = new Quaternion();
const scratchTwistFrame = new Quaternion();
const scratchTwistCorrection = new Quaternion();
const scratchTwistDelta = new Quaternion();
const scratchTwistRest = new Quaternion();
const scratchTwistShare = new Quaternion();
const scratchTwistVector = new Vector3();

/**
 * Apply the canonical pose as an absolute anatomical target.
 *
 * `PoseEvaluation` gives the canonical bone frame in world space. The imported
 * bone's `correction` says how its authored bone basis relates to that same
 * anatomical frame, so:
 *
 *   desiredActualWorld = desiredAnatomicalWorld * correction^-1
 *
 * We then convert that world rotation back into the target bone's local space.
 * The source hierarchy and bind data remain intact. Disconnected deform
 * branches receive local translations, and detached Rigify detail branches
 * follow their anatomical parent. Connected helper bones retain their offsets.
 */
export function applyRetarget(
  binding: RetargetBinding,
  pose: Pose,
  rootOffset = new Vector3(),
): void {
  binding.evaluation.apply(pose);

  binding.character.root.updateMatrixWorld(true);
  const sceneDelta = binding.character.root.matrixWorld.clone()
    .multiply(binding.restRootWorld.clone().invert());
  const sceneRotation = new Quaternion().setFromRotationMatrix(
    new Matrix4().extractRotation(sceneDelta),
  );
  let hipsPosition: Vector3 | null = null;
  // Rotate the resting pelvis about the scene origin before adding root motion.
  if (binding.hips) {
    const rootRotation = new Quaternion().setFromEuler(new Euler(
      pose.rootRotation.x, pose.rootRotation.y, pose.rootRotation.z, EULER_ORDER,
    ));
    if (binding.mirrorSides) { rootRotation.y *= -1; rootRotation.z *= -1; }
    rootRotation.premultiply(binding.worldAlignment).multiply(binding.worldAlignment.clone().invert());
    const origin = new Vector3().setFromMatrixPosition(binding.restRootWorld);
    hipsPosition = binding.hipsRest.clone().sub(origin).applyQuaternion(rootRotation).add(origin).add(new Vector3(
      (pose.rootPosition.x + rootOffset.x) * (binding.mirrorSides ? -1 : 1),
      pose.rootPosition.y + rootOffset.y,
      pose.rootPosition.z + rootOffset.z,
    ).multiplyScalar(binding.scale).applyQuaternion(binding.worldAlignment));
    // Account for display transforms applied after binding, once only.
    hipsPosition.applyMatrix4(sceneDelta);
  }

  // Parents must be current before a child's desired world rotation can be
  // converted to local space. `bones` follows canonical hierarchy order, and
  // updating each driven bone also refreshes passive source bones below it.
  binding.character.root.updateMatrixWorld(true);
  const byCanonicalEntry = new Map(binding.bones.map((entry) => [entry.canonical, entry]));
  for (const entry of binding.bones) {
    scratchDesiredFrame.copy(binding.evaluation.quaternion(entry.canonical));
    // S R S reflects a rotation into an opposite side convention while keeping
    // a proper right-handed bone frame. Geometry itself is never reflected.
    if (binding.mirrorSides) {
      scratchDesiredFrame.y *= -1;
      scratchDesiredFrame.z *= -1;
    }
    scratchDesiredFrame.premultiply(binding.worldAlignment).premultiply(sceneRotation);
    if (entry.bone === binding.hips && hipsPosition) {
      if (entry.bone.parent) entry.bone.parent.worldToLocal(hipsPosition);
      entry.bone.position.copy(hipsPosition);
    }
    const attachment = binding.attachments.get(entry.bone);
    if (attachment && entry.bone !== binding.hips) {
      const position = attachment.offset.clone().applyMatrix4(attachment.parent.matrixWorld);
      if (entry.bone.parent) entry.bone.parent.worldToLocal(position);
      entry.bone.position.copy(position);
    }
    scratchDesiredWorld
      .copy(scratchDesiredFrame)
      .multiply(scratchInverseCorrection.copy(entry.correction).invert());

    if (entry.bone.parent) {
      entry.bone.parent.getWorldQuaternion(scratchParentWorld);
      scratchLocal
        .copy(scratchParentWorld)
        .invert()
        .multiply(scratchDesiredWorld);
    } else {
      scratchLocal.copy(scratchDesiredWorld);
    }

    entry.bone.quaternion.copy(scratchLocal);
    entry.bone.updateMatrixWorld(true);

    // Hand a share of this chain's axial twist to its deform helper, before the
    // distal bone is driven. The distal bone's world orientation is set
    // absolutely a few iterations later, against whatever its parent has become,
    // so this winds the surface between them without moving the hand.
    for (const helper of binding.twistHelpers) {
      if (helper.proximal !== entry.canonical) continue;
      const distal = byCanonicalEntry.get(helper.distal);
      if (!distal) continue;
      scratchTwistFrame.copy(binding.evaluation.quaternion(distal.canonical));
      if (binding.mirrorSides) {
        scratchTwistFrame.y *= -1;
        scratchTwistFrame.z *= -1;
      }
      scratchTwistFrame
        .premultiply(binding.worldAlignment)
        .premultiply(sceneRotation)
        .multiply(scratchTwistCorrection.copy(distal.correction).invert());
      // The change in the distal bone's orientation relative to this one, since
      // the bind pose. Only its component about the long axis is redistributed.
      scratchTwistDelta
        .copy(scratchDesiredWorld)
        .invert()
        .multiply(scratchTwistFrame)
        .multiply(scratchTwistRest.copy(helper.restRelative).invert());
      scratchTwistVector.set(scratchTwistDelta.x, scratchTwistDelta.y, scratchTwistDelta.z);
      const along = scratchTwistVector.dot(helper.axis);
      const angle = 2 * Math.atan2(along, scratchTwistDelta.w);
      const wrapped = angle > Math.PI ? angle - 2 * Math.PI : angle <= -Math.PI ? angle + 2 * Math.PI : angle;
      helper.bone.quaternion
        .copy(helper.restLocal)
        .multiply(scratchTwistShare.setFromAxisAngle(helper.axis, wrapped * helper.fraction));
      helper.bone.updateMatrixWorld(true);
    }
  }

  for (const follower of binding.followers) {
    const world = follower.parent.matrixWorld.clone().multiply(follower.offset);
    const local = follower.bone.parent
      ? follower.bone.parent.matrixWorld.clone().invert().multiply(world) : world;
    // These are rigid attachments; preserve the source bone's authored scale.
    local.decompose(follower.bone.position, follower.bone.quaternion, new Vector3());
    follower.bone.updateMatrixWorld(true);
  }
  binding.character.root.updateMatrixWorld(true);
}

/**
 * The hand bone ends through the centre of the palm, not at the thumb root.
 * Rigify (and many other rigs) has no explicit node at that tail; its hand bone
 * fans directly into the five digits.  Averaging the four finger knuckles gives
 * a stable palm-longitudinal axis and avoids making the hand frame depend on
 * whichever child happens to be listed first (normally the thumb).
 */
function palmTail(
  canonical: 'hand_l' | 'hand_r',
  character: TargetCharacter,
  mapping: BoneMapping,
): Vector3 | null {
  const side = canonical.endsWith('_l') ? 'l' : 'r';
  const roots = [`index_01_${side}`, `middle_01_${side}`, `ring_01_${side}`, `pinky_01_${side}`] as BoneName[];
  const positions: Vector3[] = [];

  for (const root of roots) {
    const mapped = mapping.bones[root];
    const position = mapped ? character.restWorldPosition.get(mapped) : undefined;
    if (position) positions.push(position);
  }

  if (positions.length < 2) return null;
  const average = new Vector3();
  for (const position of positions) average.add(position);
  return average.multiplyScalar(1 / positions.length);
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

  if (canonical === 'hand_l' || canonical === 'hand_r') {
    const palm = palmTail(canonical, character, mapping);
    if (palm && palm.distanceTo(head) > 1e-4) return palm;
  }

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
    // Facial/accessory branches do not define the shaft of their parent bone.
    if (detailParent(child.name)) continue;
    const position = character.restWorldPosition.get(child.name);
    if (position && position.distanceTo(head) > 1e-4) return position;
  }

  // Rigify's leaf deform bones have an authored +Y shaft even though glTF
  // omits the tail. A canonical fallback points an A-posed fingertip elsewhere.
  if (bone && /^DEF[-_]/i.test(bone.name)) {
    const orientation = character.restWorld.get(bone.name)!;
    return head.clone().add(new Vector3(0, 0.05, 0).applyQuaternion(orientation));
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
  const restPosition = new Map<string, Vector3>();
  const restWorldPosition = new Map<string, Vector3>();
  for (const [name, bone] of bones) {
    restWorld.set(name, bone.getWorldQuaternion(new Quaternion()));
    restLocal.set(name, bone.quaternion.clone());
    restPosition.set(name, bone.position.clone());
    restWorldPosition.set(name, new Vector3().setFromMatrixPosition(bone.matrixWorld));
  }

  const box = new Box3().setFromObject(root);
  const height = Math.max(0.5, box.max.y - box.min.y);

  return { root, bones, boneNames, restWorld, restLocal, restPosition, restWorldPosition, height, meshes };
}

/** Put a character back into the rest pose it was imported in. */
export function resetCharacter(character: TargetCharacter): void {
  for (const [name, bone] of character.bones) {
    const rest = character.restLocal.get(name);
    if (rest) bone.quaternion.copy(rest);
    const position = character.restPosition.get(name);
    if (position) bone.position.copy(position);
  }
  character.root.updateMatrixWorld(true);
}
