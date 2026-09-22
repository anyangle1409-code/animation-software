import { readFileSync, writeFileSync } from 'node:fs';
import { describe, it } from 'vitest';
import { Vector3 } from 'three';
import type { SkinnedMesh } from 'three';
import { generateClip } from '../../src/animation/generate';
import { sampleClip } from '../../src/animation/clip';
import { resolveFrame } from '../../src/animation/pipeline';
import { lockAnchors } from '../../src/constraints/locks';
import { bicepCurl } from '../../src/exercises/definitions/bicepCurl';
import { canonicalSkeleton, PoseEvaluation } from '../../src/rig/skeleton';
import { applyCharacterPose } from '../../src/character/pose';
import { retargetedCharacterSource } from '../../src/character/retargetSource';

/**
 * Side-Bottom diagnostic: does the humerus descend through the middle of the
 * shoulder mass, or along its anterior face?
 *
 * Measured as a sagittal slab through the arm. For each height band the arm's
 * own front and back surfaces give a midline; the humerus axis is projected to
 * the same height and compared with it. A positive offset means the bone runs
 * ahead of the mass it is supposed to be inside.
 *
 * Deliberately surface-based rather than skin-weight-based: which bone owns a
 * vertex says nothing about where the visible silhouette sits, and the earlier
 * cap measurements were repeatedly skewed by weight selection reaching over the
 * scapula.
 */
const rig = canonicalSkeleton;
const mm = (v: number) => (v * 1000).toFixed(1);
const deg = (r: number) => (r * 180) / Math.PI;

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

describe('sagittal shoulder-to-upper-arm profile', () => {
  it('compares the humerus axis with the arm mass midline, height by height', async () => {
    for (const path of (process.env.ASSETS ?? '').split(',').filter(Boolean)) {
      const bytes = readFileSync(path);
      const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
      const character = await retargetedCharacterSource({ id: path, label: path, data }).build(rig);
      const body = (character.meshes as SkinnedMesh[]).find((m) => /freeman/i.test(m.name))!;
      const count = body.geometry.getAttribute('position').count;
      // Arm-owned surface: the combined skin weight on the humerus and its
      // twist helper. Geometry alone cannot separate arm from torso where they
      // touch, and a sleeve radius just picks up whichever lat happens to be
      // nearby; ownership is well defined. >= 0.7 keeps the arm tube and the
      // deltoid proper while excluding trapezius, scapula and the armpit blend.
      const skinIndex = body.geometry.getAttribute('skinIndex');
      const skinWeight = body.geometry.getAttribute('skinWeight');
      const armShare = new Float32Array(count);
      for (let index = 0; index < count; index += 1) {
        let share = 0;
        for (let lane = 0; lane < 4; lane += 1) {
          const w = skinWeight.getComponent(index, lane);
          if (w <= 0) continue;
          const name = body.skeleton.bones[skinIndex.getComponent(index, lane)]?.name ?? '';
          if (/upper_?arm.?L/i.test(name)) share += w;
        }
        armShare[index] = share;
      }
      const clip = generateClip(rig, bicepCurl);
      const evaluation = new PoseEvaluation(rig);
      const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
      const frame = resolveFrame(rig, evaluation, clip, 0, { anchors });
      applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
      body.skeleton.update();
      body.updateWorldMatrix(true, false);

      const at = (n: string) => {
        const b = character.boneByName.get(n as never) as { matrixWorld: never } | undefined;
        return b ? new Vector3().setFromMatrixPosition(b.matrixWorld) : null;
      };
      const clav = at('clavicle_l')!;
      const shoulder = at('upperarm_l')!;
      const elbow = at('forearm_l')!;
      const axis = elbow.clone().sub(shoulder).normalize();
      const point = new Vector3();

      console.log(`\n================ ${path.split('/').pop()} — side Bottom ================`);
      console.log(`  clavicle tail / AC point  x ${mm(clav.x)}  y ${mm(clav.y)}  z ${mm(clav.z)}`);
      console.log(`  upper-arm joint centre    x ${mm(shoulder.x)}  y ${mm(shoulder.y)}  z ${mm(shoulder.z)}`);
      console.log(`  elbow                     x ${mm(elbow.x)}  y ${mm(elbow.y)}  z ${mm(elbow.z)}`);
      console.log(`  joint centre relative to the clavicle tail: `
        + `below ${mm(clav.y - shoulder.y)} mm, behind ${mm(clav.z - shoulder.z)} mm, lateral ${mm(Math.abs(shoulder.x - clav.x))} mm`);
      console.log(`  humerus sagittal tilt ${deg(Math.atan2(axis.z, -axis.y)).toFixed(2)}°`);

      // Does any shoulder mass sit ABOVE the joint? That is what "hanging from
      // underneath the cap" means. Split by ownership, because the two halves
      // of the cap behave differently: deltoid follows the arm root rigidly,
      // trapezius/acromion is owned by the clavicle bone and the torso.
      let deltoidApex = -Infinity, shoulderApex = -Infinity, torsoApex = -Infinity;
      let deltoidApexZ = 0, shoulderApexZ = 0;
      for (let index = 0; index < count; index += 1) {
        let arm = 0, clav = 0, trunk = 0;
        for (let lane = 0; lane < 4; lane += 1) {
          const w = skinWeight.getComponent(index, lane);
          if (w <= 0) continue;
          const name = body.skeleton.bones[skinIndex.getComponent(index, lane)]?.name ?? '';
          if (/upper_?arm.?L/i.test(name)) arm += w;
          else if (/shoulderL/i.test(name)) clav += w;
          else if (/spine|breast|neck/i.test(name)) trunk += w;
        }
        posedPoint(body, index, point);
        if (point.x < 0.06) continue;
        if (arm >= 0.7 && point.y > deltoidApex) { deltoidApex = point.y; deltoidApexZ = point.z; }
        if (clav >= 0.5 && point.y > shoulderApex) { shoulderApex = point.y; shoulderApexZ = point.z; }
        if (trunk >= 0.5 && point.x > 0.09 && point.y > torsoApex) torsoApex = point.y;
      }
      console.log(`  deltoid apex (arm-owned)      y ${mm(deltoidApex)}  z ${mm(deltoidApexZ)}  -> ${mm(deltoidApex - shoulder.y)} mm ABOVE the joint`);
      console.log(`  acromion/trap apex (clav-owned) y ${mm(shoulderApex)}  z ${mm(shoulderApexZ)}  -> ${mm(shoulderApex - shoulder.y)} mm above the joint`);
      console.log(`  outer trunk apex              y ${mm(torsoApex)}                -> ${mm(torsoApex - shoulder.y)} mm above the joint`);

      // Sagittal slab through the arm: vertices within 22 mm of the humerus
      // axis in x, so the slice follows the arm rather than a fixed plane.
      // Bounded to the arm sleeve by perpendicular distance from the humerus
      // axis. A plain x-slab reaches the lat and ribcage behind the arm, which
      // inflates the measured thickness and drags the midline backwards — the
      // very bias this test exists to detect.
      const TOP = shoulder.y + 0.055;
      const BANDS = 16;
      const STEP = 0.018;
      console.log('\n  band y      n   back z   front z   midline   thick   axis z   axis-midline');
      let capOffsets: number[] = [];
      let shaftOffsets: number[] = [];
      for (let b = 0; b < BANDS; b += 1) {
        const yHi = TOP - b * STEP;
        const yLo = yHi - STEP;
        const yMid = (yHi + yLo) / 2;
        const t = (yMid - shoulder.y) / axis.y;
        const axisZ = shoulder.z + axis.z * t;
        let back = Infinity, front = -Infinity, n = 0;
        for (let index = 0; index < count; index += 1) {
          posedPoint(body, index, point);
          if (point.y < yLo || point.y >= yHi) continue;
          if (armShare[index] < 0.7) continue;
          back = Math.min(back, point.z);
          front = Math.max(front, point.z);
          n += 1;
        }
        if (n < 10) continue;
        const midline = (back + front) / 2;
        const offset = axisZ - midline;
        if (yMid > shoulder.y - 0.02) capOffsets.push(offset);
        else shaftOffsets.push(offset);
        console.log(
          `  ${mm(yMid).padStart(7)} ${String(n).padStart(5)} ${mm(back).padStart(8)} ${mm(front).padStart(9)} `
          + `${mm(midline).padStart(9)} ${mm(front - back).padStart(7)} ${mm(axisZ).padStart(8)} ${mm(offset).padStart(14)}`,
        );
      }
      const mean = (l: number[]) => (l.length ? l.reduce((a, c) => a + c, 0) / l.length : NaN);
      console.log(`\n  >> mean axis-minus-midline over the CAP  (at/above the joint): ${mm(mean(capOffsets))} mm`);
      console.log(`  >> mean axis-minus-midline over the SHAFT (below the joint): ${mm(mean(shaftOffsets))} mm`);
      console.log('     (+ = the bone runs ahead of the mass it sits in)');
      // Dump posed vertices so mesh movement can be diffed between rig states
      // independently of the joint movement reported above.
      if (process.env.DUMP) {
        const out = new Float64Array(count * 3);
        for (let index = 0; index < count; index += 1) {
          posedPoint(body, index, point);
          out[index * 3] = point.x; out[index * 3 + 1] = point.y; out[index * 3 + 2] = point.z;
        }
        writeFileSync(process.env.DUMP, Buffer.from(out.buffer));
        const armOut = Buffer.from(new Float32Array(armShare).buffer);
        writeFileSync(`${process.env.DUMP}.share`, armOut);
        console.log(`  dumped ${count} posed vertices to ${process.env.DUMP}`);
      }
      character.dispose?.();
    }
  }, 900_000);
});
