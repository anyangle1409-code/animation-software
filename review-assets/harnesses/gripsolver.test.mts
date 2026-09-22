import { readFileSync, writeFileSync } from 'node:fs';
import { describe, it } from 'vitest';
import { Matrix4, Vector3 } from 'three';
import { generateClip } from '../../src/animation/generate';
import { sampleClip } from '../../src/animation/clip';
import { resolveFrame } from '../../src/animation/pipeline';
import { lockAnchors } from '../../src/constraints/locks';
import { bicepCurl } from '../../src/exercises/definitions/bicepCurl';
import { shoulderPress } from '../../src/exercises/definitions/shoulderPress';
import { canonicalSkeleton, PoseEvaluation } from '../../src/rig/skeleton';
import { toRad } from '../../src/core/math';
import { applyCharacterPose } from '../../src/character/pose';
import { retargetedCharacterSource } from '../../src/character/retargetSource';
import { anatomicalGripOffset } from '../../src/equipment/attach';
import { equipmentSocketForInstance } from '../../src/equipment/library';
import { handAttachmentMatrix } from '../../src/export/clipBuilder';
import { GRIP_PROFILES } from '../../src/exercises/gripProfiles';

/**
 * Close-until-contact cylindrical power grip, per digit, per joint.
 *
 * The static table closes every digit to a fixed fraction of a fixed pose, so
 * the fingers keep going after they reach the handle. This closes each joint
 * proximal-to-distal and stops it where the digit's own skinned surface first
 * touches the real finite cylinder, which is what a hand actually does: the
 * proximal phalanx comes over the handle, then the middle, then the tip
 * carries on around it.
 *
 * The authored profile is the upper bound and the anatomical pattern, so the
 * result is the least deviation from the accepted pose that stops penetrating,
 * not a new hand shape.
 */
const rig = canonicalSkeleton;
const FINGERS = ['index', 'middle', 'ring', 'pinky'] as const;
type Finger = (typeof FINGERS)[number];
// 0.5 mm of skin press counts as contact, not penetration.
const TOLERANCE = -0.0005;

interface Handle {
  matrix: Matrix4;
  radius: number;
  half: number;
}

function distanceTo(handle: Handle, world: Vector3, scratch: Vector3): number {
  const p = scratch.copy(world).applyMatrix4(handle.matrix);
  const dr = Math.hypot(p.x, p.y) - handle.radius;
  const dz = Math.abs(p.z) - handle.half;
  if (dr <= 0 && dz <= 0) return Math.max(dr, dz);
  return Math.hypot(Math.max(dr, 0), Math.max(dz, 0));
}

describe('cylindrical grip solver', () => {
  it('closes each digit until it contacts the real handle', async () => {
    const bytes = readFileSync(process.env.GLB!);
    const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const character = await retargetedCharacterSource({ id: 'solve', label: 'Solve', data }).build(rig);
    const base = GRIP_PROFILES.dumbbell;

    const exercise = process.env.EXERCISE === 'press' ? shoulderPress : bicepCurl;
    const time = Number(process.env.TIME ?? 2);
    const side = (process.env.SIDE ?? 'l') as 'l' | 'r';
    const sign = side === 'l' ? 1 : -1;
    const closure = exercise.hands.closure;

    const clip = generateClip(rig, exercise);
    const evaluation = new PoseEvaluation(rig);
    const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
    const frame = resolveFrame(rig, evaluation, clip, time, { anchors });

    // Classification is pose-independent, so it is computed once: which mesh
    // vertices belong to which digit, and which to the palm.
    type Slot = { mesh: number; index: number; owner: Finger | 'thumb' | 'palm' };
    const slots: Slot[] = [];
    const patterns: [Finger | 'thumb' | 'palm', RegExp][] = [
      ['index', /^f_index\.?0[123]/i],
      ['middle', /^f_middle\.?0[123]/i],
      ['ring', /^f_ring\.?0[123]/i],
      ['pinky', /^f_pinky\.?0[123]/i],
      ['thumb', /^thumb\.?0[123]/i],
      ['palm', /^(palm\.?0[1-4]|hand)/i],
    ];
    character.meshes.forEach((mesh, meshIndex) => {
      const joints = mesh.geometry.getAttribute('skinIndex');
      const weights = mesh.geometry.getAttribute('skinWeight');
      const count = mesh.geometry.getAttribute('position').count;
      for (let index = 0; index < count; index += 1) {
        const totals = new Map<Finger | 'thumb' | 'palm', number>();
        let held = 0;
        for (let lane = 0; lane < 4; lane += 1) {
          const w = weights.getComponent(index, lane);
          if (w <= 0) continue;
          const raw = mesh.skeleton.bones[joints.getComponent(index, lane)]?.name ?? '';
          if (!raw.toLowerCase().endsWith(side)) continue;
          const hit = patterns.find(([, pattern]) => pattern.test(raw.replace(/^DEF-/, '')));
          if (!hit) continue;
          totals.set(hit[0], (totals.get(hit[0]) ?? 0) + w);
          held += w;
        }
        if (held < 0.5 || !totals.size) continue;
        let owner: Finger | 'thumb' | 'palm' = 'palm';
        let best = -1;
        for (const [name, value] of totals)
          if (value > best) {
            best = value;
            owner = name;
          }
        slots.push({ mesh: meshIndex, index, owner });
      }
    });

    // Pose the character with a candidate digit table and report, per owner,
    // the nearest distance to the handle and how many vertices are inside.
    const digits: Record<Finger, [number, number, number]> = {
      index: [0, 0, 0],
      middle: [0, 0, 0],
      ring: [0, 0, 0],
      pinky: [0, 0, 0],
    };
    let thumbAngles: [number, number, number] = [0, 0, 0];
    let opposition = 0;

    const scratch = new Vector3();
    const vertex = new Vector3();

    // PROD poses through the real applyCharacterPose grip context instead of
    // writing finger rotations here, so the shipped path is what gets measured.
    const production = Boolean(process.env.SHIPPED);
    const pose = () => {
      if (production) {
        applyCharacterPose(character, rig, frame.pose, evaluation, {
          contacts: frame.contacts,
          grip: { kind: exercise.hands.grip, closure: exercise.hands.closure },
        });
        return measureOnly();
      }
      const rotations = frame.pose.rotations as Record<string, { x: number; y: number; z: number }>;
      for (const finger of FINGERS)
        for (let seg = 0; seg < 3; seg += 1)
          rotations[`${finger}_0${seg + 1}_${side}`] = {
            x: 0,
            y: 0,
            z: sign * toRad(digits[finger][seg]),
          };
      for (let seg = 0; seg < 3; seg += 1)
        rotations[`thumb_0${seg + 1}_${side}`] = {
          x: seg === 0 ? toRad(opposition) : 0,
          y: 0,
          z: sign * toRad(thumbAngles[seg]),
        };
      applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
      return measureOnly();
    };

    const measureOnly = () => {
      const instance = clip.equipment.find(
        (entry) => entry.attachment.mode === 'hand' && entry.attachment.side === side,
      );
      const hand = character.handMatrix?.(side, new Matrix4());
      if (!hand || !instance || instance.attachment.mode !== 'hand') throw new Error('no handle');
      const socket = equipmentSocketForInstance(instance, instance.attachment.socket);
      const base = instance.attachment.gripOffset ?? character.gripOffset?.(side) ?? anatomicalGripOffset(side);
      // The swept variable: the character's held-handle centre, moved in the
      // plane perpendicular to the bar. x is mirrored with the hand, so a
      // shift is applied in the frame's own sense on each side.
      const shift = JSON.parse(process.env.OFFSET ?? '[0,0,0]') as [number, number, number];
      const offset = {
        x: base.x + (side === 'l' ? shift[0] : -shift[0]) / 1000,
        y: base.y + shift[1] / 1000,
        z: base.z + shift[2] / 1000,
      };
      const handle: Handle = {
        matrix: new Matrix4()
          .multiplyMatrices(hand, handAttachmentMatrix(offset, socket?.position ?? { x: 0, y: 0, z: 0 }))
          .invert(),
        radius: 0.015,
        half: 0.06,
      };

      const report = new Map<string, { near: number; inside: number }>();
      const angles: number[] = [];
      const meshes = character.meshes;
      for (const mesh of meshes) {
        mesh.skeleton.update();
        mesh.updateWorldMatrix(true, false);
      }
      for (const slot of slots) {
        const mesh = meshes[slot.mesh];
        mesh.getVertexPosition(slot.index, vertex);
        const d = distanceTo(handle, vertex.applyMatrix4(mesh.matrixWorld), scratch);
        const entry = report.get(slot.owner) ?? { near: Infinity, inside: 0 };
        if (d < entry.near) entry.near = d;
        if (d < TOLERANCE) entry.inside += 1;
        report.set(slot.owner, entry);
        // Wrap is only meaningful for a non-penetrating grip, so it is read off
        // the solved result rather than used to drive it.
        const local = scratch.copy(vertex).applyMatrix4(handle.matrix);
        if (Math.abs(local.z) <= handle.half && Math.hypot(local.x, local.y) - handle.radius < 0.012)
          angles.push(Math.atan2(local.y, local.x));
      }
      angles.sort((a, b) => a - b);
      let widest = angles.length ? angles[0] + Math.PI * 2 - angles[angles.length - 1] : Math.PI * 2;
      for (let i = 1; i < angles.length; i += 1) widest = Math.max(widest, angles[i] - angles[i - 1]);
      return { report, handle, wrap: 360 - (widest * 180) / Math.PI };
    };

    // VERIFY applies a table solved elsewhere instead of solving here, which
    // is how a cached grip is tested: one table per character and diameter,
    // re-used across frames, sides and exercises with no per-case tuning.
    const verifying = Boolean(process.env.VERIFY);
    if (verifying) {
      const cached = JSON.parse(readFileSync(process.env.VERIFY!, 'utf8'));
      for (const finger of FINGERS) digits[finger] = cached.digits[finger];
      thumbAngles = cached.thumbAngles;
      opposition = cached.opposition;
    }

    // --- solve, proximal to distal ------------------------------------
    const authored = base.fingers.map((a) => a * closure) as unknown as [number, number, number];
    const authoredThumb = base.thumb.map((a) => a * closure) as unknown as [number, number, number];

    // The joints advance TOGETHER along the authored pattern, each locking
    // where its own digit first contacts. Solving them one at a time from the
    // proximal end instead leaves the distal joints straight while the base
    // rotates, so an extended finger sweeps the handle and locks the base far
    // too early — that produced a pinky with a straight middle joint and a
    // bent tip, which is not a shape a hand makes.
    const ROUNDS = 24;
    for (const finger of verifying ? [] : FINGERS) {
      const locked = [false, false, false];
      for (let round = 1; round <= ROUNDS; round += 1) {
        for (let seg = 0; seg < 3; seg += 1) {
          if (locked[seg]) continue;
          const previous = digits[finger][seg];
          const target = (authored[seg] * round) / ROUNDS;
          digits[finger][seg] = target;
          if ((pose().report.get(finger)?.inside ?? 0) > 0) {
            digits[finger][seg] = previous;
            locked[seg] = true;
          }
        }
        if (locked.every(Boolean)) break;
      }
    }

    // --- thumb: opposition first, then flex until it locks -------------
    let bestOpposition = { value: opposition, near: -Infinity };
    for (const trial of verifying ? [] : [-14, -7, 0, 7, 14]) {
      opposition = trial;
      thumbAngles = [...authoredThumb] as [number, number, number];
      const entry = pose().report.get('thumb');
      if (entry && entry.near > bestOpposition.near) bestOpposition = { value: trial, near: entry.near };
    }
    opposition = bestOpposition.value;
    for (let seg = 0; seg < (verifying ? 0 : 3); seg += 1) {
      let lo = 0;
      let hi = authoredThumb[seg];
      thumbAngles[seg] = hi;
      if ((pose().report.get('thumb')?.inside ?? 0) === 0) continue;
      for (let step = 0; step < 14; step += 1) {
        const mid = (lo + hi) / 2;
        thumbAngles[seg] = mid;
        if ((pose().report.get('thumb')?.inside ?? 0) === 0) lo = mid;
        else hi = mid;
      }
      thumbAngles[seg] = lo;
    }

    const final = pose();
    console.log(`\nSOLVED GRIP  exercise=${exercise.clipName} t=${time} side=${side} closure=${closure}`);
    console.log(`authored finger max (x closure): ${authored.map((a) => a.toFixed(1)).join(' / ')}`);
    for (const finger of FINGERS) {
      const entry = final.report.get(finger)!;
      console.log(
        `  ${finger.padEnd(7)} MCP/PIP/DIP ${digits[finger].map((a) => a.toFixed(1).padStart(5)).join(' /')}  ` +
          `near ${(entry.near * 1000).toFixed(2).padStart(6)} mm  inside ${entry.inside}`,
      );
    }
    const thumbEntry = final.report.get('thumb')!;
    const palmEntry = final.report.get('palm')!;
    console.log(
      `  thumb   oppX ${opposition.toFixed(1)} flex ${thumbAngles.map((a) => a.toFixed(1)).join(' / ')}  ` +
        `near ${(thumbEntry.near * 1000).toFixed(2)} mm  inside ${thumbEntry.inside}`,
    );
    console.log(`  palm    near ${(palmEntry.near * 1000).toFixed(2)} mm  inside ${palmEntry.inside}`);
    console.log(`  WRAP    ${final.wrap.toFixed(0)}deg`);
    // Which way is proximal, and which way is deeper into the palm: the palm's
    // own centroid and the wrist joint, expressed in the handle's frame.
    if (process.env.PROBE) {
      const centroid = new Vector3();
      let count = 0;
      for (const slot of slots) {
        if (slot.owner !== 'palm') continue;
        const mesh = character.meshes[slot.mesh];
        mesh.getVertexPosition(slot.index, vertex);
        centroid.add(vertex.applyMatrix4(mesh.matrixWorld));
        count += 1;
      }
      centroid.multiplyScalar(1 / Math.max(1, count)).applyMatrix4(final.handle.matrix);
      const wrist = character.boneByName.get(`hand_${side}` as never) as unknown as { matrixWorld: Matrix4 } | undefined;
      const wristLocal = wrist
        ? new Vector3().setFromMatrixPosition(wrist.matrixWorld).applyMatrix4(final.handle.matrix)
        : null;
      console.log(`  PROBE palm centroid ${centroid.toArray().map((n) => (n * 1000).toFixed(1)).join(' / ')} mm`);
      console.log(`  PROBE wrist        ${wristLocal ? wristLocal.toArray().map((n) => (n * 1000).toFixed(1)).join(' / ') : 'n/a'} mm`);
    }

    if (process.env.DUMP) {
      writeFileSync(
        process.env.DUMP,
        JSON.stringify({ digits, thumbAngles, opposition, closure, side, exercise: exercise.clipName }),
      );
    }
  }, 600000);
});
