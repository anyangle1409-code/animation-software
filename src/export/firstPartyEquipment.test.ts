import { describe, expect, it } from 'vitest';
import type { Part } from '../equipment/geometry';
import { equipmentPrimitiveData } from './firstPartyEquipment';

const parts: Part[] = [
  { shape: 'box', size: [2, 4, 6], material: 'metal' },
  { shape: 'cylinder', radius: 1, radiusTop: 0.5, length: 2, segments: 8, material: 'metal' },
  { shape: 'sphere', radius: 2, material: 'metal' },
  { shape: 'torus', radius: 2, tube: 0.5, arc: Math.PI * 2, material: 'metal' },
];

describe('first-party equipment primitive geometry', () => {
  it.each(parts)('builds valid $shape mesh data without a renderer object', (part) => {
    const mesh = equipmentPrimitiveData(part);
    const vertexCount = mesh.positions.length / 3;

    expect(vertexCount).toBeGreaterThan(0);
    expect(mesh.normals).toHaveLength(mesh.positions.length);
    expect(mesh.uvs).toHaveLength(vertexCount * 2);
    expect(mesh.indices.length).toBeGreaterThan(0);
    expect(mesh.positions.every(Number.isFinite)).toBe(true);
    expect(mesh.normals.every(Number.isFinite)).toBe(true);
    expect(mesh.uvs.every(Number.isFinite)).toBe(true);
    expect(mesh.indices.every((index) => Number.isInteger(index) && index >= 0 && index < vertexCount)).toBe(true);
  });

  it('honours authored box dimensions exactly', () => {
    const mesh = equipmentPrimitiveData(parts[0]);
    const xs = mesh.positions.filter((_, index) => index % 3 === 0);
    const ys = mesh.positions.filter((_, index) => index % 3 === 1);
    const zs = mesh.positions.filter((_, index) => index % 3 === 2);

    expect(Math.min(...xs)).toBe(-1);
    expect(Math.max(...xs)).toBe(1);
    expect(Math.min(...ys)).toBe(-2);
    expect(Math.max(...ys)).toBe(2);
    expect(Math.min(...zs)).toBe(-3);
    expect(Math.max(...zs)).toBe(3);
  });

  it('honours sphere and torus extents', () => {
    const sphere = equipmentPrimitiveData(parts[2]);
    const sphereValues = sphere.positions;
    const sphereXs = sphereValues.filter((_, index) => index % 3 === 0);
    const sphereYs = sphereValues.filter((_, index) => index % 3 === 1);
    const sphereZs = sphereValues.filter((_, index) => index % 3 === 2);
    expect(Math.max(...sphereXs)).toBeCloseTo(2, 6);
    expect(Math.min(...sphereXs)).toBeCloseTo(-2, 6);
    expect(Math.max(...sphereYs)).toBeCloseTo(2, 6);
    expect(Math.min(...sphereYs)).toBeCloseTo(-2, 6);
    expect(Math.max(...sphereZs)).toBeCloseTo(2, 6);
    expect(Math.min(...sphereZs)).toBeCloseTo(-2, 6);

    const torus = equipmentPrimitiveData(parts[3]);
    const torusXs = torus.positions.filter((_, index) => index % 3 === 0);
    const torusYs = torus.positions.filter((_, index) => index % 3 === 1);
    const torusZs = torus.positions.filter((_, index) => index % 3 === 2);
    expect(Math.max(...torusXs)).toBeCloseTo(2.5, 6);
    expect(Math.min(...torusXs)).toBeCloseTo(-2.5, 6);
    expect(Math.max(...torusYs)).toBeCloseTo(2.5, 6);
    expect(Math.min(...torusYs)).toBeCloseTo(-2.5, 6);
    expect(Math.max(...torusZs)).toBeGreaterThan(0.45);
    expect(Math.max(...torusZs)).toBeLessThanOrEqual(0.5);
    expect(Math.min(...torusZs)).toBeLessThan(-0.45);
    expect(Math.min(...torusZs)).toBeGreaterThanOrEqual(-0.5);
  });
});
