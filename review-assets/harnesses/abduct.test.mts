import { readFileSync } from 'node:fs';
import { describe, it } from 'vitest';
import { Matrix4, Vector3 } from 'three';
import { generateClip } from '../../src/animation/generate';
import { sampleClip } from '../../src/animation/clip';
import { resolveFrame } from '../../src/animation/pipeline';
import { lockAnchors } from '../../src/constraints/locks';
import { bicepCurl } from '../../src/exercises/definitions/bicepCurl';
import { canonicalSkeleton, PoseEvaluation } from '../../src/rig/skeleton';
import { applyCharacterPose } from '../../src/character/pose';
import { retargetedCharacterSource } from '../../src/character/retargetSource';
import { anatomicalGripOffset } from '../../src/equipment/attach';
import { equipmentSocketForInstance } from '../../src/equipment/library';
import { handAttachmentMatrix } from '../../src/export/clipBuilder';

/** Smallest curl-bottom abduction that clears the plate from the thigh. */
const HANDLE_RADIUS = 0.015, HANDLE_HALF = 0.06;
const PLATE_RADIUS = 0.048, PLATE_INNER = 0.075 - 0.0175, PLATE_OUTER = 0.075 + 0.0175;
const rig = canonicalSkeleton;
const ARM = /^(shoulder|upper_?arm|forearm|hand|palm|f_|thumb|clavicle)/i;
const distance = (p: Vector3) => {
  const radial = Math.hypot(p.x, p.y), z = Math.abs(p.z);
  return Math.min(
    Math.max(radial - HANDLE_RADIUS, z - HANDLE_HALF),
    Math.max(radial - PLATE_RADIUS, PLATE_INNER - z, z - PLATE_OUTER),
  );
};

describe('curl bottom abduction sweep', () => {
  it('finds the minimum that clears the thigh', async () => {
    const bytes = readFileSync(process.env.GLB!);
    const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const character = await retargetedCharacterSource({ id: 'abduct', label: 'Abduct', data }).build(rig);
    const base = Number(bicepCurl.startPose.joints.upperarm_r?.z ?? 3);

    for (const value of [base, 5, 6, 7, 8, 9, 11]) {
      const tuned = {
        ...bicepCurl,
        startPose: {
          ...bicepCurl.startPose,
          joints: {
            ...bicepCurl.startPose.joints,
            upperarm_l: { ...bicepCurl.startPose.joints.upperarm_l, z: -value },
            upperarm_r: { ...bicepCurl.startPose.joints.upperarm_r, z: value },
          },
        },
      };
      const clip = generateClip(rig, tuned);
      const evaluation = new PoseEvaluation(rig);
      const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
      const frame = resolveFrame(rig, evaluation, clip, 0, { anchors });
      applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });

      const line: string[] = [];
      for (const side of ['l', 'r'] as const) {
        const instance = clip.equipment.find(
          (e) => e.kind === 'dumbbell' && e.attachment.mode === 'hand' && e.attachment.side === side,
        );
        if (!instance || instance.attachment.mode !== 'hand') continue;
        const hand = character.handMatrix?.(side, new Matrix4());
        if (!hand) continue;
        const socket = equipmentSocketForInstance(instance, instance.attachment.socket);
        const grip = instance.attachment.gripOffset ?? character.gripOffset?.(side) ?? anatomicalGripOffset(side);
        const toDumbbell = new Matrix4()
          .multiplyMatrices(hand, handAttachmentMatrix(grip, socket?.position ?? { x: 0, y: 0, z: 0 }))
          .invert();
        const vertex = new Vector3(), local = new Vector3();
        let minimum = Number.POSITIVE_INFINITY, inside = 0;
        for (const mesh of character.meshes) {
          mesh.skeleton.update();
          mesh.updateWorldMatrix(true, false);
          const joints = mesh.geometry.getAttribute('skinIndex');
          const weights = mesh.geometry.getAttribute('skinWeight');
          for (let index = 0; index < mesh.geometry.getAttribute('position').count; index += 1) {
            let arm = 0;
            for (let lane = 0; lane < 4; lane += 1) {
              const weight = weights.getComponent(index, lane);
              if (weight <= 0) continue;
              const name = mesh.skeleton.bones[joints.getComponent(index, lane)]?.name.replace(/^DEF-/, '') ?? '';
              if (ARM.test(name)) arm += weight;
            }
            if (arm > 0.05) continue;
            mesh.getVertexPosition(index, vertex);
            local.copy(vertex).applyMatrix4(mesh.matrixWorld).applyMatrix4(toDumbbell);
            const d = distance(local);
            if (d < minimum) minimum = d;
            if (d < 0) inside += 1;
          }
        }
        line.push(`${side} ${(minimum * 1000).toFixed(2)} mm (${inside} in)`);
      }
      // Does the hand actually move off the leg, or does a lock absorb it?
      let gap = Number.POSITIVE_INFINITY;
      for (const mesh of character.meshes) {
        mesh.skeleton.update();
        mesh.updateWorldMatrix(true, false);
        const joints = mesh.geometry.getAttribute('skinIndex');
        const weights = mesh.geometry.getAttribute('skinWeight');
        const hands: Vector3[] = [], legs: Vector3[] = [];
        const point = new Vector3();
        for (let index = 0; index < mesh.geometry.getAttribute('position').count; index += 1) {
          let h = 0, l = 0;
          for (let lane = 0; lane < 4; lane += 1) {
            const weight = weights.getComponent(index, lane);
            if (weight <= 0) continue;
            const name = mesh.skeleton.bones[joints.getComponent(index, lane)]?.name.replace(/^DEF-/, '') ?? '';
            if (/^(hand|palm|f_|thumb)/i.test(name)) h += weight;
            if (/^(thigh|pelvis)/i.test(name)) l += weight;
          }
          if (h < 0.5 && l < 0.5) continue;
          mesh.getVertexPosition(index, point);
          point.applyMatrix4(mesh.matrixWorld);
          (h >= 0.5 ? hands : legs).push(point.clone());
        }
        for (const a of hands) for (const b of legs) gap = Math.min(gap, a.distanceToSquared(b));
      }
      console.log(`ABDUCT ${String(value).padStart(2)}°  ${line.join('   ')}   hand-leg ${(Math.sqrt(gap) * 1000).toFixed(2)} mm`);
    }
  });
});
