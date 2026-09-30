import { describe, expect, it } from 'vitest';
import { HgMat4 } from '../core/linearMath';
import { cableMatrix, handAttachmentLocalMatrix, socketWorldPoint, twoHandAttachmentMatrix } from '../equipment/attach';
import type { EquipmentInstance } from '../equipment/types';
import { equipmentSocketForInstance } from '../equipment/library';
import { reflectPlacement } from '../equipment/mirror';
import { resolveEquipmentDisplayTransforms } from './equipmentDisplayTransforms';

interface MatrixLike {
  readonly elements: ArrayLike<number>;
}

const matrixValues = (matrix: MatrixLike | null) => matrix ? Array.from(matrix.elements) : null;

const expectMatrixClose = (actual: MatrixLike | null, expected: MatrixLike) => {
  expect(actual).not.toBeNull();
  const values = actual!.elements;
  for (let index = 0; index < 16; index += 1) {
    expect(values[index]).toBeCloseTo(expected.elements[index], 10);
  }
};

const instance = (
  id: string,
  kind: EquipmentInstance['kind'],
  attachment: EquipmentInstance['attachment'],
): EquipmentInstance => ({
  id,
  kind,
  position: { x: 0, y: 0, z: 0 },
  rotation: { x: 0, y: 0, z: 0 },
  attachment,
  visible: true,
});

describe('equipment display transforms', () => {
  it('copies canonical display matrices and hides a visible instance with no resolved transform', () => {
    const shown = instance('shown', 'flat_bench', { mode: 'static' });
    const missing = instance('missing', 'flat_bench', { mode: 'static' });
    const canonical = new HgMat4().makeTranslation(0.2, 0.4, -0.6);
    const result = resolveEquipmentDisplayTransforms(
      [shown, missing],
      new Map([['shown', { matrix: canonical }]]),
      null,
    );

    expect(result.get('shown')?.visible).toBe(true);
    expect(matrixValues(result.get('shown')?.matrix ?? null)).toEqual([...canonical.elements]);
    expect(result.get('shown')?.matrix).not.toBe(canonical);
    expect(result.get('missing')).toEqual({ visible: false, matrix: null });
  });

  it('uses the character hand and character-specific grip centre for a held item', () => {
    const dumbbell = instance('db_l', 'dumbbell', {
      mode: 'hand',
      side: 'l',
      socket: 'grip',
    });
    const hand = new HgMat4().makeTranslation(-0.31, 1.14, 0.22);
    const grip = { x: -0.041, y: 0.094, z: 0.013 };
    const result = resolveEquipmentDisplayTransforms(
      [dumbbell],
      new Map([['db_l', { matrix: new HgMat4().makeTranslation(-9, -9, -9) }]]),
      {
        handMatrix: (_side, target) => target.copy(hand),
        gripOffset: () => grip,
      },
    );

    const socket = equipmentSocketForInstance(dumbbell, 'grip')!;
    const expected = new HgMat4().multiplyMatrices(
      hand,
      handAttachmentLocalMatrix(grip, socket.position, { socketRotation: socket.rotation }),
    );
    expectMatrixClose(result.get('db_l')?.matrix ?? null, expected);
  });

  it('reflects canonical world placement for a mirrored character when no hand override applies', () => {
    const bench = instance('bench', 'flat_bench', { mode: 'static' });
    const canonical = new HgMat4().makeTranslation(0.45, 0.5, -0.2);
    const result = resolveEquipmentDisplayTransforms(
      [bench],
      new Map([['bench', { matrix: canonical }]]),
      { mirrored: true },
    );
    expectMatrixClose(result.get('bench')?.matrix ?? null, reflectPlacement(canonical));
  });

  it('fits a rigid two-hand item to the character own two hand matrices', () => {
    const bar = instance('bar', 'barbell', {
      mode: 'hands',
      leftSocket: 'grip_l',
      rightSocket: 'grip_r',
    });
    const left = new HgMat4().makeTranslation(-0.31, 1.12, 0.18);
    const right = new HgMat4().makeTranslation(0.31, 1.12, 0.18);
    const result = resolveEquipmentDisplayTransforms(
      [bar],
      new Map([['bar', { matrix: new HgMat4().makeTranslation(0, -5, 0) }]]),
      {
        handMatrix: (side, target) => target.copy(side === 'l' ? left : right),
      },
    );
    expectMatrixClose(result.get('bar')?.matrix ?? null, twoHandAttachmentMatrix(left, right, bar)!);
  });

  it('draws a cable between the placements actually drawn after a character hand override', () => {
    const tower = instance('tower', 'cable_tower', { mode: 'static' });
    const handle = instance('handle', 'cable_handle', {
      mode: 'hand',
      side: 'r',
      socket: 'grip',
    });
    const cable = instance('cable', 'cable', {
      mode: 'cable',
      from: { equipment: 'tower', socket: 'pulley' },
      to: { equipment: 'handle', socket: 'clip' },
    });

    const towerMatrix = new HgMat4().makeTranslation(-0.7, 0, 0.2);
    const canonicalHandle = new HgMat4().makeTranslation(9, 9, 9);
    const rightHand = new HgMat4().makeTranslation(0.42, 1.08, -0.16);
    const result = resolveEquipmentDisplayTransforms(
      [tower, handle, cable],
      new Map([
        ['tower', { matrix: towerMatrix }],
        ['handle', { matrix: canonicalHandle }],
      ]),
      {
        handMatrix: (_side, target) => target.copy(rightHand),
      },
    );

    const drawnTower = result.get('tower')!.matrix!;
    const drawnHandle = result.get('handle')!.matrix!;
    const from = socketWorldPoint(tower, 'pulley', drawnTower)!;
    const to = socketWorldPoint(handle, 'clip', drawnHandle)!;
    const expected = cableMatrix(from, to).matrix;

    expectMatrixClose(result.get('cable')?.matrix ?? null, expected);
    expect(matrixValues(drawnHandle)).not.toEqual([...canonicalHandle.elements]);
  });
});
