import { describe, expect, it } from 'vitest';
import {
  Bone,
  BufferAttribute,
  BufferGeometry,
  Matrix4,
  MeshStandardMaterial,
  Quaternion,
  Skeleton as ThreeSkeleton,
  SkinnedMesh,
  Vector3,
} from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { generateClip } from '../animation/generate';
import { resolveFrame } from '../animation/pipeline';
import { lockAnchors } from '../constraints/locks';
import { sampleClip } from '../animation/clip';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { exportGlb } from '../export/glb';
import { bakeClip } from '../export/clipBuilder';
import { createMapping, guessMapping } from '../retargeting/boneMap';
import { builtinCharacter, proceduralCharacter } from './builtin';
import { characterSource, characterSources, defaultCharacterId } from './registry';
import { glbCharacterSource } from './glbSource';
import { rebindToCanonical } from './rebind';
import { applyCharacterPose } from './pose';
import type { CharacterBuild } from './types';

const rig = canonicalSkeleton;
const studioClip = generateClip(rig, bicepCurl);

/** The curl, resolved through the whole pipeline exactly as the studio does. */
function curlPose(time: number) {
  const evaluation = new PoseEvaluation(rig);
  const anchors = lockAnchors(evaluation, sampleClip(studioClip, 0).pose, studioClip.locks);
  const frame = resolveFrame(rig, evaluation, studioClip, time, { anchors });
  return { frame, evaluation };
}

/** Where a bone's head ends up once a character has been posed. */
const boneHead = (character: CharacterBuild, name: string): Vector3 =>
  new Vector3().setFromMatrixPosition(character.boneByName.get(name as never)!.matrixWorld);

describe('the character registry', () => {
  it('offers the built-in character by default, with the mannequin as a debug model', () => {
    const ids = characterSources().map((source) => source.id);
    expect(ids).toContain('builtin');
    expect(ids).toContain('procedural');
    expect(defaultCharacterId()).toBe('builtin');
    expect(characterSource('builtin')).toBe(builtinCharacter);
    // An unknown id renders the default rather than nothing at all.
    expect(characterSource('no-such-character')).toBe(builtinCharacter);
    expect(proceduralCharacter.diagnostic).toBe(true);
  });

  it('declares what each character can do rather than assuming it', () => {
    expect(builtinCharacter.capabilities.anatomy).toBe(true);
    // The procedural mannequin has no écorché mapping, and says so.
    expect(proceduralCharacter.capabilities.anatomy).toBe(false);
    expect(glbCharacterSource({ id: 'x', label: 'x', data: new ArrayBuffer(0) }).capabilities).toEqual({
      anatomy: false,
      textured: true,
    });
  });
});

describe('the built-in character', () => {
  // Building the built-in surface runs every repair pass over 14k vertices,
  // which is seconds rather than milliseconds on a cold machine.
  it('still builds, binds to the canonical rig and animates', { timeout: 30_000 }, async () => {
    const character = await builtinCharacter.build(rig);

    expect(character.bones).toHaveLength(rig.bones.length);
    for (const bone of rig.bones) {
      const built = character.boneByName.get(bone.name);
      expect(built, bone.name).toBeDefined();
      expect(built!.parent?.name ?? null, bone.name).toBe(bone.parent ?? 'HGPT_Mannequin');
    }
    expect(character.meshes[0].geometry.getAttribute('skinWeight')).toBeDefined();

    const bottom = curlPose(0);
    applyCharacterPose(character, rig, bottom.frame.pose, bottom.evaluation);
    const low = boneHead(character, 'hand_r').clone();

    const top = curlPose(studioClip.duration * 0.4545);
    applyCharacterPose(character, rig, top.frame.pose, top.evaluation);
    const high = boneHead(character, 'hand_r').clone();

    // The curl lifts the hand by most of a forearm.
    expect(high.y - low.y).toBeGreaterThan(0.25);
    character.dispose();
  });

  it('keeps its mesh-specific correctives, and hands them to the exporter', { timeout: 30_000 }, async () => {
    const character = await builtinCharacter.build(rig);
    expect(character.deformation).not.toBeNull();

    const sampler = character.deformation!.sampler!();
    expect(sampler, 'the built-in shoulder correctives must bake into the clip').not.toBeNull();

    const baked = bakeClip(studioClip, rig, { fps: 12, deformation: sampler });
    const morphs = baked.clip.tracks.filter((track) => track.name.includes('morphTargetInfluences'));
    expect(morphs.length).toBeGreaterThan(0);
    expect(morphs.every((track) => track.name.startsWith('HGPT_Mannequin.'))).toBe(true);
    character.dispose();
  });

  it('does not lend those correctives to another character', async () => {
    const mannequin = await proceduralCharacter.build(rig);
    expect(mannequin.deformation).toBeNull();
    mannequin.dispose();
  });
});

describe('rebinding a surface by bone name', () => {
  /**
   * A one-triangle skinned mesh on a foreign rig: Mixamo names, a different
   * bone order, and a bone the canonical rig does not carry.
   */
  function foreignCharacter() {
    const hips = new Bone();
    hips.name = 'mixamorigHips';
    hips.position.set(0, 1.0, 0);
    const spine = new Bone();
    spine.name = 'mixamorigSpine';
    spine.position.set(0, 0.1, 0);
    const twist = new Bone();
    // Not in the canonical rig: its weight must fall back to an ancestor.
    twist.name = 'mixamorigSpine_twist';
    twist.position.set(0, 0.05, 0);
    hips.add(spine);
    spine.add(twist);
    hips.updateMatrixWorld(true);

    const bones = [spine, twist, hips]; // deliberately not the canonical order
    const geometry = new BufferGeometry();
    geometry.setAttribute(
      'position',
      new BufferAttribute(new Float32Array([0, 1.1, 0, 0.1, 1.1, 0, 0, 1.15, 0]), 3),
    );
    geometry.setAttribute('uv', new BufferAttribute(new Float32Array([0, 0, 1, 0, 0, 1]), 2));
    geometry.setAttribute(
      'skinIndex',
      new BufferAttribute(new Uint16Array([0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]), 4),
    );
    geometry.setAttribute(
      'skinWeight',
      new BufferAttribute(new Float32Array([1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]), 4),
    );

    const mesh = new SkinnedMesh(geometry, new MeshStandardMaterial());
    mesh.add(hips);
    mesh.updateMatrixWorld(true);
    mesh.bind(new ThreeSkeleton(bones));
    return mesh;
  }

  it('remaps foreign bone indices onto the canonical rig', () => {
    const mesh = foreignCharacter();
    const mapping = createMapping('foreign', 'test');
    mapping.bones = guessMapping(['mixamorigHips', 'mixamorigSpine', 'mixamorigSpine_twist']);
    mapping.characterHeight = 1.75;

    const report = rebindToCanonical(mesh, mapping, rig);

    expect(report.vertices).toBe(3);
    expect(report.mappedBones).toContain('mixamorigSpine');
    // The twist bone is unknown to our rig, so its vertex rides the spine.
    expect(report.reassigned).toBe(1);
    expect(report.orphaned).toBe(0);

    const skinIndex = mesh.geometry.getAttribute('skinIndex');
    const names = rig.bones.map((bone) => bone.name);
    for (let vertex = 0; vertex < skinIndex.count; vertex += 1) {
      expect(names[skinIndex.getX(vertex)]).toMatch(/^(pelvis|spine_01)$/);
    }
    // UVs survive, so a textured character keeps its maps.
    expect(mesh.geometry.getAttribute('uv')).toBeDefined();
  });

  it('places the surface in the canonical rest pose', () => {
    const mesh = foreignCharacter();
    const mapping = createMapping('foreign', 'test');
    mapping.bones = guessMapping(['mixamorigHips', 'mixamorigSpine', 'mixamorigSpine_twist']);
    mapping.characterHeight = 1.75;
    rebindToCanonical(mesh, mapping, rig);

    // The first vertex sat 100 mm above the source spine's head; it must now sit
    // 100 mm above ours, wherever that is.
    const spine = rig.bone('spine_01');
    const position = mesh.geometry.getAttribute('position');
    const moved = new Vector3(position.getX(0), position.getY(0), position.getZ(0));
    expect(moved.distanceTo(spine.restHead)).toBeCloseTo(0.0, 2);
  });

  it('reads a Rigify deform rig by name', () => {
    // Rigify numbers its spine rather than naming it, and prefixes every deform
    // bone. Blender's exporter strips the dots on the way out, which the
    // normaliser already handles.
    const bones = guessMapping([
      'DEF-spine', 'DEF-spine001', 'DEF-spine002', 'DEF-spine003', 'DEF-spine004',
      'DEF-spine006', 'DEF-shoulderR', 'DEF-upper_armR', 'DEF-forearmR', 'DEF-handR',
      'DEF-thighR', 'DEF-shinR', 'DEF-footR', 'DEF-toeR', 'neutral_bone',
    ]);
    expect(bones.pelvis).toBe('DEF-spine');
    expect(bones.spine_03).toBe('DEF-spine003');
    expect(bones.neck).toBe('DEF-spine004');
    expect(bones.head).toBe('DEF-spine006');
    expect(bones.clavicle_r).toBe('DEF-shoulderR');
    expect(bones.upperarm_r).toBe('DEF-upper_armR');
    expect(bones.forearm_r).toBe('DEF-forearmR');
    expect(bones.hand_r).toBe('DEF-handR');
    expect(bones.foot_r).toBe('DEF-footR');
    // The exporter's placeholder for unweighted vertices is not a body part.
    expect(Object.values(bones)).not.toContain('neutral_bone');
  });

  it('binds an unweighted vertex to the bone nearest it, and says so', () => {
    const mesh = foreignCharacter();
    // A third bone carrying no canonical meaning at all — the shape Blender's
    // exporter leaves behind when a vertex belongs to no vertex group.
    const skinIndex = mesh.geometry.getAttribute('skinIndex');
    skinIndex.setXYZW(2, 1, 0, 0, 0);
    const mapping = createMapping('foreign', 'test');
    mapping.bones = { pelvis: 'mixamorigHips' };
    mapping.characterHeight = 1.75;

    const report = rebindToCanonical(mesh, mapping, rig);

    // The spine and twist bones are both unmapped now, so every vertex falls
    // back — and lands on the pelvis because that is the only bone there is.
    expect(report.orphaned).toBe(0);
    expect(report.reassigned).toBe(3);

    // With nothing mapped at all the surface still has to survive.
    const bare = foreignCharacter();
    const empty = createMapping('bare', 'test');
    empty.bones = {};
    empty.characterHeight = 1.75;
    const bareReport = rebindToCanonical(bare, empty, rig);
    expect(bareReport.orphaned).toBe(3);
    const bareIndex = bare.geometry.getAttribute('skinIndex');
    for (let vertex = 0; vertex < bareIndex.count; vertex += 1) {
      expect(Number.isInteger(bareIndex.getX(vertex))).toBe(true);
    }
  });
});

describe('a GLB character through the source architecture', () => {
  /** The studio's own export, read back in as a foreign file. */
  async function exportedCharacter(): Promise<ArrayBuffer> {
    const blob = await exportGlb(studioClip, bicepCurl, { fps: 12, includeEquipment: false });
    return blob.arrayBuffer();
  }

  it('loads, rebinds and is driven by the canonical curl', async () => {
    const data = await exportedCharacter();
    const source = glbCharacterSource({ id: 'test-glb', label: 'Test GLB', data });
    const character = await source.build(rig);

    expect(character.source).toBe('test-glb');
    expect(character.meshes.length).toBeGreaterThan(0);
    expect(character.bones).toHaveLength(rig.bones.length);
    // Its surface is bound to our bones now, not to the file's.
    const report = source.lastReport!.rebind[0];
    expect(report.vertices).toBeGreaterThan(0);
    expect(report.orphaned).toBe(0);

    const bottom = curlPose(0);
    applyCharacterPose(character, rig, bottom.frame.pose, bottom.evaluation);
    const low = boneHead(character, 'hand_r').clone();
    const lowSurface = wristSurface(character);

    const top = curlPose(studioClip.duration * 0.4545);
    applyCharacterPose(character, rig, top.frame.pose, top.evaluation);
    const high = boneHead(character, 'hand_r').clone();
    const highSurface = wristSurface(character);

    expect(high.y - low.y).toBeGreaterThan(0.25);
    // And the skin follows the bone: this is the whole point of the rebind.
    expect(highSurface - lowSurface).toBeGreaterThan(0.2);

    character.dispose();
  });

  it('exports with the equipment still in its hands', async () => {
    const data = await exportedCharacter();
    const source = glbCharacterSource({ id: 'test-glb-2', label: 'Test GLB', data });
    const blob = await exportGlb(studioClip, bicepCurl, { fps: 12, character: source });
    const buffer = await blob.arrayBuffer();
    const view = new DataView(buffer);
    const jsonLength = view.getUint32(12, true);
    const json = JSON.parse(
      new TextDecoder().decode(new Uint8Array(buffer, 20, jsonLength)),
    ) as { nodes: { name?: string; children?: number[] }[]; animations: unknown[] };

    const hand = json.nodes.findIndex((node) => node.name === 'hand_r');
    expect(hand).toBeGreaterThanOrEqual(0);
    const held = (json.nodes[hand].children ?? []).map((child) => json.nodes[child].name ?? '');
    expect(held.some((name) => /dumbbell/i.test(name))).toBe(true);
    expect(json.animations).toHaveLength(1);
  });

  it('carries no built-in correctives it was not authored for', async () => {
    const data = await exportedCharacter();
    const source = glbCharacterSource({ id: 'test-glb-3', label: 'Test GLB', data });
    const character = await source.build(rig);
    expect(character.deformation).toBeNull();
    character.dispose();
  });
});

describe('the viewport and the exported file', () => {
  it('pose the same character the same way', { timeout: 30_000 }, async () => {
    const character = await builtinCharacter.build(rig);
    const baked = bakeClip(studioClip, rig, { fps: 20 });

    for (const fraction of [0, 0.2327, 0.4545, 0.8]) {
      const time = studioClip.duration * fraction;
      const { frame, evaluation } = curlPose(time);
      applyCharacterPose(character, rig, frame.pose, evaluation);

      for (const name of ['upperarm_r', 'forearm_r', 'hand_r'] as const) {
        const track = baked.clip.tracks.find((entry) => entry.name === `${name}.quaternion`);
        if (!track) continue;
        const sampled = sampleQuaternion(track.times as unknown as number[], track.values as unknown as number[], time);
        const posed = new Quaternion().setFromRotationMatrix(
          new Matrix4().extractRotation(character.boneByName.get(name)!.matrix),
        );
        // Same rotation, allowing for the baked clip's own sampling interval.
        expect(Math.abs(sampled.dot(posed)), `${name} at ${fraction}`).toBeGreaterThan(0.999);
      }
    }
    character.dispose();
  });
});

/** Highest vertex weighted to the right hand, as a coarse "did the skin follow" probe. */
function wristSurface(character: CharacterBuild): number {
  const mesh = character.meshes[0];
  const position = mesh.geometry.getAttribute('position');
  const skinIndex = mesh.geometry.getAttribute('skinIndex');
  const skinWeight = mesh.geometry.getAttribute('skinWeight');
  const hand = rig.bones.findIndex((bone) => bone.name === 'hand_r');

  const skinned = new Vector3();
  const source = new Vector3();
  const matrix = new Matrix4();
  let highest = -Infinity;

  for (let vertex = 0; vertex < position.count; vertex += 1) {
    if (skinIndex.getX(vertex) !== hand || skinWeight.getX(vertex) < 0.99) continue;
    source.set(position.getX(vertex), position.getY(vertex), position.getZ(vertex));
    matrix
      .copy(mesh.skeleton.bones[hand].matrixWorld)
      .multiply(mesh.skeleton.boneInverses[hand]);
    highest = Math.max(highest, skinned.copy(source).applyMatrix4(matrix).y);
  }
  return highest;
}

/** Nearest-sample read of a baked quaternion track. */
function sampleQuaternion(times: number[], values: number[], time: number): Quaternion {
  let best = 0;
  for (let index = 1; index < times.length; index += 1) {
    if (Math.abs(times[index] - time) < Math.abs(times[best] - time)) best = index;
  }
  return new Quaternion(
    values[best * 4],
    values[best * 4 + 1],
    values[best * 4 + 2],
    values[best * 4 + 3],
  );
}
