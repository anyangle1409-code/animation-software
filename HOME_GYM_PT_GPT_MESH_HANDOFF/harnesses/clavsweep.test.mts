import { readFileSync } from 'node:fs';
import { describe, it } from 'vitest';
import { Matrix4, Vector3 } from 'three';
import type { SkinnedMesh } from 'three';
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
import { validateClip } from '../../src/animation/validate';

/**
 * Which clavicle axis retracts the shoulder, and what does it cost?
 *
 * The forward shoulder is in the rest pose, not the curl, so the only lever
 * that moves the arm root without moving the arm relative to it is the
 * clavicle. The rig gives it +/-18 deg of protraction/retraction; the axis that
 * label maps to is measured here rather than guessed.
 */
const rig = canonicalSkeleton;
const mm = (v: number) => (v * 1000).toFixed(1);
const HANDLE_RADIUS = 0.015, HANDLE_HALF = 0.06;
const PLATE_RADIUS = 0.048, PLATE_HALF = 0.0175, PLATE_CENTRE = 0.075;

const envelope = (p: Vector3) => {
  const radial = Math.hypot(p.x, p.y), z = Math.abs(p.z);
  return Math.min(
    Math.max(radial - HANDLE_RADIUS, z - HANDLE_HALF),
    Math.max(radial - PLATE_RADIUS, PLATE_CENTRE - PLATE_HALF - z, z - PLATE_CENTRE - PLATE_HALF),
  );
};

describe('clavicle retraction sweep', () => {
  it('reports shoulder z, clearance and technique for each axis and angle', async () => {
    const bytes = readFileSync(process.env.GLB!);
    const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const character = await retargetedCharacterSource({ id: 'clav', label: 'clav', data }).build(rig);
    const body = (character.meshes as SkinnedMesh[]).find((m) => /freeman/i.test(m.name))!;

    const shift = (pose: typeof bicepCurl.startPose, axis: 'x' | 'y' | 'z', value: number) => ({
      ...pose,
      joints: {
        ...pose.joints,
        clavicle_l: { ...pose.joints.clavicle_l, [axis]: ((pose.joints.clavicle_l as never as Record<string, number>)?.[axis] ?? 0) + value },
        clavicle_r: { ...pose.joints.clavicle_r, [axis]: ((pose.joints.clavicle_r as never as Record<string, number>)?.[axis] ?? 0) + value },
      },
    });

    console.log('\naxis angle |  shoulder z | elbow z Bot | hand z Bot | thigh clear Bot | worst violation');
    for (const axis of ['x', 'y', 'z'] as const) {
      for (const angle of [0, -8, -4, 4, 8]) {
        if (axis !== 'x' && angle === 0) continue;
        const tuned = {
          ...bicepCurl,
          startPose: shift(bicepCurl.startPose, axis, angle),
          peakPose: shift(bicepCurl.peakPose, axis, angle),
        };
        const clip = generateClip(rig, tuned);
        const evaluation = new PoseEvaluation(rig);
        const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
        const frame = resolveFrame(rig, evaluation, clip, 0, { anchors });
        applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
        body.skeleton.update();
        body.updateWorldMatrix(true, false);
        const at = (name: string) => {
          const bone = character.boneByName.get(name as never) as { matrixWorld: never } | undefined;
          return bone ? new Vector3().setFromMatrixPosition(bone.matrixWorld) : null;
        };
        const shoulder = at('upperarm_l')!;
        const elbow = at('forearm_l')!;
        const hand = at('hand_l')!;

        // Dumbbell against the leg at Bottom: the tightest guard in the curl.
        let clearance = Number.POSITIVE_INFINITY;
        for (const side of ['l', 'r'] as const) {
          const instance = clip.equipment.find(
            (e) => e.kind === 'dumbbell' && e.attachment.mode === 'hand' && e.attachment.side === side,
          );
          if (!instance || instance.attachment.mode !== 'hand') continue;
          const handFrame = character.handMatrix?.(side, new Matrix4());
          if (!handFrame) continue;
          const socket = equipmentSocketForInstance(instance, instance.attachment.socket);
          const offset = instance.attachment.gripOffset ?? character.gripOffset?.(side) ?? anatomicalGripOffset(side);
          const dumbbell = new Matrix4().multiplyMatrices(
            handFrame, handAttachmentMatrix(offset, socket?.position ?? { x: 0, y: 0, z: 0 }),
          );
          const toDumbbell = dumbbell.clone().invert();
          const vertex = new Vector3(), local = new Vector3();
          const position = body.geometry.getAttribute('position');
          const skinIndex = body.geometry.getAttribute('skinIndex');
          const skinWeight = body.geometry.getAttribute('skinWeight');
          for (let index = 0; index < position.count; index += 1) {
            let leg = 0;
            for (let lane = 0; lane < 4; lane += 1) {
              const w = skinWeight.getComponent(index, lane);
              if (w <= 0) continue;
              const name = body.skeleton.bones[skinIndex.getComponent(index, lane)]?.name ?? '';
              if (/thigh|pelvis|shin/i.test(name)) leg += w;
            }
            if (leg < 0.5) continue;
            vertex.fromBufferAttribute(position, index);
            body.applyBoneTransform(index, vertex);
            body.localToWorld(vertex);
            local.copy(vertex).applyMatrix4(toDumbbell);
            clearance = Math.min(clearance, envelope(local));
          }
        }

        const review = validateClip(rig, new PoseEvaluation(rig), tuned, clip);
        const worst = review.violations.length
          ? `${review.violations.length}: ${review.violations.map((v) => v.ruleId).slice(0, 3).join(',')}`
          : null;
        const label = angle === 0 ? 'base    ' : `${axis}  ${angle > 0 ? '+' : ''}${angle}°`.padEnd(8);
        console.log(`${label} | ${mm(shoulder.z).padStart(11)} | ${mm(elbow.z).padStart(11)} | ${mm(hand.z).padStart(10)} | ${mm(clearance).padStart(15)} | ${worst ?? 'none'}`);
      }
    }
  }, 600_000);
});
