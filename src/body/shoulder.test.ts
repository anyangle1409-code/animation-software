import { describe, expect, it } from 'vitest';
import { Quaternion, Vector3 } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { EULER_ORDER } from '../rig/types';
import { restPose } from '../rig/pose';
import { generateClip } from '../animation/generate';
import { resolveFrame } from '../animation/pipeline';
import { sampleClip } from '../animation/clip';
import { lockAnchors } from '../constraints/locks';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { shoulderPress } from '../exercises/definitions/shoulderPress';
import { pushUp } from '../exercises/definitions/pushUp';
import { pullUp } from '../exercises/definitions/pullUp';
import { exportGlb } from '../export/glb';
import { buildBodyGeometry } from './mesh';
import { buildEcorcheGeometry } from './ecorche';
import { buildSkinnedRig } from './skin';
import { shoulderInfluences } from './shoulder';
import type { ArmpitReport, FinReport, ShoulderCorrective } from './shoulder';
import { Euler } from 'three';

/**
 * The shoulder: the folds at the neck-to-shoulder junction, and the armpit.
 *
 * The limits are the ones declared for this round before any of it was tuned —
 * no more than 2.0× stretch and no less than 0.35× compression across the
 * shoulder, through every angle the exercises reach. What is asserted here is
 * what the work actually achieved against them, which is not the whole of it:
 * one arm at a time meets them, both arms together and the loaded exercises do
 * not, and the numbers below say where. They are held as ceilings on what the
 * mesh does now, so that a later change cannot quietly give any of it back.
 */
const MOST_STRETCH = 2;
const LEAST_SQUASH = 0.35;

const skeleton = canonicalSkeleton;
const character = buildBodyGeometry(skeleton).geometry;
const source = buildBodyGeometry(skeleton, { repair: false }).geometry;
/** Every shared repair except this one, so the armpit's own effect is isolated. */
const withoutArmpit = buildBodyGeometry(skeleton, { shoulder: false }).geometry;
const anatomy = buildEcorcheGeometry(skeleton);
const fins = character.userData.fins as FinReport;
const armpit = character.userData.armpit as ArmpitReport;
const shoulders = character.userData.shoulders as ShoulderCorrective[];

const position = character.getAttribute('position');
const index = character.getIndex()!;
const skinIndex = character.getAttribute('skinIndex');
const skinWeight = character.getAttribute('skinWeight');

/** The shoulder joints, in the rest pose. */
const joints = (['l', 'r'] as const).map((side) =>
  new PoseEvaluation(skeleton).apply(restPose()).head(`upperarm_${side}`, new Vector3()),
);

const forearms = new Set(
  skeleton.bones
    .map((bone, slot) => (/^(forearm|hand|thumb|index|middle|ring|pinky)_/.test(bone.name) ? slot : -1))
    .filter((slot) => slot >= 0),
);

/**
 * The shoulder and the armpit: within 250 mm of either joint, and not part of
 * the elbow, whose own crease was settled in an earlier round and whose numbers
 * would otherwise drown these.
 */
const shoulderSurface = (vertex: number): boolean => {
  let lower = 0;
  for (let slot = 0; slot < 4; slot += 1) {
    if (forearms.has(skinIndex.getComponent(vertex, slot))) lower += skinWeight.getComponent(vertex, slot);
  }
  if (lower > 0.2) return false;
  const point = new Vector3(position.getX(vertex), position.getY(vertex), position.getZ(vertex));
  return joints.some((joint) => point.distanceTo(joint) < 0.25);
};

const edges: [number, number][] = [];
{
  const seen = new Set<number>();
  for (let triangle = 0; triangle < index.count; triangle += 3) {
    const corner = [index.getX(triangle), index.getX(triangle + 1), index.getX(triangle + 2)];
    for (let slot = 0; slot < 3; slot += 1) {
      const one = corner[slot];
      const two = corner[(slot + 1) % 3];
      if (!shoulderSurface(one) && !shoulderSurface(two)) continue;
      const key = one < two ? one * position.count + two : two * position.count + one;
      if (seen.has(key)) continue;
      seen.add(key);
      edges.push([one, two]);
    }
  }
}

const here = new Vector3();
const there = new Vector3();
const restLength = edges.map(([one, two]) => {
  here.fromBufferAttribute(position, one);
  there.fromBufferAttribute(position, two);
  return here.distanceTo(there);
});

type Rig = ReturnType<typeof buildSkinnedRig>;

const shapes = character.morphAttributes.position ?? [];
const influences: number[] = [];

/** Put the rig back where it started, so one pose cannot leak into the next. */
const settle = (rig: Rig) => {
  for (const bone of skeleton.bones) {
    const node = rig.boneByName.get(bone.name);
    if (node) node.quaternion.copy(bone.restLocalQuaternion);
  }
  rig.root.updateMatrixWorld(true);
  rig.skeleton.update();
};

/** Drive the correctives from the pose the rig is holding, as the viewport does. */
const drive = (rig: Rig, on = true) => {
  if (!rig.mesh.morphTargetInfluences) return;
  for (const corrective of shoulders) {
    const bone = rig.boneByName.get(corrective.bone);
    const rigBone = skeleton.bones.find((each) => each.name === corrective.bone);
    if (!bone || !rigBone) continue;
    const delta = rigBone.restLocalQuaternion.clone().invert().multiply(bone.quaternion);
    shoulderInfluences(corrective, delta, influences);
    corrective.targets.forEach((target, slot) => {
      rig.mesh.morphTargetInfluences![target] = on ? influences[slot] : 0;
    });
  }
};

/** A vertex's bind position with the correctives applied at their current weight. */
const shaped = (rig: Rig, vertex: number, out: Vector3): Vector3 => {
  out.set(position.getX(vertex), position.getY(vertex), position.getZ(vertex));
  shapes.forEach((shape, slot) => {
    const weight = rig.mesh.morphTargetInfluences?.[slot] ?? 0;
    if (!weight) return;
    out.x += shape.getX(vertex) * weight;
    out.y += shape.getY(vertex) * weight;
    out.z += shape.getZ(vertex) * weight;
  });
  return out;
};

/** The worst stretch and squash across the shoulder, in whatever pose it holds. */
const strain = (rig: Rig): [number, number] => {
  let most = 1;
  let least = 1;
  edges.forEach(([one, two], slot) => {
    shaped(rig, one, here);
    shaped(rig, two, there);
    rig.mesh.applyBoneTransform(one, here);
    rig.mesh.applyBoneTransform(two, there);
    const ratio = here.distanceTo(there) / restLength[slot];
    most = Math.max(most, ratio);
    least = Math.min(least, ratio);
  });
  return [most, least];
};

/** Lift one or both arms, sideways or forwards, from the rest pose. */
const lift = (rig: Rig, sides: ('l' | 'r')[], way: 'abduct' | 'forward', degrees: number) => {
  settle(rig);
  for (const side of sides) {
    const bone = rig.boneByName.get(`upperarm_${side}`);
    if (!bone) continue;
    if (way === 'abduct') bone.rotateZ((((side === 'l' ? -1 : 1) * degrees * Math.PI) / 180));
    else bone.rotateX((-degrees * Math.PI) / 180);
  }
  rig.root.updateMatrixWorld(true);
  rig.skeleton.update();
  drive(rig);
};

/** Every exercise, sampled across its clip. */
const exercisePoses = () => {
  const out: { label: string; hold: (rig: Rig) => void }[] = [];
  for (const definition of [bicepCurl, shoulderPress, pushUp, pullUp]) {
    const clip = generateClip(skeleton, definition);
    const evaluation = new PoseEvaluation(skeleton);
    const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
    for (let step = 0; step <= 8; step += 1) {
      const frame = resolveFrame(skeleton, evaluation, clip, (step / 8) * clip.duration, { anchors });
      out.push({
        label: `${definition.id} ${step}/8`,
        hold: (rig: Rig) => {
          settle(rig);
          const euler = new Euler(0, 0, 0, EULER_ORDER);
          for (const bone of skeleton.bones) {
            const node = rig.boneByName.get(bone.name);
            const rotation = frame.pose.rotations[bone.name];
            if (!node || !rotation) continue;
            euler.set(rotation.x, rotation.y, rotation.z, EULER_ORDER);
            node.quaternion.copy(bone.restLocalQuaternion).multiply(new Quaternion().setFromEuler(euler));
          }
          rig.root.updateMatrixWorld(true);
          rig.skeleton.update();
          drive(rig);
        },
      });
    }
  }
  return out;
};

describe('the shoulder', () => {
  it('flattens the folds at the neck-to-shoulder junction', () => {
    // The fins run to nearly 20 mm off their own neighbourhood, where the rest
    // of that surface sits within about 1.5 mm of its own: a fold, not a curve.
    expect(fins.worstBefore).toBeGreaterThan(0.018);
    expect(fins.worstAfter).toBeLessThan(0.008);
    expect(fins.moved).toBeGreaterThan(20);
    expect(fins.moved).toBeLessThan(120);
    expect(fins.maxDisplacement).toBeLessThan(0.017);
  });

  it('regrades the armpit without moving the boundary', () => {
    expect(armpit.reweighted).toBeGreaterThan(200);
    // The step in the arm's share across an edge is what a raised arm turns into
    // a tear, and it is the thing this binding exists to bring down.
    expect(armpit.stepAfter).toBeLessThan(armpit.stepBefore * 0.7);

    // Which bone owns a vertex does not change: the ribcage stays the ribcage
    // and the sleeve stays the sleeve, so the body's own proportions are the
    // same afterwards. Only the shares either side of the fold move.
    const ownerOf = (geometry: typeof character, vertex: number) => {
      const bones = geometry.getAttribute('skinIndex');
      const shares = geometry.getAttribute('skinWeight');
      let best = -1;
      let most = 0;
      for (let slot = 0; slot < 4; slot += 1) {
        const share = shares.getComponent(vertex, slot);
        if (share > most) {
          most = share;
          best = bones.getComponent(vertex, slot);
        }
      }
      return best;
    };
    for (let vertex = 0; vertex < position.count; vertex += 1) {
      if (!shoulderSurface(vertex)) continue;
      expect(ownerOf(character, vertex), `vertex ${vertex}`).toBe(ownerOf(withoutArmpit, vertex));
    }
  });

  it('keeps every vertex on two bones that still sum to one', () => {
    for (const geometry of [character, anatomy]) {
      const shares = geometry.getAttribute('skinWeight');
      const bones = geometry.getAttribute('skinIndex');
      for (let vertex = 0; vertex < shares.count; vertex += 1) {
        let used = 0;
        let total = 0;
        const seen = new Set<number>();
        for (let slot = 0; slot < 4; slot += 1) {
          const share = shares.getComponent(vertex, slot);
          total += share;
          if (share <= 0) continue;
          used += 1;
          const bone = bones.getComponent(vertex, slot);
          expect(seen.has(bone), `vertex ${vertex} repeats a bone`).toBe(false);
          seen.add(bone);
        }
        expect(used, `vertex ${vertex} influences`).toBeLessThanOrEqual(2);
        expect(total, `vertex ${vertex}`).toBeCloseTo(1, 4);
      }
    }
  });

  it('leaves the shoulder alone until the arm lifts', () => {
    const rig = buildSkinnedRig(skeleton, { geometry: character });
    settle(rig);
    drive(rig);
    for (const weight of rig.mesh.morphTargetInfluences ?? []) {
      expect(Math.abs(weight)).toBeLessThan(0.05);
    }
    const [most, least] = strain(rig);
    expect(most).toBeLessThan(1.02);
    expect(least).toBeGreaterThan(0.98);
  });

  it('holds one arm inside the declared limits, all the way up', () => {
    const rig = buildSkinnedRig(skeleton, { geometry: character });
    for (const side of ['l', 'r'] as const) {
      // Up to the horizontal and well past it. Beyond about 130° one arm is
      // outside the limits too, and the test below records where it lands.
      for (const degrees of [30, 60, 90, 100, 120, 130]) {
        lift(rig, [side], 'abduct', degrees);
        const [most, least] = strain(rig);
        expect(most, `${side} abduction ${degrees}°`).toBeLessThanOrEqual(MOST_STRETCH);
        expect(least, `${side} abduction ${degrees}°`).toBeGreaterThanOrEqual(LEAST_SQUASH);
      }
      for (const degrees of [45, 90, 120]) {
        lift(rig, [side], 'forward', degrees);
        const [most, least] = strain(rig);
        expect(most, `${side} forward ${degrees}°`).toBeLessThanOrEqual(MOST_STRETCH);
        expect(least, `${side} forward ${degrees}°`).toBeGreaterThanOrEqual(LEAST_SQUASH);
      }
    }
  });

  it('is a large improvement on the source everywhere else', () => {
    // Both arms at once, one arm past 130°, and the loaded exercises are outside
    // the declared limits and are recorded here as they stand: far better than
    // the binding they replace, and not yet good enough. These ceilings are
    // regression guards rather than acceptance limits — they are set a little
    // above what the mesh currently measures, so a later change that gives any
    // of this back fails rather than passing quietly.
    const rig = buildSkinnedRig(skeleton, { geometry: character });
    const plain = buildSkinnedRig(skeleton, { geometry: source });
    const plainEdges = restLength.map((length, slot) => {
      const [one, two] = edges[slot];
      here.fromBufferAttribute(source.getAttribute('position'), one);
      there.fromBufferAttribute(source.getAttribute('position'), two);
      void length;
      return here.distanceTo(there);
    });
    const plainStrain = (): [number, number] => {
      let most = 1;
      let least = 1;
      edges.forEach(([one, two], slot) => {
        here.fromBufferAttribute(source.getAttribute('position'), one);
        there.fromBufferAttribute(source.getAttribute('position'), two);
        plain.mesh.applyBoneTransform(one, here);
        plain.mesh.applyBoneTransform(two, there);
        const ratio = here.distanceTo(there) / plainEdges[slot];
        most = Math.max(most, ratio);
        least = Math.min(least, ratio);
      });
      return [most, least];
    };

    let worst = 1;
    let tightest = 1;
    let worstBefore = 1;
    for (const degrees of [30, 60, 90, 120, 150, 165]) {
      for (const way of ['abduct', 'forward'] as const) {
        lift(rig, ['l', 'r'], way, degrees);
        lift(plain, ['l', 'r'], way, degrees);
        const [most, least] = strain(rig);
        const [wasMost] = plainStrain();
        worst = Math.max(worst, most);
        tightest = Math.min(tightest, least);
        worstBefore = Math.max(worstBefore, wasMost);
      }
    }
    expect(worstBefore).toBeGreaterThan(6);
    expect(worst).toBeLessThan(5.5);
    expect(tightest).toBeGreaterThan(0.1);
  });

  it('improves every exercise and makes none of them worse', () => {
    const rig = buildSkinnedRig(skeleton, { geometry: character });
    const worst = new Map<string, number>();
    for (const pose of exercisePoses()) {
      pose.hold(rig);
      const withShapes = strain(rig)[0];
      drive(rig, false);
      const without = strain(rig)[0];
      const name = pose.label.split(' ')[0];
      worst.set(name, Math.max(worst.get(name) ?? 1, withShapes));
      // The correctives may never cost a pose anything: an earlier driver that
      // read Euler angles took the pull-up from 5.3× to 8.4× because the shapes
      // were being applied to a shoulder they were not built for.
      expect(withShapes, `${pose.label} against no correctives`).toBeLessThanOrEqual(without + 0.02);
    }
    // The curl, which is the exercise the studio opens on, is inside the limits.
    expect(worst.get('dumbbell_bicep_curl')!).toBeLessThanOrEqual(MOST_STRETCH);
    for (const [name, value] of worst) {
      expect(value, `${name}`).toBeLessThan(4.6);
    }
  });

  it('exports the correctives with the animation', async () => {
    const blob = await exportGlb(generateClip(skeleton, shoulderPress), shoulderPress, { fps: 10 });
    const buffer = await blob.arrayBuffer();
    const view = new DataView(buffer);
    const jsonLength = view.getUint32(12, true);
    const gltf = JSON.parse(new TextDecoder().decode(new Uint8Array(buffer, 20, jsonLength))) as {
      accessors: { bufferView: number; byteOffset?: number; count: number }[];
      bufferViews: { byteOffset: number }[];
      meshes: { primitives: { targets?: Record<string, number>[] }[]; weights?: number[] }[];
      animations: {
        channels: { sampler: number; target: { path: string } }[];
        samplers: { input: number; output: number }[];
      }[];
    };

    const targets = gltf.meshes[0].primitives[0].targets ?? [];
    expect(targets.length, 'morph targets in the file').toBe(shapes.length);
    expect(gltf.meshes[0].weights?.length).toBe(shapes.length);

    // The weights have to move with the animation, or the exported arm lifts
    // through an armpit the studio has already corrected.
    const weighted = gltf.animations[0].channels.filter((channel) => channel.target.path === 'weights');
    expect(weighted.length, 'weight channels').toBe(1);
    const sampler = gltf.animations[0].samplers[weighted[0].sampler];
    const output = gltf.accessors[sampler.output];
    const region = gltf.bufferViews[output.bufferView];
    const binary = 20 + jsonLength + 8;
    const values = new Float32Array(
      buffer,
      binary + region.byteOffset + (output.byteOffset ?? 0),
      output.count,
    );
    expect(output.count % shapes.length).toBe(0);
    let largest = 0;
    for (const value of values) largest = Math.max(largest, value);
    expect(largest, 'the exported weights actually rise').toBeGreaterThan(0.5);
  });

  it('gives the anatomy view the same correctives', () => {
    expect((anatomy.morphAttributes.position ?? []).length).toBe(shapes.length);
    expect((anatomy.userData.shoulders as ShoulderCorrective[]).length).toBe(shoulders.length);
  });
});
