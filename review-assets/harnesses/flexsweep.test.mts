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

/** Forward-clearance sweep: shoulder flexion at the curl start/end pose only. */
const rig = canonicalSkeleton;
const HANDLE_RADIUS = 0.015, HANDLE_HALF = 0.06;
const PLATE_RADIUS = 0.048, PLATE_HALF = 0.0175, PLATE_CENTRE = 0.075;
const ARM = /^(shoulder|upper_?arm|forearm|hand|palm|f_|thumb|clavicle)/i;
const regionOf = (n: string) => {
  const bare = n.replace(/^DEF-/, '');
  if (/^thigh/i.test(bare)) return /001/.test(bare) ? 'mid thigh' : 'upper thigh';
  if (/^pelvis/i.test(bare)) return 'hip/pelvis';
  if (/^spine/i.test(bare)) return 'abdomen';
  return bare;
};
const envelope = (p: Vector3) => {
  const radial = Math.hypot(p.x, p.y), z = Math.abs(p.z);
  return Math.min(
    Math.max(radial - HANDLE_RADIUS, z - HANDLE_HALF),
    Math.max(radial - PLATE_RADIUS, PLATE_CENTRE - PLATE_HALF - z, z - PLATE_CENTRE - PLATE_HALF),
  );
};
const FRAMES: [string, number][] = [['Bottom', 0], ['Mid lift', 1], ['Peak', 2], ['Mid lower', 4], ['Return', 5]];

describe('upper-arm curve rebase', () => {
  it('is the accepted curve plus the offset at every sample', () => {
    const deg = (r: number) => (r * 180) / Math.PI;
    const offset = 4.3;
    const shift = (pose: typeof bicepCurl.startPose) => ({
      ...pose,
      joints: {
        ...pose.joints,
        upperarm_l: { ...pose.joints.upperarm_l, x: (pose.joints.upperarm_l?.x ?? 0) + offset },
        upperarm_r: { ...pose.joints.upperarm_r, x: (pose.joints.upperarm_r?.x ?? 0) + offset },
      },
    });
    const accepted = generateClip(rig, bicepCurl);
    const rebased = generateClip(rig, { ...bicepCurl, startPose: shift(bicepCurl.startPose), peakPose: shift(bicepCurl.peakPose) });
    let worst = 0;
    for (let t = 0; t <= 5.5; t += 0.05) {
      for (const bone of ['upperarm_l', 'upperarm_r'] as const) {
        const a = deg(sampleClip(accepted, t).pose.rotations[bone]?.x ?? 0);
        const b = deg(sampleClip(rebased, t).pose.rotations[bone]?.x ?? 0);
        worst = Math.max(worst, Math.abs(b - a - offset));
      }
    }
    console.log(`REBASE worst deviation from +${offset}° across the rep: ${worst.toFixed(6)}°`);
    for (const t of [0, 0.5, 1.0, 1.5, 2.0, 3.3, 5.0, 5.5]) {
      const a = deg(sampleClip(accepted, t).pose.rotations.upperarm_l?.x ?? 0);
      const b = deg(sampleClip(rebased, t).pose.rotations.upperarm_l?.x ?? 0);
      console.log(`REBASE_SAMPLE ${t.toFixed(1)}s accepted ${a.toFixed(4)}° -> rebased ${b.toFixed(4)}° (Δ ${(b - a).toFixed(4)}°, relative to own baseline ${(b - 4.3).toFixed(4)}°)`);
    }
  });
});

describe('forward clearance sweep', () => {
  it('sweeps shoulder flexion at the curl start pose', async () => {
    const bytes = readFileSync(process.env.GLB!);
    const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const character = await retargetedCharacterSource({ id: 'flex', label: 'Flex', data }).build(rig);
    const baseline: Record<string, { grip: Vector3; plate: Vector3; axis: Vector3 }> = {};

    console.log('\nFLEX_SWEEP');
    console.log('flex | frame | side | region | clearance mm | inside | Δz grip | Δz plate | elbow x/y/z | grip x/y/z | axis Δ° | L/R mismatch');
    for (const flex of [0]) {
      // Neutral rebase: the whole authored upper-arm flexion curve shifted by
      // `flex`, start and peak together, so the relative motion is preserved.
      const shift = (pose: typeof bicepCurl.startPose) => ({
        ...pose,
        joints: {
          ...pose.joints,
          upperarm_l: { ...pose.joints.upperarm_l, x: (pose.joints.upperarm_l?.x ?? 0) + flex },
          upperarm_r: { ...pose.joints.upperarm_r, x: (pose.joints.upperarm_r?.x ?? 0) + flex },
        },
      });
      const tuned = { ...bicepCurl, startPose: shift(bicepCurl.startPose), peakPose: shift(bicepCurl.peakPose) };
      const clip = generateClip(rig, tuned);
      const evaluation = new PoseEvaluation(rig);
      const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
      for (const [label, time] of FRAMES) {
        const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
        applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
        const measured: Record<string, number> = {};
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
          const grip = new Vector3().setFromMatrixPosition(dumbbell);
          const axis = new Vector3(0, 0, 1).transformDirection(dumbbell).normalize();
          const inboard = grip.x > 0 ? (axis.x > 0 ? -1 : 1) : (axis.x > 0 ? 1 : -1);
          const plate = grip.clone().addScaledVector(axis, inboard * PLATE_CENTRE);
          const elbowBone = character.boneByName.get((side === 'l' ? 'forearm_l' : 'forearm_r') as never);
          const elbow = elbowBone ? new Vector3().setFromMatrixPosition(elbowBone.matrixWorld) : new Vector3();

          let best = Number.POSITIVE_INFINITY, inside = 0, region = '—';
          const vertex = new Vector3(), local = new Vector3();
          for (const mesh of character.meshes) {
            mesh.skeleton.update();
            mesh.updateWorldMatrix(true, false);
            const joints = mesh.geometry.getAttribute('skinIndex');
            const weights = mesh.geometry.getAttribute('skinWeight');
            for (let index = 0; index < mesh.geometry.getAttribute('position').count; index += 1) {
              let arm = 0, top = 0, topName = '';
              for (let lane = 0; lane < 4; lane += 1) {
                const w = weights.getComponent(index, lane);
                if (w <= 0) continue;
                const name = mesh.skeleton.bones[joints.getComponent(index, lane)]?.name ?? '';
                if (ARM.test(name.replace(/^DEF-/, ''))) arm += w;
                if (w > top) { top = w; topName = name; }
              }
              if (arm > 0.05) continue;
              mesh.getVertexPosition(index, vertex);
              local.copy(vertex.applyMatrix4(mesh.matrixWorld)).applyMatrix4(toDumbbell);
              const d = envelope(local);
              if (d < 0) inside += 1;
              if (d < best) { best = d; region = regionOf(topName); }
            }
          }
          const key = `${label}-${side}`;
          if (flex === 0) baseline[key] = { grip: grip.clone(), plate: plate.clone(), axis: axis.clone() };
          const base = baseline[key];
          const twist = ((Math.acos(Math.min(1, Math.abs(axis.dot(base.axis)))) * 180) / Math.PI).toFixed(1);
          measured[side] = best;
          console.log(
            `${flex.toFixed(1)}° | ${label} | ${side} | ${region} | ${(best * 1000).toFixed(2)} | ${inside} | ` +
            `${((grip.z - base.grip.z) * 1000).toFixed(1)} | ${((plate.z - base.plate.z) * 1000).toFixed(1)} | ` +
            `${(elbow.x * 1000).toFixed(0)}/${(elbow.y * 1000).toFixed(0)}/${(elbow.z * 1000).toFixed(0)} | ` +
            `${(grip.x * 1000).toFixed(0)}/${(grip.y * 1000).toFixed(0)}/${(grip.z * 1000).toFixed(0)} | ${twist} | ` +
            (side === 'r' && measured.l !== undefined ? `${(Math.abs(measured.l - best) * 1000).toFixed(2)}` : '—'),
          );
        }
      }
    }
  });
});

import { validateClip } from '../../src/animation/validate';

describe('forward clearance technique check', () => {
  it('re-runs the curl technique rules across the sweep', async () => {
    for (const flex of [0]) {
      // Neutral rebase: the whole authored upper-arm flexion curve shifted by
      // `flex`, start and peak together, so the relative motion is preserved.
      const shift = (pose: typeof bicepCurl.startPose) => ({
        ...pose,
        joints: {
          ...pose.joints,
          upperarm_l: { ...pose.joints.upperarm_l, x: (pose.joints.upperarm_l?.x ?? 0) + flex },
          upperarm_r: { ...pose.joints.upperarm_r, x: (pose.joints.upperarm_r?.x ?? 0) + flex },
        },
      });
      const tuned = { ...bicepCurl, startPose: shift(bicepCurl.startPose), peakPose: shift(bicepCurl.peakPose) };
      const clip = generateClip(rig, tuned);
      const evaluation = new PoseEvaluation(rig);
      const report = validateClip(rig, evaluation, tuned, clip);
      console.log(`TECHNIQUE ${flex.toFixed(1)}°: ${JSON.stringify(report).slice(0, 600)}`);
    }
  });
});
