import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { canonicalSkeleton } from '../rig/skeleton';
import { RIG_HEIGHT } from '../rig/humanoid';
import type { BoneName } from '../rig/boneNames';
import { buildBodyGeometry } from './mesh';
import { BODY_BLOBS, BODY_CHAINS } from './profiles';

const rig = canonicalSkeleton;
const { geometry, vertices, triangles } = buildBodyGeometry(rig);
const position = geometry.getAttribute('position');
const skinIndex = geometry.getAttribute('skinIndex');
const skinWeight = geometry.getAttribute('skinWeight');

/** The bone that holds most of a vertex. */
const ownerOf = (index: number): BoneName =>
  rig.bones[skinWeight.getX(index) >= 0.5 ? skinIndex.getX(index) : skinIndex.getY(index)].name;

interface Extent {
  halfWidth: number;
  low: number;
  high: number;
}

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
    expect(head.halfWidth * 2).toBeLessThan(0.19);
    expect(chest.halfWidth * 2).toBeGreaterThan(0.33);
    expect(hips.halfWidth * 2).toBeGreaterThan(0.32);
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
    expect(deltoid.high).toBeGreaterThan(shoulderJoint);
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

  it('weights every vertex to two bones at most, summing to one', () => {
    for (let index = 0; index < position.count; index += 1) {
      const sum = skinWeight.getX(index) + skinWeight.getY(index);
      expect(sum, `vertex ${index}`).toBeCloseTo(1, 5);
      expect(skinWeight.getZ(index)).toBe(0);
      expect(skinWeight.getW(index)).toBe(0);
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
      expect(point.distanceTo(nearest), `${bone.name} vertex ${index}`).toBeLessThan(0.24);
    }
  });

  it('stays small enough to export comfortably', () => {
    expect(vertices).toBeLessThan(12000);
    expect(triangles).toBeLessThan(20000);
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
