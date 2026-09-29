import { describe, expect, it } from 'vitest';
import {
  boxPrimitiveData,
  cylinderPrimitiveData,
  spherePrimitiveData,
  torusPrimitiveData,
  primitiveTrianglePositions,
} from './primitiveGeometry';

const validate = (mesh: ReturnType<typeof boxPrimitiveData>) => {
  const vertices = mesh.positions.length / 3;
  expect(mesh.positions.length % 3).toBe(0);
  expect(mesh.normals).toHaveLength(mesh.positions.length);
  expect(mesh.uvs).toHaveLength(vertices * 2);
  expect(mesh.indices.length % 3).toBe(0);
  expect(Math.max(...mesh.indices)).toBeLessThan(vertices);
  for (let index = 0; index < mesh.normals.length; index += 3) {
    const length = Math.hypot(
      mesh.normals[index],
      mesh.normals[index + 1],
      mesh.normals[index + 2],
    );
    expect(length).toBeCloseTo(1, 8);
  }
};

describe('first-party shared primitive geometry', () => {
  it('builds deterministic box geometry', () => {
    const mesh = boxPrimitiveData([1, 2, 3]);
    validate(mesh);
    expect(mesh.positions).toHaveLength(24 * 3);
    expect(mesh.indices).toHaveLength(12 * 3);
    expect(mesh.positions.slice(0, 12)).toEqual([
      0.5, -1, -1.5,
      0.5, 1, -1.5,
      0.5, 1, 1.5,
      0.5, -1, 1.5,
    ]);
  });

  it('builds valid cylinder, sphere and torus meshes from project-owned maths', () => {
    for (const mesh of [
      cylinderPrimitiveData(0.2, 0.1, 1, 12),
      spherePrimitiveData(0.4, 12, 8),
      torusPrimitiveData(0.6, 0.1, Math.PI * 2, 8, 16),
    ]) {
      validate(mesh);
      expect(mesh.positions.length).toBeGreaterThan(0);
      expect(mesh.indices.length).toBeGreaterThan(0);
    }
  });
  it('expands indexed geometry into deterministic triangle draw order', () => {
    const box = boxPrimitiveData([1, 2, 3]);
    const triangles = primitiveTrianglePositions(box);
    expect(triangles).toHaveLength(box.indices.length * 3);
    expect(Array.from(triangles.slice(0, 9))).toEqual(
      box.indices.slice(0, 3).flatMap((vertex) =>
        box.positions.slice(vertex * 3, vertex * 3 + 3),
      ),
    );
    expect(() => primitiveTrianglePositions({
      ...box,
      indices: [999, 0, 1],
    })).toThrow(/outside the vertex buffer/);
  });

});
