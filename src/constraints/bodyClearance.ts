import { Matrix4, Vector3 } from 'three';
import type { SkinnedMesh } from 'three';
import type { StudioClip } from '../animation/clip';
import { sampleClip } from '../animation/clip';
import { resolveFrame } from '../animation/pipeline';
import { applyCharacterPose } from '../character/pose';
import { dominantBone, posedVertex } from '../character/posedMesh';
import type { CharacterBuild } from '../character';
import { equipmentParts } from '../equipment/geometry';
import { anatomicalGripOffset } from '../equipment/attach';
import { equipmentSocketForInstance } from '../equipment/library';
import { reflectPlacement } from '../equipment/mirror';
import { handAttachmentMatrix } from '../export/clipBuilder';
import { PoseEvaluation } from '../rig/skeleton';
import type { Skeleton } from '../rig/skeleton';
import { lockAnchors } from './locks';
import { equipmentPartDistances, measureClearance, PointGrid } from './collision';
import type { ClearanceSample } from './collision';

/**
 * Body clearance on the production character: equipment against the body, and
 * the arms against the trunk.
 *
 * Both measurements began life inside `exercises/equipmentClearance.test.ts` and
 * `exercises/selfCollision.test.ts`, where they could only guard the exercises
 * already in the library. A generated exercise needs the same questions asked of
 * it before anyone has written a test for it, so the measuring lives here and the
 * tests, and the generator's validation, both call it. The limits live here too,
 * so the two can never hold a candidate to a looser standard than the library.
 *
 * What is measured, and why, is documented where the numbers were first taken;
 * see the headers of those two tests.
 */

/**
 * Anything that is not a support must stay this far off the body: zero would
 * pass a plate grazing the shorts, and the tightest items in the library (the
 * curls' dumbbells, 11.46 mm and 11.68 mm) sit well clear of 2 mm.
 */
export const EQUIPMENT_MARGIN = 0.002;

/**
 * A pad the body rests on must be reached — within 3 mm — and pressed into no
 * further than flesh would flatten, 15 mm. A support's frame keeps the 2 mm
 * margin of any other equipment.
 */
export const SUPPORT_LIMITS = { resting: 0.003, compression: 0.015 };

/** The surface equipment must not reach: legs and trunk. Hands and arms grip. */
export const CLEARANCE_BODY = /^(thigh|pelvis|shin|spine|breast|neck)/i;

/**
 * Imported deform bones are named `<part><side>` with an optional numeric
 * segment suffix (`upper_armL001`), so the side is captured explicitly rather
 * than read from the last character.
 */
const ARM = /^(upper_?arm|forearm)([LR])\d*$/i;
const TRUNK = /^(spine|breast|pelvis)/i;
const armSide = (bone: string): string | null => {
  const match = ARM.exec(bone);
  return match ? match[2].toUpperCase() : null;
};

/** 30 mm cells, and eight shells of them, so the arm–trunk search reaches 240 mm. */
const CELL = 0.03;
const RINGS = 8;

/** The production body mesh within a built character. */
export function bodyMeshOf(character: CharacterBuild): SkinnedMesh | undefined {
  return (character.meshes as SkinnedMesh[]).find((mesh) => /freeman/i.test(mesh.name));
}

export interface SupportPartClearance {
  material: string;
  /** Deepest point of the body against this part, metres; negative is inside. */
  deepest: number;
  where: string;
  pass: boolean;
}

export interface ItemClearance {
  id: string;
  kind: string;
  /** A bench the body rests on, asked whether it is reached rather than avoided. */
  support: boolean;
  sample: ClearanceSample;
  /** Per part, for supports only. */
  parts: SupportPartClearance[];
  pass: boolean;
}

/**
 * Pose the character through the clip and measure every visible item against
 * its legs and trunk, as `equipmentClearance.test.ts` always has.
 */
export function measureEquipmentClearance(
  character: CharacterBuild,
  rig: Skeleton,
  clip: StudioClip,
  steps = 40,
): ItemClearance[] {
  const body = bodyMeshOf(character);
  if (!body) throw new Error('The character has no production body mesh to measure');
  const count = body.geometry.getAttribute('position').count;
  const measured = Array.from({ length: count }, (_, index) => CLEARANCE_BODY.test(dominantBone(body, index)));

  const evaluation = new PoseEvaluation(rig);
  const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
  const worst = new Map<string, ClearanceSample>();
  const placement = new Matrix4();
  const parts = new Map<string, { deepest: number; where: string }[]>();
  const local = new Vector3();

  for (let step = 0; step <= steps; step += 1) {
    const time = (step / steps) * clip.duration;
    const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
    applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
    body.skeleton.update();
    body.updateWorldMatrix(true, false);

    for (const instance of clip.equipment) {
      if (!instance.visible) continue;

      if (instance.attachment.mode === 'hand') {
        // Rigid in the hand: the item's frame follows the character's own grip,
        // not the canonical rig's.
        const side = instance.attachment.side;
        const hand = character.handMatrix?.(side, new Matrix4());
        if (!hand) continue;
        const socket = equipmentSocketForInstance(instance, instance.attachment.socket);
        const offset = instance.attachment.gripOffset ?? character.gripOffset?.(side) ?? anatomicalGripOffset(side);
        placement.multiplyMatrices(hand, handAttachmentMatrix(offset, socket?.position ?? { x: 0, y: 0, z: 0 })).invert();
      } else {
        const transform = frame.equipment.get(instance.id);
        if (!transform) continue;
        placement.compose(
          new Vector3(transform.position.x, transform.position.y, transform.position.z),
          transform.quaternion,
          // A cable is stretched along its length; its surface is then measured
          // exactly beside it, where a body would meet it.
          transform.scale ?? new Vector3(1, 1, 1),
        );
        // Placed by the rig; the character is its mirror image, so the item is
        // reflected into the character's world, as it is drawn.
        if (character.mirrored) reflectPlacement(placement, placement);
        placement.invert();
      }

      if (instance.supportsBody) {
        const record =
          parts.get(instance.id) ??
          equipmentParts(instance.kind, instance.backAngle).map(() => ({ deepest: Number.POSITIVE_INFINITY, where: '' }));
        for (let index = 0; index < count; index += 1) {
          if (!measured[index]) continue;
          posedVertex(body, index, local).applyMatrix4(placement);
          equipmentPartDistances(instance.kind, local, instance.backAngle).forEach((distance, part) => {
            if (distance < record[part].deepest) {
              record[part] = { deepest: distance, where: `${time.toFixed(2)}s, ${dominantBone(body, index)}` };
            }
          });
        }
        parts.set(instance.id, record);
      }

      const sample = worst.get(instance.id) ?? { closest: Number.POSITIVE_INFINITY, inside: 0, where: '' };
      measureClearance(
        instance.kind,
        placement,
        count,
        (index, out) => (measured[index] ? posedVertex(body, index, out) : null),
        (index) => `${instance.id} at ${time.toFixed(2)}s, against ${dominantBone(body, index)}`,
        sample,
        instance.backAngle,
      );
      worst.set(instance.id, sample);
    }
  }

  return [...worst].map(([id, sample]) => {
    const instance = clip.equipment.find((item) => item.id === id)!;
    const support = instance.supportsBody === true;
    const partResults: SupportPartClearance[] = support
      ? parts.get(id)!.map((part, index) => {
          const material = equipmentParts(instance.kind, instance.backAngle)[index].material;
          return {
            material,
            deepest: part.deepest,
            where: part.where,
            pass:
              material === 'pad'
                ? part.deepest <= SUPPORT_LIMITS.resting && part.deepest >= -SUPPORT_LIMITS.compression
                : part.deepest > EQUIPMENT_MARGIN,
          };
        })
      : [];
    return {
      id,
      kind: instance.kind,
      support,
      sample,
      parts: partResults,
      pass: support ? partResults.every((part) => part.pass) : sample.inside === 0 && sample.closest > EQUIPMENT_MARGIN,
    };
  });
}

export interface ArmTrunkSide {
  side: 'L' | 'R';
  /** Closest arm vertex to any trunk vertex, metres; infinite beyond the search. */
  closest: number;
  where: string;
  armVertices: number;
}

export interface ArmTrunkSeparation {
  trunkVertices: number;
  sides: ArmTrunkSide[];
  /** The closer side's separation, and where. */
  closest: number;
  where: string;
}

/**
 * Pose the character through the clip and find how close each arm comes to the
 * trunk. A separation, not a penetration depth: a point cloud cannot tell an arm
 * resting on the chest from one buried in it, which is why the library holds
 * each exercise against its own recorded baseline rather than a shared floor.
 */
export function measureArmTrunkSeparation(
  character: CharacterBuild,
  rig: Skeleton,
  clip: StudioClip,
  steps = 40,
): ArmTrunkSeparation {
  const body = bodyMeshOf(character);
  if (!body) throw new Error('The character has no production body mesh to measure');
  const count = body.geometry.getAttribute('position').count;
  const bone = Array.from({ length: count }, (_, index) => dominantBone(body, index));
  const trunk = [...Array(count).keys()].filter((index) => TRUNK.test(bone[index]));

  const evaluation = new PoseEvaluation(rig);
  const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
  const here = new Vector3();
  const there = new Vector3();
  const sides: ArmTrunkSide[] = [];

  for (const side of ['L', 'R'] as const) {
    const arm = [...Array(count).keys()].filter((index) => armSide(bone[index]) === side);
    let closest = Number.POSITIVE_INFINITY;
    let where = '';

    for (let step = 0; step <= steps; step += 1) {
      const time = (step / steps) * clip.duration;
      const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
      applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
      body.skeleton.update();
      body.updateWorldMatrix(true, false);

      const grid = new PointGrid(CELL);
      for (const index of trunk) grid.add(index, posedVertex(body, index, there));

      for (const index of arm) {
        posedVertex(body, index, here);
        const hit = grid.nearest(here, RINGS, (i, out) => posedVertex(body, i, out), there);
        if (hit && hit.distance < closest) {
          closest = hit.distance;
          where = `${bone[index]} to ${bone[hit.index]} at ${time.toFixed(2)}s`;
        }
      }
    }
    sides.push({ side, closest, where, armVertices: arm.length });
  }

  // Nothing found within the search means the arm stayed further away than the
  // grid looks, not that it went unmeasured.
  let closest = Number.POSITIVE_INFINITY;
  let where = '';
  for (const entry of sides) {
    if (Number.isFinite(entry.closest) && entry.closest < closest) {
      closest = entry.closest;
      where = `${entry.side}: ${entry.where}`;
    }
  }
  return { trunkVertices: trunk.length, sides, closest, where };
}

/** The search reach, for reporting an arm that never came within it. */
export const ARM_TRUNK_SEARCH = CELL * RINGS;

/**
 * How much closer an arm may come to the trunk than its reference before that
 * fails. Wide enough to absorb a re-measure or a small deliberate change,
 * narrow enough that halving any of the library's separations trips it.
 */
export const ARM_TRUNK_SLACK = 0.001;
