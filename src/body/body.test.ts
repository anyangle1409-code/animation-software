import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { canonicalSkeleton } from '../rig/skeleton';
import { RIG_HEIGHT } from '../rig/humanoid';
import type { BoneName } from '../rig/boneNames';
import { Color } from 'three';
import { buildBodyGeometry } from './mesh';
import { BODY_BLOBS, BODY_CHAINS, BODY_COLOURS } from './profiles';
import { MUSCLE_GROUP_IDS } from '../muscles/groups';

const rig = canonicalSkeleton;
const { geometry, vertices, triangles } = buildBodyGeometry(rig);
const position = geometry.getAttribute('position');
const skinIndex = geometry.getAttribute('skinIndex');
const skinWeight = geometry.getAttribute('skinWeight');

/** The bone that holds most of a vertex. */
const ownerOf = (index: number): BoneName => {
  const weights = [skinWeight.getX(index), skinWeight.getY(index), skinWeight.getZ(index), skinWeight.getW(index)];
  const slots = [skinIndex.getX(index), skinIndex.getY(index), skinIndex.getZ(index), skinIndex.getW(index)];
  let strongest = 0;
  for (let slot = 1; slot < 4; slot += 1) if (weights[slot] > weights[strongest]) strongest = slot;
  return rig.bones[slots[strongest]].name;
};

interface Extent {
  halfWidth: number;
  low: number;
  high: number;
}

/** Uint8 vertex colours approximate the linear-space palette. */
const matches = (
  colour: { getX(i: number): number; getY(i: number): number; getZ(i: number): number },
  index: number,
  target: Color,
): boolean =>
  Math.abs(colour.getX(index) - target.r) < 0.005 &&
  Math.abs(colour.getY(index) - target.g) < 0.005 &&
  Math.abs(colour.getZ(index) - target.b) < 0.005;

const extentOf = (bones: BoneName[]): Extent => {
  const wanted = new Set(bones);
  const extent: Extent = { halfWidth: 0, low: Infinity, high: -Infinity };
  for (let index = 0; index < position.count; index += 1) {
    if (!wanted.has(ownerOf(index))) continue;
    extent.halfWidth = Math.max(extent.halfWidth, Math.abs(position.getX(index)));
    extent.low = Math.min(extent.low, position.getY(index));
    extent.high = Math.max(extent.high, position.getY(index));
  }
  return extent;
};

describe('body mesh', () => {
  it('stands the right height on the floor', () => {
    let lowest = Infinity;
    let highest = -Infinity;
    for (let index = 0; index < position.count; index += 1) {
      lowest = Math.min(lowest, position.getY(index));
      highest = Math.max(highest, position.getY(index));
    }
    // The crown is the rig's own stated height, and the soles are on the floor
    // rather than hovering over it or sunk into it.
    expect(highest).toBeCloseTo(RIG_HEIGHT, 1);
    expect(lowest).toBeGreaterThan(-0.005);
    expect(lowest).toBeLessThan(0.01);
  });

  it('has the proportions of an adult, not a mannequin of tubes', () => {
    const head = extentOf(['head']);
    const chest = extentOf(['spine_03']);
    const waist = extentOf(['spine_01']);
    const hips = extentOf(['pelvis']);

    // Anthropometry for a 1.75 m adult, in metres across.
    expect(head.halfWidth * 2).toBeGreaterThan(0.14);
    expect(head.halfWidth * 2).toBeLessThan(0.29);
    expect(chest.halfWidth * 2).toBeGreaterThan(0.33);
    expect(hips.halfWidth * 2).toBeGreaterThan(0.3);
    // A waist narrower than both the ribcage and the hips is what gives the
    // figure a human silhouette rather than a barrel.
    expect(waist.halfWidth).toBeLessThan(chest.halfWidth);
    expect(waist.halfWidth).toBeLessThan(hips.halfWidth);
    // The crotch sits at roughly half standing height.
    expect(hips.low).toBeGreaterThan(0.78);
    expect(hips.low).toBeLessThan(0.88);
  });

  it('keeps the shoulder cap on the shoulder', () => {
    const shoulderJoint = rig.bone('upperarm_l').restHead.y;
    const deltoid = extentOf(['upperarm_l', 'upperarm_r', 'clavicle_l', 'clavicle_r']);
    // A deltoid that rises far above the joint reads as a shoulder pad, and the
    // arm then looks bolted on rather than attached.
    expect(deltoid.high - shoulderJoint).toBeLessThan(0.05);
    expect(deltoid.high).toBeGreaterThan(shoulderJoint - 0.01);
    // Shoulder width, deltoid to deltoid.
    expect(deltoid.halfWidth * 2).toBeGreaterThan(0.4);
    expect(deltoid.halfWidth * 2).toBeLessThan(0.48);
  });

  it('encloses a body-sized volume, wound outwards', () => {
    // The divergence theorem over the triangles: a mesh wound inside-out gives a
    // negative volume, and one whose parts have collapsed gives far too little.
    const index = geometry.getIndex()!;
    const a = new Vector3();
    const b = new Vector3();
    const c = new Vector3();
    let volume = 0;
    for (let i = 0; i < index.count; i += 3) {
      a.fromBufferAttribute(position, index.getX(i));
      b.fromBufferAttribute(position, index.getX(i + 1));
      c.fromBufferAttribute(position, index.getX(i + 2));
      volume += a.dot(b.clone().cross(c)) / 6;
    }
    // Overlapping parts are counted twice where they intersect, so this runs a
    // little over a real 70 kg body's 0.07 m³ — but it is the right order, and
    // positive.
    expect(volume).toBeGreaterThan(0.05);
    expect(volume).toBeLessThan(0.13);
  });

  it('weights every vertex to four bones at most, summing to one', () => {
    for (let index = 0; index < position.count; index += 1) {
      const sum = skinWeight.getX(index) + skinWeight.getY(index) + skinWeight.getZ(index) + skinWeight.getW(index);
      expect(sum, `vertex ${index}`).toBeCloseTo(1, 5);
      expect(skinWeight.getX(index)).toBeGreaterThanOrEqual(0);
      expect(skinWeight.getW(index)).toBeGreaterThanOrEqual(0);
    }
  });

  it('keeps every vertex within reach of the bone that carries it', () => {
    const head = new Vector3();
    const tail = new Vector3();
    const point = new Vector3();
    for (let index = 0; index < position.count; index += 1) {
      const bone = rig.bone(ownerOf(index));
      head.copy(bone.restHead);
      tail.copy(bone.restTail);
      point.fromBufferAttribute(position, index);
      // Distance to the bone's own segment: a vertex much further away than the
      // body is thick means a profile has been authored onto the wrong bone.
      const along = tail.clone().sub(head);
      const t = Math.max(0, Math.min(1, point.clone().sub(head).dot(along) / along.lengthSq()));
      const nearest = head.clone().addScaledVector(along, t);
      expect(point.distanceTo(nearest), `${bone.name} vertex ${index}`).toBeLessThan(0.5);
    }
  });

  it('has an athletic male silhouette, not a barrel or an hourglass', () => {
    const chest = extentOf(['spine_03']);
    const waist = extentOf(['spine_01']);
    const hips = extentOf(['pelvis']);
    // Shoulders wider than hips, waist narrower than both: the V a trained man
    // has and a mannequin does not.
    expect(chest.halfWidth).toBeGreaterThan(hips.halfWidth);
    expect(chest.halfWidth / waist.halfWidth).toBeGreaterThan(1.3);
    expect(chest.halfWidth / waist.halfWidth).toBeLessThan(1.65);

    // Limb girths, as diameters at the belly of each muscle.
    const upperArm = extentOf(['upperarm_l']);
    const forearm = extentOf(['forearm_l']);
    const thigh = extentOf(['thigh_l']);
    const shoulder = rig.bone('upperarm_l').restHead;
    expect((upperArm.halfWidth - Math.abs(shoulder.x)) * 2).toBeGreaterThan(0.09);
    expect((upperArm.halfWidth - Math.abs(shoulder.x)) * 2).toBeLessThan(0.13);
    expect(forearm.halfWidth).toBeLessThan(upperArm.halfWidth);
    expect(thigh.low).toBeLessThan(0.6);
  });

  it('wears shorts that leave every working joint visible', () => {
    const shorts = new Color(BODY_COLOURS.shorts);
    let lowest = Infinity;
    let highest = -Infinity;
    let clothed = 0;
    const colour = geometry.getAttribute('color');
    for (let index = 0; index < colour.count; index += 1) {
      const near = matches(colour, index, shorts);
      if (!near) continue;
      clothed += 1;
      lowest = Math.min(lowest, position.getY(index));
      highest = Math.max(highest, position.getY(index));
    }

    expect(clothed).toBeGreaterThan(60);
    // Waistband on the hip, hem at mid-thigh: elbows, knees, shoulders and the
    // whole torso stay bare, which is where the muscle highlighting lands.
    expect(highest).toBeLessThan(1.05);
    expect(lowest).toBeGreaterThan(0.68);
  });

  it('has eyes in its head', () => {
    const sclera = new Color(BODY_COLOURS.sclera);
    const iris = new Color(BODY_COLOURS.iris);
    const colour = geometry.getAttribute('color');
    const seen = { sclera: 0, iris: 0 };
    for (let index = 0; index < colour.count; index += 1) {
      const isSclera = matches(colour, index, sclera);
      const isIris = matches(colour, index, iris);
      if (isSclera) seen.sclera += 1;
      if (isIris) seen.iris += 1;
      if (!isSclera && !isIris) continue;
      // Both sit in the head, above the shoulders and in front of the ears.
      expect(position.getY(index)).toBeGreaterThan(1.55);
      expect(position.getZ(index)).toBeGreaterThan(-0.01);
    }
    expect(seen.sclera).toBeGreaterThan(40);
    expect(seen.iris).toBeGreaterThan(40);
    expect(ownerOf(0)).toBeDefined();
  });

  it('maps exercise muscles onto the anatomical surface', () => {
    const groups = geometry.getAttribute('muscleGroup');
    const biceps = MUSCLE_GROUP_IDS.indexOf('biceps') + 1;
    const flexors = MUSCLE_GROUP_IDS.indexOf('forearm_flexors') + 1;
    let bicepsVertices = 0;
    let flexorVertices = 0;
    for (let index = 0; index < groups.count; index += 1) {
      expect(groups.getX(index)).toBeGreaterThanOrEqual(0);
      expect(groups.getX(index)).toBeLessThanOrEqual(MUSCLE_GROUP_IDS.length);
      if (groups.getX(index) === biceps) bicepsVertices += 1;
      if (groups.getX(index) === flexors) flexorVertices += 1;
    }
    expect(bicepsVertices).toBeGreaterThan(40);
    expect(flexorVertices).toBeGreaterThan(40);
  });

  it('stays small enough to export comfortably', () => {
    expect(vertices).toBeLessThan(16000);
    expect(triangles).toBeLessThan(30000);
  });

  it('names a bone that exists for every profile it defines', () => {
    for (const chain of BODY_CHAINS) {
      for (const part of chain.parts) expect(rig.has(part.bone), part.bone).toBe(true);
      // Rings have to advance along the chain, or the tube folds back on itself.
      const positions = chain.parts.flatMap((part) =>
        part.rings.map((entry) => ({ bone: part.bone, t: entry.t })),
      );
      for (const part of chain.parts) {
        const ts = part.rings.map((entry) => entry.t);
        expect([...ts].sort((x, y) => x - y), `${chain.id}/${part.bone}`).toEqual(ts);
      }
      expect(positions.length).toBeGreaterThan(1);
    }
    for (const blob of BODY_BLOBS) expect(rig.has(blob.bone), blob.bone).toBe(true);
  });
});
