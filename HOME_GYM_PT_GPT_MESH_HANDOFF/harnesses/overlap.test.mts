import { readFileSync } from 'node:fs';
import { describe, it } from 'vitest';
import { Matrix4, Vector3 } from 'three';
import { generateClip } from '../../src/animation/generate';
import { sampleClip } from '../../src/animation/clip';
import { resolveFrame } from '../../src/animation/pipeline';
import { lockAnchors } from '../../src/constraints/locks';
import { bicepCurl } from '../../src/exercises/definitions/bicepCurl';
import { shoulderPress } from '../../src/exercises/definitions/shoulderPress';
import { canonicalSkeleton, PoseEvaluation } from '../../src/rig/skeleton';
import { applyCharacterPose } from '../../src/character/pose';
import { retargetedCharacterSource } from '../../src/character/retargetSource';
import { anatomicalGripOffset } from '../../src/equipment/attach';
import { equipmentSocketForInstance } from '../../src/equipment/library';
import { handAttachmentMatrix } from '../../src/export/clipBuilder';

/**
 * Dumbbell-versus-thigh closest approach at the curl bottom.
 *
 * A true 3D test, not screen-space occlusion: every body vertex that is not
 * part of the arm holding the weight is transformed into the dumbbell's frame
 * and measured against its envelope — the handle cylinder, and the two plates
 * as discs at each end. Negative means the weight is inside the leg.
 */
// The real parts from src/equipment/geometry.ts, not the bounding box: a bar of
// radius 15 mm and length 120 mm, and two rubber discs of radius 48 mm and
// thickness 35 mm centred 75 mm out. Modelling the plates as a solid region out
// to the bounding box reads about 11 mm more overlap than there is.
const HANDLE_RADIUS = 0.015;
const HANDLE_HALF = 0.06;
const PLATE_RADIUS = 0.048;
const PLATE_INNER = 0.075 - 0.0175;
const PLATE_OUTER = 0.075 + 0.0175;

const rig = canonicalSkeleton;
// GLTFLoader sanitises DEF-hand.L to DEF-handL, so a pattern expecting the dot
// or an underscore matches nothing and the "closest approach" comes back as the
// grip itself — identical for every body, which is how this was caught.
const ARM = /^(shoulder|upper_?arm|forearm|hand|palm|f_|thumb|clavicle)/i;

function distanceToDumbbell(local: Vector3): number {
  const radial = Math.hypot(local.x, local.y);
  const z = Math.abs(local.z);
  // Outside the handle's span the surface is the plate disc.
  const handle = Math.max(radial - HANDLE_RADIUS, z - HANDLE_HALF);
  const plate = Math.max(radial - PLATE_RADIUS, PLATE_INNER - z, z - PLATE_OUTER);
  return Math.min(handle, plate);
}

describe('dumbbell clearance', () => {
  it('measures closest approach to the leg at the curl bottom', async () => {
    const bytes = readFileSync(process.env.GLB!);
    const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const character = await retargetedCharacterSource({ id: 'overlap', label: 'Overlap', data }).build(rig);
    const definition = process.env.EXERCISE === 'press' ? shoulderPress : bicepCurl;
    const clip = generateClip(rig, definition);
    const evaluation = new PoseEvaluation(rig);
    const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);

    // The retained curl review sequence.
    const FRAMES: [string, number][] =
      process.env.EXERCISE === 'press'
        ? [['Rack', 0], ['Mid', clip.duration * 0.25], ['Overhead', clip.duration * 0.5], ['Lower', clip.duration * 0.75]]
        : process.env.BOTTOM_ONLY
          ? [['Bottom', 0]]
          : [['Bottom', 0], ['Mid lift', 1], ['Peak', 2], ['Mid lower', 4], ['Return', 5]];
    for (const [label, time] of FRAMES) {
      const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
      applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
      // Exactly what src/viewer/EquipmentView.tsx does to draw a held weight:
      // the character's own hand, the grip offset and the socket, rotations
      // included. resolveEquipment is a different placement — it works from the
      // canonical rig's hand — and is what the constraint pipeline uses, not
      // what is rendered.
      const line: string[] = [];
      for (const side of ['l', 'r'] as const) {
        const instance = clip.equipment.find(
          (entry) => entry.kind === 'dumbbell' && entry.attachment.mode === 'hand' && entry.attachment.side === side,
        );
        if (!instance || instance.attachment.mode !== 'hand') continue;
        const hand = character.handMatrix?.(side, new Matrix4());
        if (!hand) continue;
        const socket = equipmentSocketForInstance(instance, instance.attachment.socket);
        // The authoritative rule: the character's own handle centre.
        const grip =
          instance.attachment.gripOffset ??
          character.gripOffset?.(side) ??
          anatomicalGripOffset(side);
        const equipment = new Matrix4().multiplyMatrices(
          hand,
          handAttachmentMatrix(grip, socket?.position ?? { x: 0, y: 0, z: 0 }, {
            gripRotation: instance.attachment.gripRotation,
            socketRotation: socket?.rotation,
          }),
        );
        const toDumbbell = equipment.clone().invert();
        const vertex = new Vector3();
        const local = new Vector3();
        let minimum = Number.POSITIVE_INFINITY;
        let inside = 0;
        const at = new Vector3();
        for (const mesh of character.meshes) {
          // On a dressed file the garment is a second skinned mesh sitting
          // outside the skin, so a figure measured over both is not comparable
          // with the bare body's. SKIN_ONLY restricts this to the body.
          if (process.env.SKIN_ONLY && /shorts|garment|cloth/i.test(mesh.name)) continue;
          mesh.skeleton.update();
          mesh.updateWorldMatrix(true, false);
          const joints = mesh.geometry.getAttribute('skinIndex');
          const weights = mesh.geometry.getAttribute('skinWeight');
          const count = mesh.geometry.getAttribute('position').count;
          for (let index = 0; index < count; index += 1) {
            // Skip the arm that is holding it; only the rest of the body counts.
            let arm = 0;
            for (let lane = 0; lane < 4; lane += 1) {
              const weight = weights.getComponent(index, lane);
              if (weight <= 0) continue;
              const bone = mesh.skeleton.bones[joints.getComponent(index, lane)];
              if (bone && ARM.test(bone.name.replace(/^DEF-/, ''))) arm += weight;
            }
            if (arm > 0.05) continue;
            mesh.getVertexPosition(index, vertex);
            local.copy(vertex).applyMatrix4(mesh.matrixWorld).applyMatrix4(toDumbbell);
            const distance = distanceToDumbbell(local);
            if (distance < minimum) { minimum = distance; at.copy(local); }
            if (distance < 0) inside += 1;
          }
        }
        const radial = Math.hypot(at.x, at.y);
        const part = Math.abs(at.z) <= HANDLE_HALF ? 'handle' : 'plate';
        line.push(
          `${side}: ${(minimum * 1000).toFixed(2)} mm (${inside} in, worst at ${part}` +
            ` x${(at.x * 1000).toFixed(0)} y${(at.y * 1000).toFixed(0)} z${(at.z * 1000).toFixed(0)}, radial ${(radial * 1000).toFixed(0)})`,
        );
      }
      console.log(`DUMBBELL_CLEARANCE ${label}  ${line.join('   ')}`);

      // Is the hand itself against the leg? If the body already touches at this
      // pose, no equipment placement can clear the weight without moving the
      // arm, which the curl motion is not allowed to do.
      if (process.env.BODY_GAP) {
        for (const mesh of character.meshes) {
          mesh.skeleton.update();
          mesh.updateWorldMatrix(true, false);
          const joints = mesh.geometry.getAttribute('skinIndex');
          const weights = mesh.geometry.getAttribute('skinWeight');
          const count = mesh.geometry.getAttribute('position').count;
          const hands: Vector3[] = [];
          const legs: Vector3[] = [];
          const point = new Vector3();
          for (let index = 0; index < count; index += 1) {
            let arm = 0, leg = 0;
            for (let lane = 0; lane < 4; lane += 1) {
              const weight = weights.getComponent(index, lane);
              if (weight <= 0) continue;
              const name = mesh.skeleton.bones[joints.getComponent(index, lane)]?.name.replace(/^DEF-/, '') ?? '';
              if (/^(hand|palm|f_|thumb)/i.test(name)) arm += weight;
              if (/^(thigh|pelvis)/i.test(name)) leg += weight;
            }
            if (arm < 0.5 && leg < 0.5) continue;
            mesh.getVertexPosition(index, point);
            point.applyMatrix4(mesh.matrixWorld);
            (arm >= 0.5 ? hands : legs).push(point.clone());
          }
          let closest = Number.POSITIVE_INFINITY;
          for (const h of hands) for (const l of legs) closest = Math.min(closest, h.distanceToSquared(l));
          console.log(`BODY_GAP ${label}  closest hand-to-leg surface ${(Math.sqrt(closest) * 1000).toFixed(2)} mm` +
            ` (${hands.length} hand vertices, ${legs.length} leg vertices)`);
        }
      }
    }
  });
});
