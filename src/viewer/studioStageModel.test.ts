import { describe, expect, it } from 'vitest';
import { BACKDROPS } from '../editor/storeCore';
import { buildHgStageModel } from './studioStageModel';

describe('first-party Studio stage model', () => {
  it('owns the stage lighting, floor and grid configuration as plain data', () => {
    const model = buildHgStageModel(BACKDROPS.studio, true);

    expect(model.background).toBe('#12151a');
    expect(model.hemisphere).toEqual({
      sky: '#f0f4fb',
      ground: '#171b21',
      intensity: BACKDROPS.studio.lighting.ambient,
    });
    expect(model.key.position).toEqual([3, 5, 4]);
    expect(model.key.castShadow).toBe(true);
    expect(model.key.shadowMapSize).toEqual([1024, 1024]);
    expect(model.key.shadowBounds).toEqual({
      left: -3,
      right: 3,
      top: 3,
      bottom: -3,
    });
    expect(model.rim.position).toEqual([-3, 2.5, -2]);
    expect(model.floor).toMatchObject({
      colour: '#171b21',
      size: [24, 24],
      roughness: 0.95,
      receiveShadow: true,
    });
    expect(model.floor?.rotationX).toBeCloseTo(-Math.PI / 2, 12);
    expect(model.grid?.buffers.minor.length).toBeGreaterThan(0);
    expect(model.grid?.buffers.major.length).toBeGreaterThan(0);
  });

  it('removes floor, grid and key shadows for floorless backdrops', () => {
    const model = buildHgStageModel(BACKDROPS.void, true);
    expect(model.floor).toBeNull();
    expect(model.grid).toBeNull();
    expect(model.key.castShadow).toBe(false);
  });

  it('honours the grid toggle without changing stage lighting or floor', () => {
    const withGrid = buildHgStageModel(BACKDROPS.light, true);
    const withoutGrid = buildHgStageModel(BACKDROPS.light, false);
    expect(withGrid.grid).not.toBeNull();
    expect(withoutGrid.grid).toBeNull();
    expect(withoutGrid.floor).toEqual(withGrid.floor);
    expect(withoutGrid.key).toEqual(withGrid.key);
    expect(withoutGrid.rim).toEqual(withGrid.rim);
  });
});
