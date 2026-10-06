import { describe, expect, it } from 'vitest';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import type { BoneName } from '../rig/boneNames';
import { generateClip } from '../animation/generate';
import { resolveFrame } from '../animation/pipeline';
import { lockAnchors } from '../constraints/locks';
import { sampleClip } from '../animation/clip';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { cablePushdown } from '../exercises/definitions/cablePushdown';
import { inclineCurl } from '../exercises/definitions/inclineCurl';
import { buildSkinnedRig } from './rigBuilder';
import { exportAnimationJson, exportMetadataJson, SKELETON_ID } from './json';
import { exportGlb } from './glb';
import { applyCharacterPose } from '../character/pose';
import { parseHgGlb } from '../core/glbContainer';
import { readHgGltfAnimations, type HgGltfAnimationChannel } from '../core/gltfAnimation';
import { hgRuntimeNodeNames } from '../core/gltfRuntimeNames';
import { HgQuat, HgVec3 } from '../core/linearMath';
import type { HgObject3D } from '../core/sceneGraph';
import { loadHgFirstPartyScene } from '../character/gltfFirstPartyScene';
import { bakeClipData } from './clipData';

const skeleton = canonicalSkeleton;
const studioClip = generateClip(skeleton, bicepCurl);

/**
 * A bone and the joints above it, counted as joints rather than bones: a bone
 * hinged exactly at its parent's head (the upper arm under the scapula) adds
 * no joint between itself and the clavicle, so it adds no step either. For
 * every bone of the 53-bone rig this is exactly its chain to the root.
 */
const jointChain = (name: BoneName): BoneName[] => {
  const chain = [name];
  for (let parent = skeleton.jointParent(name); parent; parent = skeleton.jointParent(parent)) chain.push(parent);
  return chain;
};

describe('skinned rig', () => {
  const rig = buildSkinnedRig(skeleton);

  it('mirrors the canonical hierarchy bone for bone', () => {
    expect(rig.bones).toHaveLength(skeleton.bones.length);
    for (const bone of skeleton.bones) {
      const exported = rig.boneByName.get(bone.name);
      expect(exported, bone.name).toBeDefined();
      // The root bone hangs off the skinned mesh; everything else keeps its
      // canonical parent.
      const parent = exported!.parent?.name ?? null;
      expect(parent, bone.name).toBe(bone.parent ?? 'HGPT_Mannequin');
    }
  });

  it('weights every vertex to its own bone, sharing only across a real joint', () => {
    const weights = rig.mesh.geometry.getAttribute('skinWeight');
    const bones = rig.mesh.geometry.getAttribute('skinIndex');
    let shared = 0;

    for (let index = 0; index < weights.count; index += 1) {
      const sum = weights.getX(index) + weights.getY(index);
      expect(sum, `vertex ${index}`).toBeCloseTo(1, 5);
      expect(weights.getZ(index)).toBe(0);
      expect(weights.getW(index)).toBe(0);

      if (weights.getY(index) === 0) continue;
      shared += 1;
      // A vertex may only be shared with a bone on the other side of one of
      // its own joints — its parent or one of its children. That is what makes
      // a joint crease instead of a limb detaching.
      const own = skeleton.bones[bones.getX(index)];
      const other = skeleton.bones[bones.getY(index)];
      const ownChain = jointChain(own.name);
      const otherChain = jointChain(other.name);
      let jointDistance = Infinity;
      ownChain.forEach((name, ownSteps) => {
        const otherSteps = otherChain.indexOf(name);
        if (otherSteps >= 0) jointDistance = Math.min(jointDistance, ownSteps + otherSteps);
      });
      // Detailed shoulder skin legitimately bridges the upper arm and thorax
      // across the clavicle. Anything farther apart is a corrupt binding.
      const fingerWeb =
        /^(thumb|index|middle|ring|pinky)_/.test(own.name) &&
        /^(thumb|index|middle|ring|pinky)_/.test(other.name) &&
        own.name.endsWith(other.name.slice(-2));
      const jointed = jointDistance <= 3 || fingerWeb;
      expect(jointed, `vertex ${index}: ${own.name} shared with ${other.name}`).toBe(true);
    }

    // The whole point of the body mesh: joints are shared, not rigid.
    expect(shared).toBeGreaterThan(weights.count * 0.1);
  });

  it('stands in the rest pose at bind time', () => {
    rig.root.updateMatrixWorld(true);
    const evaluation = new PoseEvaluation(skeleton).apply(sampleClip(studioClip, 0).pose);
    const head = rig.boneByName.get('head')!;
    const exported = new HgVec3().setFromMatrixPosition(head.matrixWorld);
    // The bind pose is the rig's rest pose, so bones start where the rig says.
    expect(exported.distanceTo(evaluation.head('head', new HgVec3()))).toBeLessThan(0.35);
  });

  it('keeps the complete skin together in the contracted curl pose', () => {
    const posed = buildSkinnedRig(skeleton);
    const evaluation = new PoseEvaluation(skeleton);
    const anchors = lockAnchors(evaluation, sampleClip(studioClip, 0).pose, studioClip.locks);
    const frame = resolveFrame(skeleton, evaluation, studioClip, 2, { anchors });
    applyCharacterPose({
      source: 'skin-test',
      root: posed.root,
      bones: posed.bones,
      boneByName: posed.boneByName,
      skeleton: posed.skeleton,
      object: posed.mesh,
      meshes: [posed.mesh],
      deformation: null,
      capabilities: { anatomy: false, textured: false },
      dispose() {},
    }, skeleton, frame.pose, evaluation);
    posed.root.updateMatrixWorld(true);
    posed.skeleton.update();

    const positions = posed.mesh.geometry.getAttribute('position');
    const point = new HgVec3();
    const transformed: HgVec3[] = [];
    for (let index = 0; index < positions.count; index += 1) {
      point.set(positions.getX(index), positions.getY(index), positions.getZ(index));
      posed.mesh.applyBoneTransform(index, point);
      expect(Number.isFinite(point.x) && Number.isFinite(point.y) && Number.isFinite(point.z)).toBe(true);
      // This catches a mesh bound in a different rest pose: fingers and limb
      // strips otherwise explode metres away while all bone-only tests pass.
      expect(Math.abs(point.x), `vertex ${index} x`).toBeLessThan(0.65);
      expect(point.y, `vertex ${index} y`).toBeGreaterThan(-0.1);
      expect(point.y, `vertex ${index} y`).toBeLessThan(1.9);
      expect(Math.abs(point.z), `vertex ${index} z`).toBeLessThan(0.65);
      transformed.push(point.clone());
    }

    const triangles = posed.mesh.geometry.getIndex()!;
    const bindA = new HgVec3();
    const bindB = new HgVec3();
    const bindC = new HgVec3();
    for (let index = 0; index < triangles.count; index += 3) {
      const ia = triangles.getX(index);
      const ib = triangles.getX(index + 1);
      const ic = triangles.getX(index + 2);
      const a = transformed[ia];
      const b = transformed[ib];
      const c = transformed[ic];
      bindA.set(positions.getX(ia), positions.getY(ia), positions.getZ(ia));
      bindB.set(positions.getX(ib), positions.getY(ib), positions.getZ(ib));
      bindC.set(positions.getX(ic), positions.getY(ic), positions.getZ(ic));
      const bindMax = Math.max(
        bindA.distanceTo(bindB),
        bindB.distanceTo(bindC),
        bindC.distanceTo(bindA),
      );
      const posedMax = Math.max(a.distanceTo(b), b.distanceTo(c), c.distanceTo(a));
      // Topology density is allowed to change between first-party surfaces.
      // What must not change is a triangle exploding relative to its own bind
      // size. This catches metre-long strips/fans without encoding the removed
      // anatomical mesh's absolute edge length.
      expect(posedMax / Math.max(bindMax, 1e-8), `triangle ${index / 3}`).toBeLessThan(1.75);
      expect(posedMax, `triangle ${index / 3} absolute size`).toBeLessThan(0.2);
    }
  });
});

describe('baked animation', () => {
  const baked = bakeClipData(studioClip, skeleton, { fps: 30 });

  it('samples the whole clip and lands exactly on the loop point', () => {
    expect(baked.times[0]).toBe(0);
    expect(baked.times.at(-1)).toBeCloseTo(studioClip.duration, 9);
    expect(baked.duration).toBeCloseTo(studioClip.duration, 9);
  });

  it('drops tracks for bones that never move', () => {
    const names = baked.tracks.map((track) => `${track.bone}.${track.property}`);
    expect(names).toContain('forearm_l.quaternion');
    // Bones held at a non-rest angle keep a two-key track; only bones actually
    // at rest are dropped.
    expect(names).toContain('thigh_l.quaternion');
    expect(names).not.toContain('toe_l.quaternion');
    const thigh = baked.tracks.find(
      (entry) => entry.bone === 'thigh_l' && entry.property === 'quaternion',
    )!;
    expect(thigh.times).toHaveLength(2);
  });

  it('returns to its opening pose so the loop is seamless', () => {
    const track = baked.tracks.find(
      (entry) => entry.bone === 'forearm_l' && entry.property === 'quaternion',
    )!;
    // Normalised, because the track stores float32 and angleTo is sensitive
    // to a norm that is a rounding error away from one.
    const first = new HgQuat(
      track.values[0], track.values[1], track.values[2], track.values[3],
    ).normalize();
    const offset = track.values.length - 4;
    const last = new HgQuat(
      track.values[offset], track.values[offset + 1],
      track.values[offset + 2], track.values[offset + 3],
    ).normalize();
    expect(first.angleTo(last)).toBeLessThan(1e-5);
  });

  it('reproduces the studio pose when the real exported GLB is played by first-party animation data', async () => {
    const blob = await exportGlb(studioClip, bicepCurl, {
      fps: 30,
      clipOnly: true,
    });
    const buffer = await blob.arrayBuffer();
    const document = parseHgGlb(buffer);
    const animations = readHgGltfAnimations(document);
    expect(animations).toHaveLength(1);
    const scene = await loadHgFirstPartyScene(buffer);

    const jsonNodes = document.json.nodes as Array<{ name?: string }>;
    const runtimeNames = hgRuntimeNodeNames(jsonNodes.map((node) => node.name ?? ''));
    const byName = new Map<string, HgObject3D>();
    scene.traverse((object) => {
      if (object.name) byName.set(object.name, object);
    });
    const objects = runtimeNames.map((name) => byName.get(name) ?? null);

    const sample = (channel: HgGltfAnimationChannel, time: number) => {
      const { times, values, valueSize } = channel;
      if (time <= times[0]) return values.slice(0, valueSize);
      const last = times.length - 1;
      if (time >= times[last]) return values.slice(last * valueSize, (last + 1) * valueSize);
      let upper = 1;
      while (upper < times.length && time > times[upper]) upper += 1;
      const lower = upper - 1;
      const alpha = (time - times[lower]) / (times[upper] - times[lower]);
      const from = values.slice(lower * valueSize, (lower + 1) * valueSize);
      const to = values.slice(upper * valueSize, (upper + 1) * valueSize);
      if (channel.path === 'rotation') {
        const q = new HgQuat(from[0], from[1], from[2], from[3]).normalize()
          .slerp(new HgQuat(to[0], to[1], to[2], to[3]).normalize(), alpha)
          .normalize();
        return q.toArray();
      }
      return from.map((value, index) => value + (to[index] - value) * alpha);
    };

    const applyAnimation = (time: number) => {
      for (const channel of animations[0].channels) {
        const object = objects[channel.node];
        if (!object) throw new Error(`Missing runtime node ${channel.node}`);
        const values = sample(channel, time);
        if (channel.path === 'translation') object.position.set(values[0], values[1], values[2]);
        else if (channel.path === 'rotation') object.quaternion.set(values[0], values[1], values[2], values[3]);
        else if (channel.path === 'scale') object.scale.set(values[0], values[1], values[2]);
        object.matrixWorldNeedsUpdate = true;
      }
      scene.updateMatrixWorld(true);
    };

    const evaluation = new PoseEvaluation(skeleton);
    const anchors = lockAnchors(evaluation, sampleClip(studioClip, 0).pose, studioClip.locks);

    for (const time of [0, 1, 2, 3.5, 5]) {
      applyAnimation(time);
      const frame = resolveFrame(skeleton, evaluation, studioClip, time, { anchors });
      evaluation.apply(frame.pose);

      for (const name of ['hand_l', 'hand_r', 'foot_l', 'head'] as const) {
        const node = byName.get(name);
        expect(node, name).toBeDefined();
        const exported = new HgVec3().setFromMatrixPosition(node!.matrixWorld);
        const expected = evaluation.head(name, new HgVec3());
        expect(exported.distanceTo(expected), `${name} at ${time}s`).toBeLessThan(2e-3);
      }
    }
  });
});

describe('json export', () => {
  it('reports the live canonical v4 rig identity', () => {
    expect(SKELETON_ID).toBe('hgpt_canonical_v4_original');
    expect(exportAnimationJson(studioClip, bicepCurl, skeleton, 30).skeleton).toBe(SKELETON_ID);
    expect(exportMetadataJson(bicepCurl).derived.skeleton).toBe(SKELETON_ID);
  });

  it('writes the legacy Three-compatible JSON shape from first-party baked data', () => {
    const json = exportAnimationJson(studioClip, bicepCurl, skeleton, 30);
    expect(json.format).toBe('hgpt-animation');
    expect(json.name).toBe('bicep_curl');
    expect(json.skeleton).toBe(SKELETON_ID);
    expect(json.tracks.length).toBeGreaterThan(4);

    const parsed = json.threeClip as {
      duration: number;
      uuid: string;
      blendMode: number;
      tracks: Array<{ name: string; type: string; times: number[]; values: number[] }>;
    };
    expect(parsed.duration).toBeCloseTo(studioClip.duration, 6);
    expect(parsed.uuid).toBe('hgpt-clip-bicep_curl');
    expect(parsed.blendMode).toBe(2500);
    expect(parsed.tracks.map((track) => track.name)).toContain('forearm_l.quaternion');
    expect(parsed.tracks.find((track) => track.name === 'forearm_l.quaternion')?.type)
      .toBe('quaternion');
  });

  it('writes exercise metadata with the derived phase timings', () => {
    const json = exportMetadataJson(bicepCurl);
    expect(json.exercise.id).toBe('dumbbell_bicep_curl');
    expect(json.derived.repetitionDuration).toBeCloseTo(5.5, 6);
    expect(json.derived.phases.map((phase) => phase.id)).toEqual([
      'concentric',
      'squeeze',
      'eccentric',
      'reset',
    ]);
    expect(json.derived.muscles.primary).toEqual([{ id: 'biceps', label: 'Biceps' }]);
    // The technique rules travel with the exercise, not just the animation.
    expect(json.exercise.technique.length).toBeGreaterThan(10);
  });

  it('is stable across runs', () => {
    const a = JSON.stringify(exportAnimationJson(studioClip, bicepCurl, skeleton, 30));
    const b = JSON.stringify(exportAnimationJson(studioClip, bicepCurl, skeleton, 30));
    expect(a).toBe(b);
  });
});

describe('glb export', () => {
  it('writes a valid binary glTF containing the rig and the clip', async () => {
    const blob = await exportGlb(studioClip, bicepCurl, { fps: 20 });
    const buffer = await blob.arrayBuffer();
    const view = new DataView(buffer);

    // glTF binary header: magic, version 2, total length.
    expect(view.getUint32(0, true)).toBe(0x46546c67);
    expect(view.getUint32(4, true)).toBe(2);
    expect(view.getUint32(8, true)).toBe(buffer.byteLength);

    const jsonLength = view.getUint32(12, true);
    const json = JSON.parse(
      new TextDecoder().decode(new Uint8Array(buffer, 20, jsonLength)),
    ) as {
      asset: { generator?: string };
      animations: { name: string; channels: unknown[] }[];
      nodes: { name?: string }[];
      skins: unknown[];
      meshes: unknown[];
    };

    expect(json.asset.generator).toBe('Home Gym PT first-party codec');
    expect(json.animations).toHaveLength(1);
    expect(json.animations[0].name).toBe('bicep_curl');
    expect(json.animations[0].channels.length).toBeGreaterThan(5);
    expect(json.skins).toHaveLength(1);
    expect(json.meshes.length).toBeGreaterThan(0);

    const names = json.nodes.map((node) => node.name);
    expect(names).toContain('forearm_l');
    expect(names).toContain('hand_r');
    // The dumbbells travel with the file, parented to the hands.
    expect(names.filter((name) => name?.includes('dumbbell')).length).toBe(2);
  });

  it('writes the clean canonical character with the first-party GLB codec when equipment is excluded', async () => {
    const blob = await exportGlb(studioClip, bicepCurl, { fps: 20, includeEquipment: false });
    const buffer = await blob.arrayBuffer();
    const view = new DataView(buffer);
    const jsonLength = view.getUint32(12, true);
    const json = JSON.parse(
      new TextDecoder().decode(new Uint8Array(buffer, 20, jsonLength)),
    ) as {
      asset: { generator?: string };
      animations: unknown[];
      meshes: unknown[];
      skins: unknown[];
      nodes: { name?: string }[];
    };

    expect(json.asset.generator).toBe('Home Gym PT first-party codec');
    expect(json.animations).toHaveLength(1);
    expect(json.meshes).toHaveLength(1);
    expect(json.skins).toHaveLength(1);
    expect(json.nodes.map((node) => node.name)).toContain('HGPT_Mannequin');
    expect(json.nodes.map((node) => node.name)).toContain('hand_r');
  });

  it('can export the animation without the character mesh', async () => {
    const blob = await exportGlb(studioClip, bicepCurl, { fps: 20, clipOnly: true });
    const buffer = await blob.arrayBuffer();
    const view = new DataView(buffer);
    const jsonLength = view.getUint32(12, true);
    const json = JSON.parse(
      new TextDecoder().decode(new Uint8Array(buffer, 20, jsonLength)),
    ) as {
      asset: { generator?: string };
      meshes?: unknown[];
      animations: unknown[];
      nodes: { name?: string }[];
    };

    expect(json.asset.generator).toBe('Home Gym PT first-party codec');
    expect(json.animations).toHaveLength(1);
    expect(json.meshes ?? []).toHaveLength(0);
    expect(json.nodes.map((node) => node.name)).toContain('pelvis');
    // Much smaller than the full export — that is the point of the option.
    const full = await exportGlb(studioClip, bicepCurl, { fps: 20 });
    expect(buffer.byteLength).toBeLessThan((await full.arrayBuffer()).byteLength);
  });

  /** The JSON chunk of an exported file. */
  async function gltfJson(exercise: typeof bicepCurl) {
    const buffer = await (await exportGlb(generateClip(skeleton, exercise), exercise, { fps: 20 })).arrayBuffer();
    const view = new DataView(buffer);
    return JSON.parse(new TextDecoder().decode(new Uint8Array(buffer, 20, view.getUint32(12, true)))) as {
      animations: { channels: { target: { node: number; path: string } }[] }[];
      nodes: { name?: string; rotation?: number[]; scale?: number[] }[];
    };
  }

  it('stretches a cable as it plays', async () => {
    const json = await gltfJson(cablePushdown);
    const cable = json.nodes.findIndex((node) => node.name === 'equipment_cable');
    const bar = json.nodes.findIndex((node) => node.name === 'equipment_bar');
    expect(cable).toBeGreaterThanOrEqual(0);
    expect(bar).toBeGreaterThanOrEqual(0);
    const paths = (node: number) =>
      json.animations[0].channels.filter((channel) => channel.target.node === node).map((channel) => channel.target.path);
    // The cable alone changes size; the bar only moves.
    expect(paths(cable).sort()).toEqual(['rotation', 'scale', 'translation']);
    expect(paths(bar).sort()).toEqual(['rotation', 'translation']);
    expect(json.nodes[cable].scale?.[1]).toBeGreaterThan(1);
  });

  it('turns static equipment as the studio does', async () => {
    // The incline curl's bench is turned round to face the lifter: 180° about Y.
    const json = await gltfJson(inclineCurl);
    const bench = json.nodes.find((node) => node.name === 'Incline bench');
    expect(bench?.rotation).toBeDefined();
    expect(Math.abs(bench!.rotation![1])).toBeCloseTo(1, 6);
  });
});
