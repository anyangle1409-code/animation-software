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
 * Side-view shoulder alignment: is the deltoid cap sitting forward of the
 * humerus and forward of the torso, and if so is that the pose or the mesh?
 *
 * +z is the model's front, and the character's LEFT arm is at +x. Sides are
 * selected by the dominant bone's own L/R suffix rather than by x sign, and the
 * ribcage reference is taken near the midline at chest height — a band at
 * shoulder height lands on the neck and trapezius, not the chest.
 */
const rig = canonicalSkeleton;
const FRAMES: [string, number][] = [['Bottom', 0], ['Peak', 2.5]];

const load = async () => {
  const bytes = readFileSync(process.env.GLB!);
  const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
  return retargetedCharacterSource({ id: 'shoulderz', label: 'shoulderz', data }).build(rig);
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

function posedPoint(mesh: SkinnedMesh, index: number, out: Vector3, skin: boolean): Vector3 {
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
  if (skin) mesh.applyBoneTransform(index, out);
  return mesh.localToWorld(out);
}

const mm = (v: number) => (v * 1000).toFixed(1);

describe('side-view shoulder alignment', () => {
  it('locates the deltoid cap against the humerus and the ribcage', async () => {
    const character = await load();
    const body = (character.meshes as SkinnedMesh[]).find((m) => /freeman/i.test(m.name))!;
    const count = body.geometry.getAttribute('position').count;
    const clip = generateClip(rig, bicepCurl);
    const evaluation = new PoseEvaluation(rig);
    const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
    const regions = Array.from({ length: count }, (_, index) => dominant(body, index));

    const analyse = (mesh: SkinnedMesh, skin: boolean, label: string, at: (n: string) => Vector3 | null) => {
      console.log(`\n=== ${label} ===`);
      const spine = at('spine_03')!;
      const point = new Vector3();

      // Ribcage reference: near the midline at chest height, so front is the
      // sternum and back is the surface over the thoracic spine.
      let chestFront = -Infinity, chestBack = Infinity, chestN = 0;
      for (let index = 0; index < count; index += 1) {
        if (!/^(spine|breast)/i.test(regions[index])) continue;
        posedPoint(mesh, index, point, skin);
        if (Math.abs(point.y - spine.y) > 0.045) continue;
        if (Math.abs(point.x) > 0.06) continue;
        chestFront = Math.max(chestFront, point.z);
        chestBack = Math.min(chestBack, point.z);
        chestN += 1;
      }
      const chestCentre = (chestFront + chestBack) / 2;
      console.log(`RIBCAGE near midline at y=${mm(spine.y)} (${chestN} vtx): sternum ${mm(chestFront)}  back ${mm(chestBack)}  mid-depth ${mm(chestCentre)}  depth ${mm(chestFront - chestBack)}`);

      for (const side of ['l', 'r'] as const) {
        const S = side.toUpperCase();
        const shoulder = at(`upperarm_${side}`)!;
        const elbow = at(`forearm_${side}`)!;
        const clavicle = at(`clavicle_${side}`);
        const axis = elbow.clone().sub(shoulder).normalize();

        // Trunk surface at the shoulder joint's own height, so "in line with
        // the torso" is measured where the shoulder actually sits.
        let trunkFront = -Infinity, trunkBack = Infinity;
        for (let index = 0; index < count; index += 1) {
          if (!/^(spine|breast)/i.test(regions[index])) continue;
          posedPoint(mesh, index, point, skin);
          if (Math.abs(point.y - shoulder.y) > 0.03) continue;
          if (Math.abs(point.x) > 0.08) continue;
          trunkFront = Math.max(trunkFront, point.z);
          trunkBack = Math.min(trunkBack, point.z);
        }
        const trunkCentre = (trunkFront + trunkBack) / 2;

        let capSum = 0, axisSum = 0, capN = 0;
        let capFront = -Infinity, capBack = Infinity;
        let apexY = -Infinity, apexZ = 0, apexAxis = 0;
        for (let index = 0; index < count; index += 1) {
          const region = regions[index];
          if (!/^(shoulder|upper_?arm)/i.test(region)) continue;
          if (!region.toUpperCase().includes(S) || region.toUpperCase().includes(S === 'L' ? 'R' : 'L')) continue;
          posedPoint(mesh, index, point, skin);
          const along = point.clone().sub(shoulder).dot(axis);
          if (along < -0.02 || along > 0.06) continue;
          const onAxis = shoulder.z + axis.z * along;
          capSum += point.z;
          axisSum += onAxis;
          capFront = Math.max(capFront, point.z);
          capBack = Math.min(capBack, point.z);
          capN += 1;
          if (point.y > apexY) { apexY = point.y; apexZ = point.z; apexAxis = onAxis; }
        }
        if (!capN) { console.log(`  ${S}: no cap vertices found`); continue; }
        const capCentre = capSum / capN;
        const axisCentre = axisSum / capN;
        console.log(`  --- ${S} arm (${capN} cap vtx) ---`);
        console.log(`    joints z: clavicle ${clavicle ? mm(clavicle.z) : '—'}  shoulder ${mm(shoulder.z)}  elbow ${mm(elbow.z)}`);
        console.log(`    trunk at shoulder height: front ${mm(trunkFront)} back ${mm(trunkBack)} mid ${mm(trunkCentre)}`);
        console.log(`    cap: front ${mm(capFront)} back ${mm(capBack)} centroid ${mm(capCentre)}  axis ${mm(axisCentre)}`);
        console.log(`    >> cap centroid - humerus axis : ${mm(capCentre - axisCentre)} mm   (+ = cap forward of the bone)`);
        console.log(`    >> cap apex     - humerus axis : ${mm(apexZ - apexAxis)} mm`);
        console.log(`    >> shoulder joint - trunk mid  : ${mm(shoulder.z - trunkCentre)} mm`);
        console.log(`    >> shoulder joint - sternum    : ${mm(shoulder.z - chestFront)} mm   (+ = joint in front of the sternum skin)`);
        console.log(`    >> shoulder joint - ribcage mid: ${mm(shoulder.z - chestCentre)} mm`);
        console.log(`    >> cap front - sternum         : ${mm(capFront - chestFront)} mm`);
      }
    };

    for (const [label, time] of FRAMES) {
      const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
      applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
      body.skeleton.update();
      body.updateWorldMatrix(true, false);
      analyse(body, true, `${label} (t=${time}s), posed`, (name) => {
        const bone = character.boneByName.get(name as never) as { matrixWorld: never } | undefined;
        return bone ? new Vector3().setFromMatrixPosition(bone.matrixWorld) : null;
      });
    }

    // The imported bind pose, unskinned: the part the curl cannot be blamed for.
    const fresh = await load();
    const bindBody = (fresh.meshes as SkinnedMesh[]).find((m) => /freeman/i.test(m.name))!;
    bindBody.updateWorldMatrix(true, true);
    for (const bone of bindBody.skeleton.bones) bone.updateWorldMatrix(true, false);
    regions.length = 0;
    regions.push(...Array.from({ length: count }, (_, index) => dominant(bindBody, index)));
    analyse(bindBody, false, 'BIND POSE (imported rest, unskinned geometry)', (name) => {
      const bone = fresh.boneByName.get(name as never) as { matrixWorld: never } | undefined;
      return bone ? new Vector3().setFromMatrixPosition(bone.matrixWorld) : null;
    });
  }, 240_000);
});
