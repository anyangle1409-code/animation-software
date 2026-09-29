import { describe, expect, it } from 'vitest';
import { HgMat4 } from '../core/linearMath';
import { hgRgbaFromHex } from '../core/sceneMesh';
import { equipmentParts, MATERIALS } from '../equipment/geometry';
import type { EquipmentInstance } from '../equipment/types';
import {
  applyHgEquipmentDisplayTransforms,
  createHgEquipmentScene,
} from './firstPartyEquipmentScene';

const instance = (
  id: string,
  kind: EquipmentInstance['kind'],
  visible = true,
): EquipmentInstance => ({
  id,
  kind,
  position: { x: 0, y: 0, z: 0 },
  rotation: { x: 0, y: 0, z: 0 },
  attachment: { mode: 'static' },
  visible,
});

describe('first-party equipment visual scene', () => {
  it('builds exact shared authored parts with project-owned geometry/materials', () => {
    const dumbbell = instance('db', 'dumbbell');
    const resources = createHgEquipmentScene([dumbbell]);
    const built = resources.instances.get('db');
    expect(built).toBeDefined();

    const authored = equipmentParts('dumbbell');
    expect(built!.parts).toHaveLength(authored.length);
    expect(resources.group.children).toContain(built!.group);

    authored.forEach((part, index) => {
      const mesh = built!.parts[index];
      expect(mesh.geometry.positions.length).toBeGreaterThan(0);
      expect(mesh.geometry.indices.length).toBeGreaterThan(0);
      expect(mesh.material.colour).toEqual(
        hgRgbaFromHex(MATERIALS[part.material].color),
      );
      expect(mesh.position.toArray()).toEqual(part.position ?? [0, 0, 0]);
    });

    resources.dispose();
  });

  it('applies the same resolved display matrix and inherited visibility', () => {
    const resources = createHgEquipmentScene([
      instance('bench', 'flat_bench'),
      instance('hidden', 'dumbbell'),
    ]);
    const matrix = new HgMat4().makeTranslation(0.25, 0.4, -0.3);
    applyHgEquipmentDisplayTransforms(resources, new Map([
      ['bench', { visible: true, matrix }],
      ['hidden', { visible: false, matrix: null }],
    ]));

    const bench = resources.instances.get('bench')!;
    const hidden = resources.instances.get('hidden')!;
    expect(bench.group.visible).toBe(true);
    expect(bench.group.matrix.toArray()).toEqual(matrix.toArray());
    expect(hidden.group.visible).toBe(false);

    resources.group.updateMatrixWorld(true);
    expect(bench.group.matrixWorld.elements[12]).toBeCloseTo(0.25, 10);
    expect(bench.group.matrixWorld.elements[13]).toBeCloseTo(0.4, 10);
    expect(bench.group.matrixWorld.elements[14]).toBeCloseTo(-0.3, 10);
    resources.dispose();
  });

  it('omits authored-invisible instances and disposes deterministically', () => {
    const resources = createHgEquipmentScene([
      instance('shown', 'kettlebell'),
      instance('not_shown', 'kettlebell', false),
    ]);
    expect(resources.instances.has('shown')).toBe(true);
    expect(resources.instances.has('not_shown')).toBe(false);
    resources.dispose();
    resources.dispose();
    expect(resources.group.children).toHaveLength(0);
    expect(resources.instances.size).toBe(0);
  });
});
