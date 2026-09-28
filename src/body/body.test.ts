import { describe, expect, it } from 'vitest';
import { canonicalSkeleton } from '../rig/skeleton';
import { buildBodyGeometry } from './mesh';
import { BODY_BLOBS, BODY_CHAINS } from './profiles';

const rig = canonicalSkeleton;
const { geometry, vertices, triangles } = buildBodyGeometry(rig);
const position = geometry.getAttribute('position');
const skinIndex = geometry.getAttribute('skinIndex');
const skinWeight = geometry.getAttribute('skinWeight');
const colour = geometry.getAttribute('color');

describe('clean profile body mesh', () => {
  it('builds a finite, non-trivial project-authored surface', () => {
    expect(vertices).toBeGreaterThan(1000);
    expect(vertices).toBeLessThan(10000);
    expect(triangles).toBeGreaterThan(1000);
    expect(triangles).toBeLessThan(20000);
    expect(position.count).toBe(vertices);
    expect(colour.count).toBe(vertices);

    for (let index = 0; index < position.count; index += 1) {
      expect(Number.isFinite(position.getX(index))).toBe(true);
      expect(Number.isFinite(position.getY(index))).toBe(true);
      expect(Number.isFinite(position.getZ(index))).toBe(true);
    }
  });

  it('keeps all skin rows normalized to at most two active influences', () => {
    for (let index = 0; index < skinWeight.count; index += 1) {
      const x = skinWeight.getX(index);
      const y = skinWeight.getY(index);
      expect(x + y).toBeCloseTo(1, 5);
      expect(skinWeight.getZ(index)).toBe(0);
      expect(skinWeight.getW(index)).toBe(0);
      expect(skinIndex.getX(index)).toBeGreaterThanOrEqual(0);
      expect(skinIndex.getX(index)).toBeLessThan(rig.bones.length);
      expect(skinIndex.getY(index)).toBeGreaterThanOrEqual(0);
      expect(skinIndex.getY(index)).toBeLessThan(rig.bones.length);
    }
  });

  it('uses only declared rig bones and monotonic authored rings', () => {
    for (const chain of BODY_CHAINS) {
      for (const part of chain.parts) {
        expect(rig.has(part.bone), part.bone).toBe(true);
        const ts = part.rings.map((entry) => entry.t);
        expect([...ts].sort((a, b) => a - b), `${chain.id}/${part.bone}`).toEqual(ts);
      }
    }
    for (const blob of BODY_BLOBS) expect(rig.has(blob.bone), blob.bone).toBe(true);
  });

  it('produces valid indexed triangles and bounded human-scale geometry', () => {
    const index = geometry.getIndex();
    expect(index).not.toBeNull();
    expect(index!.count % 3).toBe(0);
    for (let entry = 0; entry < index!.count; entry += 1) {
      const vertex = index!.getX(entry);
      expect(vertex).toBeGreaterThanOrEqual(0);
      expect(vertex).toBeLessThan(vertices);
    }

    geometry.computeBoundingBox();
    const box = geometry.boundingBox!;
    const height = box.max.y - box.min.y;
    expect(height).toBeGreaterThan(1.4);
    expect(height).toBeLessThan(2.0);
    expect(box.max.x - box.min.x).toBeGreaterThan(0.25);
    expect(box.max.x - box.min.x).toBeLessThan(0.8);
  });
});
