import { describe, expect, it } from 'vitest';
import { AnimationClip, AnimationMixer, Object3D, Quaternion, Vector3 } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { generateClip } from '../animation/generate';
import { resolveFrame } from '../animation/pipeline';
import { lockAnchors } from '../constraints/locks';
import { sampleClip } from '../animation/clip';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { bakeClip } from './clipBuilder';
import { buildSkinnedRig } from './rigBuilder';
import { exportAnimationJson, exportMetadataJson, SKELETON_ID } from './json';
import { exportGlb } from './glb';

const skeleton = canonicalSkeleton;
const studioClip = generateClip(skeleton, bicepCurl);

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

  it('binds every vertex to exactly one bone', () => {
    const weights = rig.mesh.geometry.getAttribute('skinWeight');
    for (let index = 0; index < weights.count; index += 1) {
      expect(weights.getX(index)).toBe(1);
      expect(weights.getY(index)).toBe(0);
    }
  });

  it('stands in the rest pose at bind time', () => {
    rig.root.updateMatrixWorld(true);
    const evaluation = new PoseEvaluation(skeleton).apply(sampleClip(studioClip, 0).pose);
    const head = rig.boneByName.get('head')!;
    const exported = new Vector3().setFromMatrixPosition(head.matrixWorld);
    // The bind pose is the rig's rest pose, so bones start where the rig says.
    expect(exported.distanceTo(evaluation.head('head', new Vector3()))).toBeLessThan(0.35);
  });
});

describe('baked animation', () => {
  const baked = bakeClip(studioClip, skeleton, { fps: 30 });

  it('samples the whole clip and lands exactly on the loop point', () => {
    expect(baked.times[0]).toBe(0);
    expect(baked.times.at(-1)).toBeCloseTo(studioClip.duration, 9);
    expect(baked.clip.duration).toBeCloseTo(studioClip.duration, 9);
  });

  it('drops tracks for bones that never move', () => {
    const names = baked.clip.tracks.map((track) => track.name);
    expect(names).toContain('forearm_l.quaternion');
    // Bones held at a non-rest angle keep a two-key track; only bones actually
    // at rest are dropped.
    expect(names).toContain('thigh_l.quaternion');
    expect(names).not.toContain('toe_l.quaternion');
    const thigh = baked.clip.tracks.find((entry) => entry.name === 'thigh_l.quaternion')!;
    expect(thigh.times).toHaveLength(2);
  });

  it('returns to its opening pose so the loop is seamless', () => {
    const track = baked.clip.tracks.find((entry) => entry.name === 'forearm_l.quaternion')!;
    // Normalised, because the track stores float32 and `angleTo` is sensitive
    // to a norm that is a rounding error away from one.
    const first = new Quaternion().fromArray(Array.from(track.values.slice(0, 4))).normalize();
    const last = new Quaternion().fromArray(Array.from(track.values.slice(-4))).normalize();
    expect(first.angleTo(last)).toBeLessThan(1e-5);
  });

  it('reproduces the studio pose when played back through three.js', () => {
    // Play the baked clip on the exported rig and compare bone positions with
    // the studio's own pipeline: an export that does not match is worthless.
    const rig = buildSkinnedRig(skeleton);
    const holder = new Object3D();
    holder.add(rig.mesh);
    const mixer = new AnimationMixer(holder);
    const action = mixer.clipAction(baked.clip);
    action.play();

    const evaluation = new PoseEvaluation(skeleton);
    const anchors = lockAnchors(evaluation, sampleClip(studioClip, 0).pose, studioClip.locks);

    for (const time of [0, 1, 2, 3.5, 5]) {
      mixer.setTime(time);
      holder.updateMatrixWorld(true);
      const frame = resolveFrame(skeleton, evaluation, studioClip, time, { anchors });
      evaluation.apply(frame.pose);

      for (const name of ['hand_l', 'hand_r', 'foot_l', 'head'] as const) {
        const exported = new Vector3().setFromMatrixPosition(rig.boneByName.get(name)!.matrixWorld);
        const expected = evaluation.head(name, new Vector3());
        expect(exported.distanceTo(expected), `${name} at ${time}s`).toBeLessThan(2e-3);
      }
    }
  });
});

describe('json export', () => {
  it('writes an animation file that three.js can read back', () => {
    const json = exportAnimationJson(studioClip, bicepCurl, skeleton, 30);
    expect(json.format).toBe('hgpt-animation');
    expect(json.name).toBe('bicep_curl');
    expect(json.skeleton).toBe(SKELETON_ID);
    expect(json.tracks.length).toBeGreaterThan(4);

    const parsed = AnimationClip.parse(json.threeClip as never);
    expect(parsed.duration).toBeCloseTo(studioClip.duration, 6);
    expect(parsed.tracks.map((track) => track.name)).toContain('forearm_l.quaternion');
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
      animations: { name: string; channels: unknown[] }[];
      nodes: { name?: string }[];
      skins: unknown[];
      meshes: unknown[];
    };

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

  it('can export the animation without the character mesh', async () => {
    const blob = await exportGlb(studioClip, bicepCurl, { fps: 20, clipOnly: true });
    const buffer = await blob.arrayBuffer();
    const view = new DataView(buffer);
    const jsonLength = view.getUint32(12, true);
    const json = JSON.parse(
      new TextDecoder().decode(new Uint8Array(buffer, 20, jsonLength)),
    ) as { meshes?: unknown[]; animations: unknown[]; nodes: { name?: string }[] };

    expect(json.animations).toHaveLength(1);
    expect(json.meshes ?? []).toHaveLength(0);
    expect(json.nodes.map((node) => node.name)).toContain('pelvis');
    // Much smaller than the full export — that is the point of the option.
    const full = await exportGlb(studioClip, bicepCurl, { fps: 20 });
    expect(buffer.byteLength).toBeLessThan((await full.arrayBuffer()).byteLength);
  });
});
