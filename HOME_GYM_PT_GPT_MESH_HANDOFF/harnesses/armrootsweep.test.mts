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
 * How far posterior does the arm root have to move before the shoulder stops
 * reading forward, and what does each step cost?
 *
 * +z is front. Shoulder flexion and abduction can be overridden so the curl can
 * be re-solved against a corrected chain rather than the old forward-biased one.
 */
const rig = canonicalSkeleton;
const mm = (v: number) => (v * 1000).toFixed(1);
const deg = (r: number) => (r * 180) / Math.PI;
const HANDLE_RADIUS = 0.015, HANDLE_HALF = 0.06;
const PLATE_RADIUS = 0.048, PLATE_HALF = 0.0175, PLATE_CENTRE = 0.075;
const envelope = (p: Vector3) => {
  const radial = Math.hypot(p.x, p.y), z = Math.abs(p.z);
  return Math.min(
    Math.max(radial - HANDLE_RADIUS, z - HANDLE_HALF),
    Math.max(radial - PLATE_RADIUS, PLATE_CENTRE - PLATE_HALF - z, z - PLATE_CENTRE - PLATE_HALF),
  );
};

function dominant(mesh: SkinnedMesh, index: number): string {
  const skinIndex = mesh.geometry.getAttribute('skinIndex');
  const skinWeight = mesh.geometry.getAttribute('skinWeight');
  let best = -1;
  let bone = '?';
  for (let lane = 0; lane < 4; lane += 1) {
    const weight = skinWeight.getComponent(index, lane);
    if (weight > best) {
      best = weight;
      bone = mesh.skeleton.bones[skinIndex.getComponent(index, lane)]?.name ?? '?';
    }
  }
  return bone.replace(/^DEF-?/, '');
}

function posedPoint(mesh: SkinnedMesh, index: number, out: Vector3): Vector3 {
  const position = mesh.geometry.getAttribute('position');
  out.fromBufferAttribute(position, index);
  const morphs = mesh.geometry.morphAttributes.position ?? [];
  const influences = mesh.morphTargetInfluences ?? [];
  const relative = mesh.geometry.morphTargetsRelative === true;
  for (let slot = 0; slot < morphs.length; slot += 1) {
    const weight = influences[slot] ?? 0;
    if (!weight) continue;
    const morph = morphs[slot];
    out.x += (relative ? morph.getX(index) : morph.getX(index) - position.getX(index)) * weight;
    out.y += (relative ? morph.getY(index) : morph.getY(index) - position.getY(index)) * weight;
    out.z += (relative ? morph.getZ(index) : morph.getZ(index) - position.getZ(index)) * weight;
  }
  mesh.applyBoneTransform(index, out);
  return mesh.localToWorld(out);
}

/**
 * Re-solve levers. Shoulder flexion and abduction live in the start/peak poses;
 * the elbow's Bottom angle is a jointTarget `start`. The elbow is the lever that
 * buys dumbbell clearance without tilting the humerus forward, which matters
 * because a forward humerus is the thing being corrected.
 */
const tunedCurl = (flexion: number | null, abduction: number | null, elbow: number | null = null) => {
  if (flexion === null && abduction === null && elbow === null) return bicepCurl;
  const patch = (pose: typeof bicepCurl.startPose, mirror: boolean) => ({
    ...pose,
    joints: {
      ...pose.joints,
      [mirror ? 'upperarm_r' : 'upperarm_l']: {
        ...(mirror ? pose.joints.upperarm_r : pose.joints.upperarm_l),
        ...(flexion === null ? {} : { x: flexion }),
        ...(abduction === null ? {} : { z: mirror ? -abduction : abduction }),
      },
    },
  });
  const both = (pose: typeof bicepCurl.startPose) => patch(patch(pose, false), true);
  const jointTargets = elbow === null
    ? bicepCurl.jointTargets
    : bicepCurl.jointTargets.map((t) => (t.axis === 'x' && /^forearm_/.test(t.bone) ? { ...t, start: elbow } : t));
  return {
    ...bicepCurl,
    startPose: both(bicepCurl.startPose),
    peakPose: both(bicepCurl.peakPose),
    jointTargets,
  };
};

describe('arm-root posterior sweep', () => {
  it('reports alignment and cost for each candidate', async () => {
    const assets = (process.env.ASSETS ?? '').split(',').filter(Boolean);
    // GRID re-solves the curl around a corrected chain: "flex,abd" pairs, where
    // an empty field keeps the authored value.
    const grid: [number | null, number | null, number | null][] = (process.env.GRID ?? ',')
      .split(';')
      .filter(Boolean)
      .map((pair) => {
        const [f, a, e] = pair.split(',');
        const num = (v: string | undefined) => (v === '' || v === undefined ? null : Number(v));
        return [num(f), num(a), num(e)];
      });
    console.log('\nasset / overrides           | sh z  | sh-spine | tilt° | cap ctr | cap front-sternum | hand z | clear body | viol');

    for (const path of assets) for (const [flexion, abduction, elbowStart] of grid) {
      const exercise = tunedCurl(flexion, abduction, elbowStart);
      const bytes = readFileSync(path);
      const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
      const character = await retargetedCharacterSource({ id: path, label: path, data }).build(rig);
      const body = (character.meshes as SkinnedMesh[]).find((m) => /freeman/i.test(m.name))!;
      const count = body.geometry.getAttribute('position').count;
      const regions = Array.from({ length: count }, (_, index) => dominant(body, index));
      const clip = generateClip(rig, exercise);
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
      const spine = at('spine_03')!;
      const shoulder = at('upperarm_l')!;
      const elbow = at('forearm_l')!;
      const hand = at('hand_l')!;
      const axis = elbow.clone().sub(shoulder).normalize();
      const tilt = deg(Math.atan2(axis.z, -axis.y));
      const front = new Vector3(0, 0, 1).addScaledVector(axis, -new Vector3(0, 0, 1).dot(axis)).normalize();
      const point = new Vector3();

      let sternum = -Infinity;
      for (let index = 0; index < count; index += 1) {
        if (!/^(spine|breast)/i.test(regions[index])) continue;
        posedPoint(body, index, point);
        if (Math.abs(point.y - spine.y) > 0.045 || Math.abs(point.x) > 0.06) continue;
        sternum = Math.max(sternum, point.z);
      }
      let capSum = 0, capN = 0, capFront = -Infinity;
      for (let index = 0; index < count; index += 1) {
        const region = regions[index];
        if (!/^(shoulder|upper_?arm)/i.test(region) || !/L\d*$/.test(region)) continue;
        posedPoint(body, index, point);
        const rel = point.clone().sub(shoulder);
        const along = rel.dot(axis);
        if (along < -0.005 || along > 0.07) continue;
        capFront = Math.max(capFront, point.z);
        const radial = rel.addScaledVector(axis, -along);
        if (radial.length() > 0.07) continue;
        capSum += radial.dot(front);
        capN += 1;
      }

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
        const local = new Vector3();
        for (let index = 0; index < count; index += 1) {
          if (!/^(thigh|pelvis|shin)/i.test(regions[index])) continue;
          posedPoint(body, index, point);
          local.copy(point).applyMatrix4(toDumbbell);
          clearance = Math.min(clearance, envelope(local));
        }
      }

      const review = validateClip(rig, new PoseEvaluation(rig), exercise, clip);
      const viol = review.violations.length
        ? `${review.violations.length}:${review.violations.map((v) => v.ruleId).slice(0, 2).join(',')}`
        : 'none';
      const name = `${path.split('/').pop()!.replace('HomeGymPT_Male_', '').replace('.glb', '')} f${flexion ?? 'auto'}/a${abduction ?? 'auto'}/e${elbowStart ?? 'auto'}`;
      console.log(
        `${name.padEnd(32)} | ${mm(shoulder.z).padStart(5)} | ${mm(shoulder.z - spine.z).padStart(8)} | ${tilt.toFixed(2).padStart(5)} | ${(capN ? mm(capSum / capN) : '—').padStart(7)} | ${mm(capFront - sternum).padStart(17)} | ${mm(hand.z).padStart(6)} | ${mm(clearance).padStart(10)} | ${viol}`,
      );
      character.dispose?.();
    }
  }, 900_000);
});
