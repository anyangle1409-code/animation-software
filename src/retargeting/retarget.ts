import {
  measureCharacterObjectHeight,
  type CharacterBone as Bone,
  type CharacterObject3D as Object3D,
  type CharacterSkinnedMesh as SkinnedMesh,
} from '../character/bones';
import { HgMat4, HgQuat, HgVec3 } from '../core/linearMath';
import type { BoneName } from '../rig/boneNames';
import { isMetacarpal } from '../rig/boneNames';
import { boneFrame, canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import type { Skeleton } from '../rig/skeleton';
import type { Pose } from '../rig/types';
import { RIG_HEIGHT } from '../rig/humanoid';
import type { BoneMapping } from './boneMap';

/** A character imported from a GLB, measured once at load time. */
export interface TargetCharacter {
  root: Object3D;
  bones: Map<string, Bone>;
  boneNames: string[];
  /** World position and rotation of each bone in the character's rest pose. */
  restWorldPosition: Map<string, HgVec3>;
  restWorld: Map<string, HgQuat>;
  restLocal: Map<string, HgQuat>;
  restPosition: Map<string, HgVec3>;
  height: number;
  meshes: SkinnedMesh[];
}

interface BoundBone {
  canonical: BoneName;
  bone: Bone;
  restLocal: HgQuat;
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
  correction: HgQuat;
}

export interface RetargetBinding {
  character: TargetCharacter;
  mapping: BoneMapping;
  bones: BoundBone[];
  hips: Bone | null;
  hipsRest: HgVec3;
  /** Scene transform when rest-world measurements were captured. */
  restRootWorld: HgMat4;
  /** Target height divided by the canonical rig's height. */
  scale: number;
  /** Canonical forward kinematics reused for every transferred frame. */
  evaluation: PoseEvaluation;
  /** Rotate canonical world frames into the direction the imported character faces. */
  worldAlignment: HgQuat;
  mirrorSides: boolean;
  /**
   * Per side, the turn from the hand frame this binding used before mirrored
   * characters' palm roll was reflected to the frame it uses now: the identity
   * on a same-side character, and a 5.5° turn about the hand's own axis on a
   * mirrored one. Offsets measured against the old frame — a delivered asset's
   * embedded grip metadata — are brought into the new one by it, so what they
   * describe on the mesh (a fist's centre, a palm's contact point) stays put.
   */
  legacyHandFrame: Record<'l' | 'r', HgQuat>;
  /** Virtual attachments drive disconnected exported branches without rebinding. */
  attachments: Map<Bone, { parent: Bone; offset: HgVec3 }>;
  followers: { bone: Bone; parent: Bone; offset: HgMat4 }[];
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
  restLocal: HgQuat;
  /** The helper's own long axis, in its local frame. */
  axis: HgVec3;
  /** Distal-relative-to-proximal orientation in the bind pose. */
  restRelative: HgQuat;
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

const WORLD_FORWARD = new HgVec3(0, 0, 1);

interface QuaternionComponents {
  x: number;
  y: number;
  z: number;
  w: number;
}

function copyQuaternionComponents(
  target: HgQuat,
  source: QuaternionComponents,
): HgQuat {
  return target.set(source.x, source.y, source.z, source.w);
}

function sceneQuaternion(source: QuaternionComponents): HgQuat {
  return copyQuaternionComponents(new HgQuat(), source);
}

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
  requested: BoneMapping,
  rig: Skeleton = canonicalSkeleton,
): RetargetBinding {
  const mapping = plausiblePalms(character, requested);
  const forward = detectForward(character, mapping);
  const bones: BoundBone[] = [];
  // Whether this character's left is on the rig's right. Every canonical frame
  // is reflected into it at runtime (applyRetarget), so any rig-space rotation
  // built into a correction here has to be reflected the same way — see the
  // palm roll below. Known from the thighs and the facing alone, before any
  // bone is bound.
  const left = mapping.bones.thigh_l && character.restWorldPosition.get(mapping.bones.thigh_l);
  const right = mapping.bones.thigh_r && character.restWorldPosition.get(mapping.bones.thigh_r);
  const alignedRight = new HgVec3(1, 0, 0).applyQuaternion(new HgQuat().setFromUnitVectors(WORLD_FORWARD, forward));
  const mirrorSides = !!(left && right && left.clone().sub(right).dot(alignedRight) > 0);
  const legacyHandFrame = { l: new HgQuat(), r: new HgQuat() };

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
        // The roll from the rig's knuckle-plane frame to its anatomical frame:
        // a turn of 2.7-4.3° about the bone's own axis. It is a rig-space
        // rotation, so on a mirrored character it must be reflected like every
        // other canonical frame is at runtime — a turn about the bone axis
        // reverses under reflection. Applied unreflected it rolled a mirrored
        // character's hands and fingers by twice the angle: the knuckle fan sat
        // 5.5° off (8.6° for the thumb base), against 0.5° same-side.
        const roll = rigPalmFrame.invert().multiply(rigBone.restWorldQuaternion);
        const unreflected = roll.clone();
        if (mirrorSides) {
          roll.y *= -1;
          roll.z *= -1;
        }
        targetFrame = boneFrame(head, tail, width).multiply(roll);
        if (rigBone.name === `hand_${side}`) copyQuaternionComponents(legacyHandFrame[side], roll).invert().multiply(sceneQuaternion(unreflected));
      }
    }
    bones.push({
      canonical: rigBone.name,
      bone,
      restLocal: new HgQuat().copy(bone.quaternion),
      correction: restWorld.clone().invert().multiply(sceneQuaternion(targetFrame)),
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
    const axis = new HgVec3()
      .setFromMatrixPosition(childBone.matrixWorld)
      .applyMatrix4(new HgMat4().copy(helper.matrixWorld).invert());
    if (axis.lengthSq() < 1e-12) continue;
    const proximalRest = character.restWorld.get(parentName);
    const distalRest = character.restWorld.get(childName);
    if (!proximalRest || !distalRest) continue;
    twistHelpers.push({
      bone: helper,
      proximal,
      distal,
      restLocal: new HgQuat().copy(helper.quaternion),
      axis: axis.normalize(),
      restRelative: proximalRest.clone().invert().multiply(distalRest),
      fraction: FOREARM_TWIST_SHARE,
    });
  }

  const hipsName = mapping.bones.pelvis;
  const hips = hipsName ? character.bones.get(hipsName) ?? null : null;
  const hipsRest =
    (hipsName && character.restWorldPosition.get(hipsName)?.clone()) || new HgVec3();

  // Some deform-only exports omit Rigify constraints: thighs, shoulders and
  // upper arms then become armature siblings, as do face bones. Reconstruct
  // only their runtime attachment, retaining the exported hierarchy/bind data.
  const attachments = new Map<Bone, { parent: Bone; offset: HgVec3 }>();
  const byCanonical = new Map(bones.map(b => [b.canonical, b]));
  const hasAncestor = (bone: Bone, parent: Bone) => {
    let walk = bone.parent;
    while (walk) { if (walk === parent) return true; walk = walk.parent; }
    return false;
  };
  for (const entry of bones) {
    // The nearest *mapped* canonical ancestor, not merely the parent: a bone
    // the character lacks — the scapula, between the clavicle and the upper
    // arm — must not cut the arm loose from the shoulder it hangs from.
    let parentName = rig.bone(entry.canonical).parent;
    while (parentName && !byCanonical.has(parentName)) parentName = rig.bone(parentName).parent;
    const parent = parentName ? byCanonical.get(parentName)?.bone : undefined;
    if (parent && !hasAncestor(entry.bone, parent)) {
      attachments.set(entry.bone, {
        parent,
        offset: character.restWorldPosition.get(entry.bone.name)!.clone()
          .applyMatrix4(new HgMat4().copy(parent.matrixWorld).invert()),
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
    followers.push({
      bone,
      parent,
      offset: new HgMat4().copy(parent.matrixWorld).invert().multiply(bone.matrixWorld),
    });
  }

  // Metacarpals ride the hand. Their frames are taken from the target hand's
  // own frame and the canonical rig's hand-to-metacarpal rest rotation, not
  // from the target palm bone's direction, so at rest a mapped palm bone sits
  // exactly where riding its hand would put it, and a metacarpal's motion
  // arrives as rotation relative to the hand. Transferring them absolutely,
  // like a limb, would turn every palm bone by however far the character's
  // knuckle fan differs from the rig's the moment the hand is driven at all.
  const byCanonicalBound = new Map(bones.map((entry) => [entry.canonical, entry]));
  for (const entry of bones) {
    if (!isMetacarpal(entry.canonical)) continue;
    const hand = byCanonicalBound.get(`hand_${entry.canonical.slice(-1)}` as BoneName);
    const restWorld = character.restWorld.get(entry.bone.name);
    if (!hand || !restWorld) continue;
    const handRest = character.restWorld.get(hand.bone.name)!;
    const handFrame = handRest.clone().multiply(hand.correction);
    const relative = rig.bone(`hand_${entry.canonical.slice(-1)}` as BoneName).restWorldQuaternion.clone()
      .invert()
      .multiply(rig.bone(entry.canonical).restWorldQuaternion);
    // The same reflection applyRetarget gives every canonical frame.
    if (mirrorSides) {
      relative.y *= -1;
      relative.z *= -1;
    }
    entry.correction.copy(restWorld.clone().invert().multiply(handFrame.multiply(sceneQuaternion(relative))));
  }

  return {
    character,
    mapping,
    bones,
    hips,
    hipsRest,
    restRootWorld: new HgMat4().copy(character.root.matrixWorld),
    attachments, followers, twistHelpers, mirrorSides, legacyHandFrame,
    scale: character.height / RIG_HEIGHT,
    evaluation: new PoseEvaluation(rig),
    worldAlignment: new HgQuat().setFromUnitVectors(WORLD_FORWARD, forward),
  };
}

const scratchDesiredFrame = new HgQuat();
const scratchDesiredWorld = new HgQuat();
const scratchParentWorld = new HgQuat();
const scratchLocal = new HgQuat();
const scratchInverseCorrection = new HgQuat();
const scratchTwistFrame = new HgQuat();
const scratchTwistCorrection = new HgQuat();
const scratchTwistDelta = new HgQuat();
const scratchTwistRest = new HgQuat();
const scratchTwistShare = new HgQuat();
const scratchTwistApplied = new HgQuat();
const scratchTwistVector = new HgVec3();
const scratchFollowerPosition = new HgVec3();
const scratchFollowerRotation = new HgQuat();
const scratchFollowerScale = new HgVec3();

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
  rootOffset = new HgVec3(),
): void {
  binding.evaluation.apply(pose);

  binding.character.root.updateMatrixWorld(true);
  const sceneDelta = new HgMat4()
    .copy(binding.character.root.matrixWorld)
    .multiply(binding.restRootWorld.clone().invert());
  const sceneRotation = new HgQuat().setFromRotationMatrix(
    new HgMat4().extractRotation(sceneDelta),
  );
  let hipsPosition: HgVec3 | null = null;
  // Rotate the resting pelvis about the scene origin before adding root motion.
  if (binding.hips) {
    const rootRotation = new HgQuat().setFromEulerXZY(
      pose.rootRotation.x,
      pose.rootRotation.y,
      pose.rootRotation.z,
    );
    if (binding.mirrorSides) { rootRotation.y *= -1; rootRotation.z *= -1; }
    rootRotation.premultiply(binding.worldAlignment).multiply(binding.worldAlignment.clone().invert());
    const origin = new HgVec3().setFromMatrixPosition(binding.restRootWorld);
    hipsPosition = binding.hipsRest.clone().sub(origin).applyQuaternion(rootRotation).add(origin).add(new HgVec3(
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
    copyQuaternionComponents(scratchDesiredFrame, binding.evaluation.quaternion(entry.canonical));
    // S R S reflects a rotation into an opposite side convention while keeping
    // a proper right-handed bone frame. Geometry itself is never reflected.
    if (binding.mirrorSides) {
      scratchDesiredFrame.y *= -1;
      scratchDesiredFrame.z *= -1;
    }
    scratchDesiredFrame.premultiply(binding.worldAlignment).premultiply(sceneRotation);
    if (entry.bone === binding.hips && hipsPosition) {
      if (entry.bone.parent) {
        hipsPosition.applyMatrix4(new HgMat4().copy(entry.bone.parent.matrixWorld).invert());
      }
      entry.bone.position.set(hipsPosition.x, hipsPosition.y, hipsPosition.z);
    }
    const attachment = binding.attachments.get(entry.bone);
    if (attachment && entry.bone !== binding.hips) {
      const position = attachment.offset.clone().applyMatrix4(attachment.parent.matrixWorld);
      if (entry.bone.parent) {
        position.applyMatrix4(new HgMat4().copy(entry.bone.parent.matrixWorld).invert());
      }
      entry.bone.position.set(position.x, position.y, position.z);
    }
    scratchDesiredWorld
      .copy(scratchDesiredFrame)
      .multiply(scratchInverseCorrection.copy(entry.correction).invert());

    if (entry.bone.parent) {
      scratchParentWorld.setFromRotationMatrix(
        new HgMat4().extractRotation(entry.bone.parent.matrixWorld),
      );
      scratchLocal
        .copy(scratchParentWorld)
        .invert()
        .multiply(scratchDesiredWorld);
    } else {
      scratchLocal.copy(scratchDesiredWorld);
    }

    entry.bone.quaternion.set(
      scratchLocal.x,
      scratchLocal.y,
      scratchLocal.z,
      scratchLocal.w,
    );
    entry.bone.updateMatrixWorld(true);

    // Hand a share of this chain's axial twist to its deform helper, before the
    // distal bone is driven. The distal bone's world orientation is set
    // absolutely a few iterations later, against whatever its parent has become,
    // so this winds the surface between them without moving the hand.
    for (const helper of binding.twistHelpers) {
      if (helper.proximal !== entry.canonical) continue;
      const distal = byCanonicalEntry.get(helper.distal);
      if (!distal) continue;
      copyQuaternionComponents(scratchTwistFrame, binding.evaluation.quaternion(distal.canonical));
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
      scratchTwistApplied
        .copy(helper.restLocal)
        .multiply(scratchTwistShare.setFromAxisAngle(helper.axis, wrapped * helper.fraction));
      helper.bone.quaternion.set(
        scratchTwistApplied.x,
        scratchTwistApplied.y,
        scratchTwistApplied.z,
        scratchTwistApplied.w,
      );
      helper.bone.updateMatrixWorld(true);
    }
  }

  for (const follower of binding.followers) {
    const world = new HgMat4().copy(follower.parent.matrixWorld).multiply(follower.offset);
    const local = follower.bone.parent
      ? new HgMat4().copy(follower.bone.parent.matrixWorld).invert().multiply(world)
      : world;
    // These are rigid attachments; preserve the source bone's authored scale.
    local.decompose(
      scratchFollowerPosition,
      scratchFollowerRotation,
      scratchFollowerScale,
    );
    follower.bone.position.set(
      scratchFollowerPosition.x,
      scratchFollowerPosition.y,
      scratchFollowerPosition.z,
    );
    follower.bone.quaternion.set(
      scratchFollowerRotation.x,
      scratchFollowerRotation.y,
      scratchFollowerRotation.z,
      scratchFollowerRotation.w,
    );
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
): HgVec3 | null {
  const side = canonical.endsWith('_l') ? 'l' : 'r';
  const roots = [`index_01_${side}`, `middle_01_${side}`, `ring_01_${side}`, `pinky_01_${side}`] as BoneName[];
  const positions: HgVec3[] = [];

  for (const root of roots) {
    const mapped = mapping.bones[root];
    const position = mapped ? character.restWorldPosition.get(mapped) : undefined;
    if (position) positions.push(position);
  }

  if (positions.length < 2) return null;
  const average = new HgVec3();
  for (const position of positions) average.add(position);
  return average.multiplyScalar(1 / positions.length);
}

/**
 * A mapping with any palm bone that cannot be a metacarpal left out.
 *
 * A metacarpal runs from the carpus to its finger's knuckle, so its base lies
 * inside the hand: no further from the knuckle than the wrist is, and along
 * roughly the same line. The production character's `DEF-palm` bones fail
 * both by a wide margin — each sits 207-213 mm from its knuckle, half as far
 * again as the wrist, and 99-146 mm behind it — because its export kept the
 * joints and lost their placement. Driven, such a joint would swing its
 * finger's root through an arc 20 cm across. Unmapped, the finger simply
 * hangs from the hand, as it does on a character with no palm bones at all.
 */
export function plausiblePalms(character: TargetCharacter, mapping: BoneMapping): BoneMapping {
  let result = mapping;
  for (const [canonical, target] of Object.entries(mapping.bones) as [BoneName, string][]) {
    if (!target || !isMetacarpal(canonical)) continue;
    const side = canonical.slice(-1);
    const finger = canonical.slice('metacarpal_'.length, -2);
    const handName = mapping.bones[`hand_${side}` as BoneName];
    const rootName = mapping.bones[`${finger}_01_${side}` as BoneName];
    const base = character.restWorldPosition.get(target);
    const wrist = handName ? character.restWorldPosition.get(handName) : undefined;
    const knuckle = rootName ? character.restWorldPosition.get(rootName) : undefined;
    const plausible =
      !!base && !!wrist && !!knuckle &&
      base.distanceTo(knuckle) <= wrist.distanceTo(knuckle) * 1.05 &&
      knuckle.clone().sub(base).angleTo(knuckle.clone().sub(wrist)) <= (30 * Math.PI) / 180;
    if (plausible) continue;
    if (result === mapping) result = { ...mapping, bones: { ...mapping.bones } };
    delete result.bones[canonical];
  }
  return result;
}

/**
 * The nearest mapped canonical descendant's rest position, searching through
 * unmapped bones depth-first in canonical child order.
 */
function mappedDescendant(
  children: readonly BoneName[],
  character: TargetCharacter,
  mapping: BoneMapping,
  rig: Skeleton,
  head: HgVec3,
): HgVec3 | null {
  for (const childName of children) {
    if (mapping.bones[childName]) continue;
    const grandchildren = rig.bone(childName).children;
    for (const grandchild of grandchildren) {
      const mapped = mapping.bones[grandchild];
      const position = mapped ? character.restWorldPosition.get(mapped) : undefined;
      if (position && position.distanceTo(head) > 1e-4) return position;
    }
    const deeper = mappedDescendant(grandchildren, character, mapping, rig, head);
    if (deeper) return deeper;
  }
  return null;
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
  head: HgVec3,
): HgVec3 | null {
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

  // No direct child is mapped: look through the unmapped ones to the nearest
  // mapped descendant. This is what lets the canonical rig carry bones a
  // character does not have. The clavicle's only canonical child is the
  // scapula, which no imported character maps, so without this the clavicle
  // would lose the upper arm that defines its shaft and fall back to whatever
  // the character's own export says — on the production character, a 6.75°
  // different frame. Direct children are still tried first, above, so a bone
  // whose children are mapped resolves exactly as it always did.
  const descendant = mappedDescendant(rigBone.children, character, mapping, rig, head);
  if (descendant) return descendant;

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
    return head.clone().add(new HgVec3(0, 0.05, 0).applyQuaternion(orientation));
  }
  const direction = rigBone.restTail.clone().sub(rigBone.restHead);
  if (direction.lengthSq() < 1e-9) return null;
  return head.clone().add(direction);
}

/**
 * Which way the character faces, taken from its feet. A model exported facing
 * away from us would otherwise get every flexion angle backwards.
 */
function detectForward(character: TargetCharacter, mapping: BoneMapping): HgVec3 {
  const forward = new HgVec3(0, 0, 1);
  const pairs: [BoneName, BoneName][] = [
    ['foot_l', 'toe_l'],
    ['foot_r', 'toe_r'],
  ];
  const direction = new HgVec3();
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

  const restWorld = new Map<string, HgQuat>();
  const restLocal = new Map<string, HgQuat>();
  const restPosition = new Map<string, HgVec3>();
  const restWorldPosition = new Map<string, HgVec3>();
  const scratchWorldPosition = new HgVec3();
  const scratchWorldScale = new HgVec3();
  for (const [name, bone] of bones) {
    const world = new HgMat4().copy(bone.matrixWorld);
    const worldRotation = new HgQuat();
    world.decompose(scratchWorldPosition, worldRotation, scratchWorldScale);
    restWorld.set(name, worldRotation);
    restLocal.set(name, new HgQuat().copy(bone.quaternion));
    restPosition.set(name, new HgVec3().copy(bone.position));
    restWorldPosition.set(name, new HgVec3().setFromMatrixPosition(bone.matrixWorld));
  }

  const height = measureCharacterObjectHeight(root);

  return { root, bones, boneNames, restWorld, restLocal, restPosition, restWorldPosition, height, meshes };
}

/** Put a character back into the rest pose it was imported in. */
export function resetCharacter(character: TargetCharacter): void {
  for (const [name, bone] of character.bones) {
    const rest = character.restLocal.get(name);
    if (rest) bone.quaternion.set(rest.x, rest.y, rest.z, rest.w);
    const position = character.restPosition.get(name);
    if (position) bone.position.set(position.x, position.y, position.z);
  }
  character.root.updateMatrixWorld(true);
}
