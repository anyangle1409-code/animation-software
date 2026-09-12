import { describe, expect, it } from 'vitest';
import {
  AnimationMixer,
  Bone,
  BufferAttribute,
  BufferGeometry,
  Group,
  Matrix4,
  MeshStandardMaterial,
  Object3D,

  Skeleton as ThreeSkeleton,
  SkinnedMesh,
  Vector3,
} from 'three';
import { GLTFExporter } from 'three/examples/jsm/exporters/GLTFExporter.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { generateClip } from '../animation/generate';
import { resolveFrame } from '../animation/pipeline';
import { lockAnchors } from '../constraints/locks';
import { sampleClip } from '../animation/clip';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { exportGlb } from '../export/glb';
import { retargetedCharacterSource } from './retargetSource';
import { applyCharacterPose } from './pose';
import type { CharacterBuild } from './types';

/**
 * An imported character is *preserved*: the studio drives its skeleton and
 * changes nothing else about it.
 *
 * The fixture is a Rigify-shaped character built here and round-tripped
 * through a real GLB — deform-bone names, numbered spine, twist bones, and a
 * helper bone parented to the armature rather than to the head, which is the
 * arrangement that used to be read as "unweighted" surface.
 */

const rig = canonicalSkeleton;
const studioClip = generateClip(rig, bicepCurl);
/** Bottom of the rep, and the top, as clip fractions. */
const TOP = 0.4545;

function curlPose(time: number) {
  const evaluation = new PoseEvaluation(rig);
  const anchors = lockAnchors(evaluation, sampleClip(studioClip, 0).pose, studioClip.locks);
  return { frame: resolveFrame(rig, evaluation, studioClip, time, { anchors }), evaluation };
}

interface Fixture {
  data: ArrayBuffer;
  /** The positions as authored, to compare an import against. */
  positions: Float32Array;
  boneNames: string[];
}

/** A small skinned humanoid on Rigify deform names, exported as a GLB. */
async function rigifyFixture(): Promise<Fixture> {
  const made = new Map<string, Bone>();
  const bone = (name: string, parent: string | null, offset: [number, number, number]) => {
    const made1 = new Bone();
    made1.name = name;
    made1.position.set(...offset);
    if (parent) made.get(parent)!.add(made1);
    made.set(name, made1);
    return made1;
  };

  const root = bone('DEF-spine', null, [0, 0.95, 0]);
  bone('DEF-spine.001', 'DEF-spine', [0, 0.14, 0]);
  bone('DEF-spine.002', 'DEF-spine.001', [0, 0.14, 0]);
  bone('DEF-spine.003', 'DEF-spine.002', [0, 0.14, 0]);
  bone('DEF-spine.004', 'DEF-spine.003', [0, 0.15, 0]);
  bone('DEF-spine.005', 'DEF-spine.004', [0, 0.05, 0]);
  bone('DEF-spine.006', 'DEF-spine.005', [0, 0.05, 0]);
  // A helper hung off the armature root rather than off the head — the shape
  // a Rigify face rig arrives in.
  bone('DEF-jaw.helper', 'DEF-spine', [0.02, 0.62, 0.06]);

  for (const [side, sign] of [['L', 1], ['R', -1]] as [string, number][]) {
    bone(`DEF-shoulder.${side}`, 'DEF-spine.003', [sign * 0.04, 0.12, 0]);
    bone(`DEF-upper_arm.${side}`, `DEF-shoulder.${side}`, [sign * 0.12, 0, 0]);
    bone(`DEF-upper_arm.${side}.001`, `DEF-upper_arm.${side}`, [sign * 0.14, 0, 0]);
    bone(`DEF-forearm.${side}`, `DEF-upper_arm.${side}.001`, [sign * 0.14, 0, 0]);
    bone(`DEF-forearm.${side}.001`, `DEF-forearm.${side}`, [sign * 0.12, 0, 0]);
    bone(`DEF-hand.${side}`, `DEF-forearm.${side}.001`, [sign * 0.12, 0, 0]);
    bone(`DEF-thigh.${side}`, 'DEF-spine', [sign * 0.09, -0.04, 0]);
    bone(`DEF-shin.${side}`, `DEF-thigh.${side}`, [0, -0.42, 0]);
    bone(`DEF-foot.${side}`, `DEF-shin.${side}`, [0, -0.42, 0]);
    bone(`DEF-toe.${side}`, `DEF-foot.${side}`, [0, -0.04, 0.12]);
  }

  root.updateMatrixWorld(true);
  const bones = [...made.values()];

  // Six vertices around each bone's head, weighted to that bone, and a couple
  // shared with its parent so joints have something that must not tear.
  const positions: number[] = [];
  const skinIndices: number[] = [];
  const skinWeights: number[] = [];
  const indices: number[] = [];
  const head = new Vector3();

  bones.forEach((each, boneIndex) => {
    const parentIndex = bones.indexOf(each.parent as Bone);
    head.setFromMatrixPosition(each.matrixWorld);
    const start = positions.length / 3;
    for (let step = 0; step < 6; step += 1) {
      const angle = (step / 6) * Math.PI * 2;
      positions.push(
        head.x + 0.04 * Math.cos(angle),
        head.y + 0.02 * (step % 2 === 0 ? 1 : -1),
        head.z + 0.04 * Math.sin(angle),
      );
      // Two of the six share with the parent, so every joint carries a blend.
      const shared = step < 2 && parentIndex >= 0;
      skinIndices.push(boneIndex, shared ? parentIndex : 0, 0, 0);
      skinWeights.push(shared ? 0.6 : 1, shared ? 0.4 : 0, 0, 0);
    }
    for (let step = 0; step < 4; step += 1) {
      indices.push(start, start + step + 1, start + step + 2 > start + 5 ? start + 1 : start + step + 2);
    }
  });

  const geometry = new BufferGeometry();
  const authored = new Float32Array(positions);
  geometry.setAttribute('position', new BufferAttribute(authored.slice(), 3));
  geometry.setAttribute(
    'uv',
    new BufferAttribute(new Float32Array((positions.length / 3) * 2).fill(0.5), 2),
  );
  geometry.setAttribute('skinIndex', new BufferAttribute(new Uint16Array(skinIndices), 4));
  geometry.setAttribute('skinWeight', new BufferAttribute(new Float32Array(skinWeights), 4));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();

  const mesh = new SkinnedMesh(geometry, new MeshStandardMaterial({ color: '#cccccc' }));
  mesh.name = 'FixtureBody';
  const scene = new Group();
  scene.name = 'FixtureCharacter';
  scene.add(mesh);
  scene.add(root);
  scene.updateMatrixWorld(true);
  mesh.bind(new ThreeSkeleton(bones));

  const exported = await new GLTFExporter().parseAsync(scene as Object3D, {
    binary: true,
    onlyVisible: false,
  });

  return {
    data: exported as ArrayBuffer,
    positions: authored,
    boneNames: bones.map((each) => each.name),
  };
}

const fixture = await rigifyFixture();
const importedSource = () =>
  retargetedCharacterSource({ id: 'fixture', label: 'Fixture', data: fixture.data });

/** Where a bone of the character's own skeleton has ended up. */
const boneAt = (character: CharacterBuild, name: string): Vector3 => {
  const bone = character.bones.find((each) => each.name.replace(/[.]/g, '') === name.replace(/[.]/g, ''));
  if (!bone) throw new Error(`no bone ${name}`);
  bone.updateWorldMatrix(true, false);
  return new Vector3().setFromMatrixPosition(bone.matrixWorld);
};

describe('an imported character', () => {
  it('keeps its rest geometry, changing only where it stands and how big it is', async () => {
    const source = importedSource();
    const character = await source.build(rig);

    const position = character.meshes[0].geometry.getAttribute('position');
    expect(position.count).toBe(fixture.positions.length / 3);
    // Vertex for vertex, exactly as authored. Nothing is re-placed, blended or
    // rebound: the only change is the uniform scale on the root, and that is a
    // transform, not a rewrite.
    for (let vertex = 0; vertex < position.count; vertex += 1) {
      expect(position.getX(vertex), `x${vertex}`).toBeCloseTo(fixture.positions[vertex * 3], 6);
      expect(position.getY(vertex), `y${vertex}`).toBeCloseTo(fixture.positions[vertex * 3 + 1], 6);
      expect(position.getZ(vertex), `z${vertex}`).toBeCloseTo(fixture.positions[vertex * 3 + 2], 6);
    }

    const scale = new Vector3().setFromMatrixScale(character.object.matrixWorld);
    expect(scale.x).toBeCloseTo(scale.y, 6);
    expect(scale.y).toBeCloseTo(scale.z, 6);
    expect(scale.x).toBeGreaterThan(0);
    character.dispose();
  });

  it('drives the mapped source bones with the canonical curl', async () => {
    const character = await importedSource().build(rig);

    /** The angle at the character's own elbow, from its own bones. */
    const elbowAngle = () => {
      const shoulder = boneAt(character, 'DEF-upper_arm.R');
      const elbow = boneAt(character, 'DEF-forearm.R');
      const wrist = boneAt(character, 'DEF-hand.R');
      return elbow.clone().sub(shoulder).angleTo(wrist.clone().sub(elbow));
    };
    /** The same angle on the rig that is driving it. */
    const canonicalAngle = (evaluation: PoseEvaluation) =>
      new Vector3(0, 1, 0)
        .applyQuaternion(evaluation.quaternion('upperarm_r'))
        .angleTo(new Vector3(0, 1, 0).applyQuaternion(evaluation.quaternion('forearm_r')));

    const bottom = curlPose(0);
    applyCharacterPose(character, rig, bottom.frame.pose, bottom.evaluation);
    const low = boneAt(character, 'DEF-hand.R');
    const elbowLow = boneAt(character, 'DEF-forearm.R');
    const straight = elbowAngle();

    const top = curlPose(studioClip.duration * TOP);
    applyCharacterPose(character, rig, top.frame.pose, top.evaluation);
    const high = boneAt(character, 'DEF-hand.R');
    const elbowHigh = boneAt(character, 'DEF-forearm.R');
    const flexed = elbowAngle();

    // The hand travels the better part of a forearm, and the elbow stays where
    // it is — which is what makes it a curl rather than a row.
    expect(high.distanceTo(low)).toBeGreaterThan(0.15);
    expect(elbowHigh.distanceTo(elbowLow)).toBeLessThan(0.1);

    // And the angle that arrived at the character's elbow is the angle the rig
    // is holding, not merely some movement: this is the transfer working.
    expect(straight).toBeCloseTo(canonicalAngle(bottom.evaluation), 1);
    expect(flexed).toBeCloseTo(canonicalAngle(top.evaluation), 1);
    expect(flexed - straight).toBeGreaterThan(1.5);
    character.dispose();
  });

  it('leaves twist bones rigid with the limb that carries them', async () => {
    const character = await importedSource().build(rig);
    const twist = character.bones.find((each) => /upper_armR001|upper_arm\.R\.001/.test(each.name))!;
    const parent = twist.parent as Bone;
    const restLocal = twist.quaternion.clone();
    const restOffset = twist.position.clone();

    for (const fraction of [0, 0.2327, TOP, 0.8]) {
      const { frame, evaluation } = curlPose(studioClip.duration * fraction);
      applyCharacterPose(character, rig, frame.pose, evaluation);

      // Never driven, so it keeps the local transform the file gave it …
      expect(twist.quaternion.angleTo(restLocal), `rotation at ${fraction}`).toBeLessThan(1e-6);
      expect(twist.position.distanceTo(restOffset), `offset at ${fraction}`).toBeLessThan(1e-9);

      // … and therefore travels with the upper arm rather than staying behind.
      parent.updateWorldMatrix(true, false);
      twist.updateWorldMatrix(true, false);
      const gap = new Vector3()
        .setFromMatrixPosition(twist.matrixWorld)
        .distanceTo(new Vector3().setFromMatrixPosition(parent.matrixWorld));
      expect(gap, `distance from its parent at ${fraction}`).toBeGreaterThan(0.01);
    }
    character.dispose();
  });

  it('treats helper and face bones as undriven, not as unweighted surface', async () => {
    const source = importedSource();
    const character = await source.build(rig);
    const report = source.lastReport!;

    // Every canonical bone the rig needs found a home …
    expect(report.mapping.missingRequired).toEqual([]);
    // … and the bones it has no use for are simply not driven. They are not
    // errors, and nothing about the surface they carry is redistributed.
    expect(report.passive).toBeGreaterThan(0);
    expect(report.driven + report.passive).toBe(report.bones);

    const helper = character.bones.find((each) => /jaw/i.test(each.name))!;
    expect(helper, 'the helper bone survives the import').toBeDefined();
    const restWorld = new Vector3().setFromMatrixPosition(helper.matrixWorld);

    // It rides its parent: posing the character moves it, and it does not fly
    // off to the origin or stay pinned while the body moves.
    const { frame, evaluation } = curlPose(studioClip.duration * TOP);
    applyCharacterPose(character, rig, frame.pose, evaluation);
    helper.updateWorldMatrix(true, false);
    const posed = new Vector3().setFromMatrixPosition(helper.matrixWorld);
    expect(posed.length()).toBeGreaterThan(0.1);
    expect(posed.distanceTo(restWorld)).toBeLessThan(0.35);
    character.dispose();
  });

  it('keeps a hand-held item locked to the hand it is carried in', async () => {
    const character = await importedSource().build(rig);
    expect(character.handMatrix, 'a preserved import places its own hands').toBeDefined();

    const offsets: number[] = [];
    for (const fraction of [0, 0.2327, TOP, 0.8]) {
      const { frame, evaluation } = curlPose(studioClip.duration * fraction);
      applyCharacterPose(character, rig, frame.pose, evaluation);

      const held = character.handMatrix!('r', new Matrix4());
      expect(held, 'the right hand resolves').not.toBeNull();
      const grip = new Vector3().setFromMatrixPosition(held!);
      const hand = boneAt(character, 'DEF-hand.R');
      offsets.push(grip.distanceTo(hand));
    }

    // The grip frame is the hand's own, at every point in the rep — so whatever
    // is attached to it cannot drift out of the hand.
    for (const offset of offsets) expect(offset).toBeLessThan(1e-6);
    character.dispose();
  });

  it('exports its own mesh and skeleton, posed as the viewport poses it', async () => {
    const source = importedSource();
    const blob = await exportGlb(studioClip, bicepCurl, { fps: 20, character: source });
    const buffer = await blob.arrayBuffer();

    const view = new DataView(buffer);
    const jsonLength = view.getUint32(12, true);
    const json = JSON.parse(
      new TextDecoder().decode(new Uint8Array(buffer, 20, jsonLength)),
    ) as {
      meshes: { name?: string }[];
      skins: { joints: number[] }[];
      nodes: { name?: string; children?: number[] }[];
      animations: { channels: unknown[] }[];
    };

    // The file carries the imported character, not a rebuilt stand-in.
    expect(json.meshes.length).toBeGreaterThan(0);
    expect(json.skins).toHaveLength(1);
    const joints = json.skins[0].joints.map((node) => json.nodes[node].name ?? '');
    expect(joints).toContain('DEF-handR');
    expect(joints).toContain('DEF-upper_armR001');
    expect(json.animations).toHaveLength(1);

    // The dumbbell hangs off the character's own hand bone.
    const hand = json.nodes.findIndex((node) => node.name === 'DEF-handR');
    expect(hand).toBeGreaterThanOrEqual(0);
    const held = (json.nodes[hand].children ?? []).map((child) => json.nodes[child].name ?? '');
    expect(held.some((name) => /dumbbell/i.test(name))).toBe(true);

    // And playing it back reproduces the pose the viewport shows.
    const loaded = await new GLTFLoader().parseAsync(buffer, '');
    const mixer = new AnimationMixer(loaded.scene);
    const time = studioClip.duration * TOP;
    mixer.clipAction(loaded.animations[0]).play();
    mixer.setTime(time);
    loaded.scene.updateMatrixWorld(true);

    let playedHand: Object3D | null = null;
    loaded.scene.traverse((object) => {
      if (object.name === 'DEF-handR') playedHand = object;
    });
    expect(playedHand, 'the exported hand bone').not.toBeNull();

    const character = await importedSource().build(rig);
    const { frame, evaluation } = curlPose(time);
    applyCharacterPose(character, rig, frame.pose, evaluation);
    const shown = boneAt(character, 'DEF-hand.R');
    const written = new Vector3().setFromMatrixPosition((playedHand as unknown as Object3D).matrixWorld);

    // Within a millimetre: the difference is the baked clip's sampling
    // interval, not a different pose.
    expect(written.distanceTo(shown)).toBeLessThan(0.001);

    // Nothing about the surface changed on the way out either.
    let exportedVertices = 0;
    loaded.scene.traverse((object) => {
      const skinned = object as SkinnedMesh;
      if (skinned.isSkinnedMesh) exportedVertices = skinned.geometry.getAttribute('position').count;
    });
    expect(exportedVertices).toBe(fixture.positions.length / 3);
    character.dispose();
  }, 30_000);
});

