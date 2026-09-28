import { describe, expect, it, vi } from 'vitest';
import { LineSegments } from 'three';
import { BACKDROPS } from '../editor/store';
import { createStudioStage } from './studioStage';

describe('project-owned Studio static stage', () => {
  it('reproduces the working stage lights, floor, grid and shadow settings', () => {
    const stage = createStudioStage(BACKDROPS.studio, true);

    expect(stage.background.getHexString()).toBe('12151a');
    expect(stage.hemisphere.intensity).toBe(BACKDROPS.studio.lighting.ambient);
    expect(stage.hemisphere.groundColor.getHexString()).toBe('171b21');

    expect(stage.key.position.toArray()).toEqual([3, 5, 4]);
    expect(stage.key.intensity).toBe(BACKDROPS.studio.lighting.key);
    expect(stage.key.castShadow).toBe(true);
    expect(stage.key.shadow.mapSize.width).toBe(1024);
    expect(stage.key.shadow.mapSize.height).toBe(1024);
    expect(stage.key.shadow.camera.left).toBe(-3);
    expect(stage.key.shadow.camera.right).toBe(3);
    expect(stage.key.shadow.camera.top).toBe(3);
    expect(stage.key.shadow.camera.bottom).toBe(-3);

    expect(stage.rim.position.toArray()).toEqual([-3, 2.5, -2]);
    expect(stage.rim.intensity).toBe(BACKDROPS.studio.lighting.rim);
    expect(stage.rim.color.getHexString()).toBe('9fc4ff');

    expect(stage.grid?.name).toBe('hgpt-reference-grid');
    expect(stage.grid?.children).toHaveLength(2);
    expect(stage.floor?.name).toBe('hgpt-stage-floor');
    expect(stage.floor?.rotation.x).toBeCloseTo(-Math.PI / 2, 12);
    expect(stage.floor?.receiveShadow).toBe(true);

    stage.dispose();
  });

  it('keeps floorless backdrops free of floor/grid/shadow casting', () => {
    const stage = createStudioStage(BACKDROPS.void, true);

    expect(stage.background.getHexString()).toBe('000000');
    expect(stage.floor).toBeNull();
    expect(stage.grid).toBeNull();
    expect(stage.key.castShadow).toBe(false);
    expect(stage.root.children).toEqual([stage.hemisphere, stage.key, stage.rim]);

    stage.dispose();
  });

  it('honours the grid toggle without changing the floor or lights', () => {
    const stage = createStudioStage(BACKDROPS.light, false);

    expect(stage.grid).toBeNull();
    expect(stage.floor).not.toBeNull();
    expect(stage.root.children).toContain(stage.hemisphere);
    expect(stage.root.children).toContain(stage.key);
    expect(stage.root.children).toContain(stage.rim);
    expect(stage.root.children).toContain(stage.floor);

    stage.dispose();
  });

  it('disposes owned geometry/material resources exactly once', () => {
    const stage = createStudioStage(BACKDROPS.studio, true);
    const floorGeometry = vi.spyOn(stage.floor!.geometry, 'dispose');
    const floorMaterial = vi.spyOn(stage.floor!.material, 'dispose');
    const gridDisposals = stage.grid!.children.flatMap((child) => {
      const line = child as LineSegments;
      const material = Array.isArray(line.material) ? line.material[0] : line.material;
      return [vi.spyOn(line.geometry, 'dispose'), vi.spyOn(material, 'dispose')];
    });

    stage.dispose();
    stage.dispose();

    expect(floorGeometry).toHaveBeenCalledTimes(1);
    expect(floorMaterial).toHaveBeenCalledTimes(1);
    for (const dispose of gridDisposals) expect(dispose).toHaveBeenCalledTimes(1);
    expect(stage.root.children).toHaveLength(0);
  });
});
