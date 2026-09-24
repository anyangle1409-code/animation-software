import { describe, expect, it } from 'vitest';
import { Euler, Matrix4, Quaternion, Vector3 } from 'three';
import { EQUIPMENT_PARTS } from './geometry';
import { equipmentPartDistances } from '../constraints/collision';
import { EXERCISES } from '../exercises/library';
import { mirrorInvariant, reflectBakedTrack, reflectedStaticPlacement, reflectPlacement } from './mirror';
import type { EquipmentKind } from './types';

/**
 * Reflecting what the rig placed into a mirrored character's world
 * (`equipment/mirror.ts`).
 */

/**
 * The two kinds whose shape is not its own mirror image. Both are two-handed
 * bars no exercise uses yet; a baked two-hand track reflected with S·M·S would
 * draw them with their bends the wrong way round.
 */
const NOT_SELF_MIRRORED = new Set<EquipmentKind>(['ez_curl_bar', 'lat_pulldown_bar']);

describe('reflecting rig-placed equipment', () => {
  it('draws the same item: every other kind is its own mirror image about local x = 0', () => {
    let seed = 7;
    const random = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
    for (const kind of Object.keys(EQUIPMENT_PARTS) as EquipmentKind[]) {
      let worst = 0;
      for (let sample = 0; sample < 2000; sample += 1) {
        const point = new Vector3(random() * 2 - 1, random() * 2.5 - 0.2, random() * 2 - 1);
        const here = Math.min(...equipmentPartDistances(kind, point));
        const there = Math.min(...equipmentPartDistances(kind, point.clone().setX(-point.x)));
        worst = Math.max(worst, Math.abs(here - there));
      }
      if (NOT_SELF_MIRRORED.has(kind)) expect(worst, kind).toBeGreaterThan(0.01);
      else expect(worst, kind).toBeLessThan(1e-9);
    }
  });

  it('uses none of the kinds that are not, in any exercise', () => {
    for (const exercise of EXERCISES) {
      for (const instance of exercise.equipment.instances) expect(NOT_SELF_MIRRORED.has(instance.kind), exercise.id).toBe(false);
    }
  });

  it('puts an item where the mirror puts it, as a proper rotation', () => {
    const matrix = new Matrix4().compose(
      new Vector3(0.9, 1.2, 0.3),
      new Quaternion().setFromEuler(new Euler(0.3, -0.7, 0.2)),
      new Vector3(1, 1.5, 1),
    );
    const reflected = reflectPlacement(matrix);
    expect(reflected.determinant()).toBeCloseTo(matrix.determinant(), 12);
    // A point on the item lands on the mirror image of where it was.
    const local = new Vector3(0.1, 0.2, -0.3);
    const before = local.clone().applyMatrix4(matrix);
    const after = local.clone().setX(-local.x).applyMatrix4(reflected);
    expect(after.distanceTo(before.setX(-before.x))).toBeLessThan(1e-12);
    // In place, as the clearance test uses it.
    expect(reflectPlacement(matrix.clone(), undefined).equals(reflectPlacement(matrix))).toBe(true);
    const same = matrix.clone();
    expect(reflectPlacement(same, same).equals(reflected)).toBe(true);
  });

  it('reflects a static placement and a baked track the same way as a matrix', () => {
    const instance = { position: { x: 0.9, y: 0, z: 0.35 }, rotation: { x: 10, y: -90, z: 5 } };
    const R = Math.PI / 180;
    const toMatrix = (placement: typeof instance) =>
      new Matrix4().compose(
        new Vector3(placement.position.x, placement.position.y, placement.position.z),
        new Quaternion().setFromEuler(new Euler(placement.rotation.x * R, placement.rotation.y * R, placement.rotation.z * R, 'XYZ')),
        new Vector3(1, 1, 1),
      );
    const expected = reflectPlacement(toMatrix(instance));
    const actual = toMatrix(reflectedStaticPlacement(instance));
    for (let index = 0; index < 16; index += 1) expect(actual.elements[index]).toBeCloseTo(expected.elements[index], 12);

    const quaternion = new Quaternion().setFromEuler(new Euler(0.3, -0.7, 0.2));
    const track = { position: [0.9, 1.2, 0.3], quaternion: quaternion.toArray() };
    reflectBakedTrack(track);
    const baked = new Matrix4().compose(new Vector3(...track.position), new Quaternion(...track.quaternion), new Vector3(1, 1, 1));
    const matrix = reflectPlacement(new Matrix4().compose(new Vector3(0.9, 1.2, 0.3), quaternion, new Vector3(1, 1, 1)));
    for (let index = 0; index < 16; index += 1) expect(baked.elements[index]).toBeCloseTo(matrix.elements[index], 12);
  });

  it('leaves an item already its own mirror image exactly as it was', () => {
    expect(mirrorInvariant({ position: { x: 0, y: 0, z: -0.45 }, rotation: { x: 0, y: 180, z: 0 } })).toBe(true);
    expect(mirrorInvariant({ position: { x: 0, y: 0, z: 0 }, rotation: { x: 30, y: -180, z: 0 } })).toBe(true);
    expect(mirrorInvariant({ position: { x: 0.9, y: 0, z: 0 }, rotation: { x: 0, y: -90, z: 0 } })).toBe(false);
    expect(mirrorInvariant({ position: { x: 0, y: 0, z: 0 }, rotation: { x: 0, y: -90, z: 0 } })).toBe(false);
    // And never writes −0 for a zero.
    const reflected = reflectedStaticPlacement({ position: { x: 0, y: 0, z: 0 }, rotation: { x: 0, y: 0, z: 0 } });
    expect(Object.is(reflected.position.x, 0) && Object.is(reflected.rotation.y, 0) && Object.is(reflected.rotation.z, 0)).toBe(true);
  });
});
