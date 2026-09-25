import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { EQUIPMENT_PARTS, equipmentParts } from './geometry';
import { equipmentDistance, equipmentPartDistances } from '../constraints/collision';
import type { EquipmentKind } from './types';

/**
 * The incline bench's back pad is a per-instance parameter (`EquipmentInstance.
 * backAngle`), not a fixed shape: `equipmentParts` is the one function every
 * consumer — the viewport, the GLB export, the collision envelope, the
 * body-clearance measurement — asks for it, so none of them can draw or
 * measure a bench the others disagree with.
 *
 * At the bench's default 45°, that function must be exactly what it always
 * was: a hand-placed box, not a value recomputed through floating-point trig
 * that happens to be close.
 */
describe('the incline bench back angle', () => {
  it('is byte-identical to today at 45°, with no angle given', () => {
    expect(equipmentParts('incline_bench')).toEqual(EQUIPMENT_PARTS.incline_bench);
  });

  it('is byte-identical to today at 45°, given explicitly', () => {
    expect(equipmentParts('incline_bench', 45)).toEqual(EQUIPMENT_PARTS.incline_bench);
    const pad = equipmentParts('incline_bench', 45)[0];
    expect(pad).toEqual({
      shape: 'box',
      size: [0.32, 0.09, 0.8],
      position: [0, 0.691, 0.105],
      rotation: [-Math.PI / 4, 0, 0],
      material: 'pad',
    });
  });

  it('ignores the angle for every other kind', () => {
    for (const kind of Object.keys(EQUIPMENT_PARTS) as EquipmentKind[]) {
      if (kind === 'incline_bench') continue;
      expect(equipmentParts(kind, 30)).toBe(EQUIPMENT_PARTS[kind]);
    }
  });

  it("rotates the pad by the angle asked for, and only the pad", () => {
    for (const angle of [20, 30, 60, 75]) {
      const parts = equipmentParts('incline_bench', angle);
      // Every other part is unmoved.
      expect(parts.slice(1)).toEqual(EQUIPMENT_PARTS.incline_bench.slice(1));
      const pad = parts[0];
      if (pad.shape !== 'box') throw new Error('unexpected part');
      expect(pad.rotation).toEqual([(-angle * Math.PI) / 180, 0, 0]);
    }
  });

  it('hinges the pad at the seat, however far it reclines', () => {
    // The pad's top-near corner before rotation — (x, y = 0.045, z = -0.4) in
    // its own local frame — is the point that lands on the seat's top, at its
    // back edge, for every angle the generic formula computes. (The 45° case
    // is excluded: it is kept as today's literal hand-placed box rather than
    // this formula, and the two agree only to within its original rounding,
    // about 0.02 mm — see the byte-identical tests above for what 45° must
    // match exactly.)
    const hinge = (angle: number) => {
      const pad = equipmentParts('incline_bench', angle)[0];
      if (pad.shape !== 'box' || !pad.rotation) throw new Error('unexpected part');
      const [rx] = pad.rotation;
      const [, py, pz] = pad.position ?? [0, 0, 0];
      const cos = Math.cos(rx);
      const sin = Math.sin(rx);
      const t = 0.045;
      const L = 0.4;
      // Rotate the local corner (y=t, z=-L) by rx and add the pad's centre.
      const y = py + (t * cos - -L * sin);
      const z = pz + (t * sin + -L * cos);
      return { y, z };
    };
    for (const angle of [20, 30, 60, 75, 90]) {
      const here = hinge(angle);
      expect(here.y).toBeCloseTo(0.44, 9);
      expect(here.z).toBeCloseTo(-0.21, 9);
    }
  });

  it('the collision envelope reads the same angle the viewport and export draw', () => {
    // A point sitting exactly at 45°'s pad centre is deep inside the pad at
    // 45°, but the pad has rotated away from it at a very different angle, so
    // the envelope must disagree between the two — proving `equipmentDistance`
    // actually consults the angle rather than a cached default.
    const point = new Vector3(0, 0.691, 0.105);
    const at45 = equipmentDistance('incline_bench', point, 45);
    const at90 = equipmentDistance('incline_bench', point, 90);
    expect(at45).toBeLessThan(0);
    expect(at90).toBeGreaterThan(at45);
  });

  it('equipmentPartDistances agrees with equipmentDistance, at any angle', () => {
    const point = new Vector3(0.05, 0.5, -0.3);
    for (const angle of [30, 45, 60]) {
      const distances = equipmentPartDistances('incline_bench', point, angle);
      expect(Math.min(...distances)).toBeCloseTo(equipmentDistance('incline_bench', point, angle), 9);
    }
  });
});
