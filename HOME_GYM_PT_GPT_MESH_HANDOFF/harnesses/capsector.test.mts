import { readFileSync } from 'node:fs';
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
 * Is the deltoid cap centred on the humerus, and does it stand proud of the
 * chest at its own height?
 *
 * The cap is measured as a cross-section *around* the humerus axis rather than
 * as a z range over shoulder-weighted vertices: that set reaches back over the
 * scapula, which drags a centroid posterior and says nothing about whether the
 * deltoid bulges forward. +z is front; the character's left arm is at +x.
 */
const rig = canonicalSkeleton;
const FRAMES: [string, number][] = [['Bottom', 0], ['Peak', 2.5]];
const mm = (v: number) => (v * 1000).toFixed(1);
const deg = (r: number) => (r * 180) / Math.PI;

const load = async () => {
  const bytes = readFileSync(process.env.GLB!);
  const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
  return retargetedCharacterSource({ id: 'cap', label: 'cap', data }).build(rig);
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

describe('deltoid cap centring', () => {
  it('measures the cap cross-section around the humerus and against the chest', async () => {
    const character = await load();
    const body = (character.meshes as SkinnedMesh[]).find((m) => /freeman/i.test(m.name))!;
    const count = body.geometry.getAttribute('position').count;
    const regions = Array.from({ length: count }, (_, index) => dominant(body, index));
    const clip = generateClip(rig, bicepCurl);
    const evaluation = new PoseEvaluation(rig);
    const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);

    for (const [label, time] of FRAMES) {
      const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
      applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
      body.skeleton.update();
      body.updateWorldMatrix(true, false);
      console.log(`\n================ ${label} (t=${time}s) ================`);
      const at = (name: string) => {
        const bone = character.boneByName.get(name as never) as { matrixWorld: never } | undefined;
        return bone ? new Vector3().setFromMatrixPosition(bone.matrixWorld) : null;
      };
      const point = new Vector3();

      for (const side of ['l', 'r'] as const) {
        const S = side.toUpperCase();
        const suffix = new RegExp(`${S}\\d*$`);
        const shoulder = at(`upperarm_${side}`)!;
        const elbow = at(`forearm_${side}`)!;
        const axis = elbow.clone().sub(shoulder).normalize();
        // Sagittal tilt of the humerus: how far forward the arm hangs.
        const tilt = deg(Math.atan2(axis.z, -axis.y));

        // A frame perpendicular to the humerus: `front` is the model's +z with
        // the axial part removed, `out` is lateral.
        const front = new Vector3(0, 0, 1).addScaledVector(axis, -new Vector3(0, 0, 1).dot(axis)).normalize();
        const out = new Vector3().crossVectors(axis, front).normalize();

        const SECTORS: [string, number, number][] = [
          ['anterior', -35, 35],
          ['antero-lat', 35, 80],
          ['lateral', 80, 100],
          ['postero-lat', 100, 145],
          ['posterior', 145, 180],
        ];
        const radii = new Map<string, number[]>(SECTORS.map(([n]) => [n, []]));
        let offsetFront = 0, offsetOut = 0, capN = 0;
        for (let index = 0; index < count; index += 1) {
          const region = regions[index];
          if (!/^(shoulder|upper_?arm)/i.test(region) || !suffix.test(region)) continue;
          posedPoint(body, index, point);
          const rel = point.clone().sub(shoulder);
          const along = rel.dot(axis);
          if (along < -0.005 || along > 0.07) continue; // the cap band
          const radial = rel.addScaledVector(axis, -along);
          const f = radial.dot(front);
          const o = Math.abs(radial.dot(out));
          const r = Math.hypot(f, o);
          if (r < 1e-4) continue;
          offsetFront += f;
          offsetOut += o;
          capN += 1;
          const angle = deg(Math.atan2(o, f));
          for (const [name, lo, hi] of SECTORS) {
            if (angle >= lo && angle < hi) radii.get(name)!.push(r);
          }
        }

        // Chest at the shoulder's own height, across the full pec width, so
        // "proud of the chest" is measured where the deltoid actually sits.
        let chestFront = -Infinity, chestN = 0;
        for (let index = 0; index < count; index += 1) {
          if (!/^(spine|breast)/i.test(regions[index])) continue;
          posedPoint(body, index, point);
          if (Math.abs(point.y - shoulder.y) > 0.025) continue;
          if (Math.abs(point.x) > 0.13) continue;
          chestFront = Math.max(chestFront, point.z);
          chestN += 1;
        }
        let capFrontZ = -Infinity;
        for (let index = 0; index < count; index += 1) {
          const region = regions[index];
          if (!/^(shoulder|upper_?arm)/i.test(region) || !suffix.test(region)) continue;
          posedPoint(body, index, point);
          const along = point.clone().sub(shoulder).dot(axis);
          if (along < -0.005 || along > 0.07) continue;
          capFrontZ = Math.max(capFrontZ, point.z);
        }

        console.log(`  --- ${S} arm, ${capN} cap vertices ---`);
        console.log(`    humerus sagittal tilt: ${tilt.toFixed(2)}°  (+ = hanging forward of vertical)`);
        console.log(`    shoulder z ${mm(shoulder.z)}   elbow z ${mm(elbow.z)}`);
        console.log('    sector        n   mean r    max r');
        for (const [name] of SECTORS) {
          const list = radii.get(name)!;
          if (!list.length) { console.log(`    ${name.padEnd(12)} ${String(0).padStart(3)}       —        —`); continue; }
          const mean = list.reduce((a, b) => a + b, 0) / list.length;
          console.log(`    ${name.padEnd(12)} ${String(list.length).padStart(3)} ${mm(mean).padStart(7)} ${mm(Math.max(...list)).padStart(8)}`);
        }
        const ant = radii.get('anterior')!;
        const post = radii.get('posterior')!;
        const meanOf = (l: number[]) => (l.length ? l.reduce((a, b) => a + b, 0) / l.length : NaN);
        console.log(`    >> anterior mean r - posterior mean r : ${mm(meanOf(ant) - meanOf(post))} mm  (+ = cap bulges forward)`);
        console.log(`    >> cross-section centroid offset from the axis: front ${mm(offsetFront / capN)} mm, mean |lateral| ${mm(offsetOut / capN)} mm`);

        // The deltoid sleeve alone: within 70 mm of the humerus axis, which
        // drops the trapezius and neck vertices that reach 200 mm+ and
        // contaminate any sector mean.
        let sleeveFront = 0, sleeveN = 0, sleeveAntMax = 0, sleevePostMax = 0;
        for (let index = 0; index < count; index += 1) {
          const region = regions[index];
          if (!/^(shoulder|upper_?arm)/i.test(region) || !suffix.test(region)) continue;
          posedPoint(body, index, point);
          const rel = point.clone().sub(shoulder);
          const along = rel.dot(axis);
          if (along < -0.005 || along > 0.07) continue;
          const radial = rel.addScaledVector(axis, -along);
          if (radial.length() > 0.07) continue;
          const f = radial.dot(front);
          sleeveFront += f;
          sleeveN += 1;
          sleeveAntMax = Math.max(sleeveAntMax, f);
          sleevePostMax = Math.min(sleevePostMax, f);
        }
        console.log(`    DELTOID SLEEVE (r<70mm, ${sleeveN} vtx): centroid ${mm(sleeveFront / sleeveN)} mm forward of the axis`);
        console.log(`      reach: anterior ${mm(sleeveAntMax)} mm, posterior ${mm(sleevePostMax)} mm, asymmetry ${mm(sleeveAntMax + sleevePostMax)} mm`);
        // Sliced along the humerus: a bias concentrated at the top is the
        // anterior deltoid head standing proud, which is a local mesh defect.
        // A bias spread evenly is just the whole arm sitting forward.
        console.log('      slice along humerus   n   centroid fwd   ant reach   post reach');
        for (const [lo, hi] of [[-0.005, 0.015], [0.015, 0.033], [0.033, 0.051], [0.051, 0.07]] as [number, number][]) {
          let sf = 0, sn = 0, sa = -1e9, sp = 1e9;
          for (let index = 0; index < count; index += 1) {
            const region = regions[index];
            if (!/^(shoulder|upper_?arm)/i.test(region) || !suffix.test(region)) continue;
            posedPoint(body, index, point);
            const rel = point.clone().sub(shoulder);
            const along = rel.dot(axis);
            if (along < lo || along >= hi) continue;
            const radial = rel.addScaledVector(axis, -along);
            if (radial.length() > 0.07) continue;
            const f = radial.dot(front);
            sf += f; sn += 1;
            sa = Math.max(sa, f); sp = Math.min(sp, f);
          }
          const tag = `${(lo * 1000).toFixed(0)}..${(hi * 1000).toFixed(0)}mm`;
          console.log(`      ${tag.padEnd(20)} ${String(sn).padStart(3)} ${(sn ? mm(sf / sn) : '—').padStart(13)} ${(sn ? mm(sa) : '—').padStart(11)} ${(sn ? mm(sp) : '—').padStart(12)}`);
        }
        console.log(`    chest front at shoulder height (${chestN} vtx, |x|<130): ${mm(chestFront)}`);
        console.log(`    >> cap front - chest front at the same height: ${mm(capFrontZ - chestFront)} mm  (+ = deltoid proud of the chest)`);
      }
    }
  }, 240_000);
});
