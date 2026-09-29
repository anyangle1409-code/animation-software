import { describe, expect, it } from 'vitest';
import { BACKDROPS } from '../editor/storeCore';
import { HgPrimitiveMesh } from '../core/sceneMesh';
import { createHgStudioStage } from './firstPartyStudioStage';

describe('first-party Studio static stage', () => {
  it('keeps backdrop, floor and two-level reference grid in project-owned scene nodes', () => {
    const stage = createHgStudioStage(BACKDROPS.studio, true);
    expect(stage.background).toBe(BACKDROPS.studio.background);
    expect(stage.floor?.name).toBe('hgpt-stage-floor');
    expect(stage.grid?.name).toBe('hgpt-reference-grid');
    expect(stage.grid?.children).toHaveLength(2);
    expect(stage.grid?.children.every((child) => child instanceof HgPrimitiveMesh)).toBe(true);
    for (const child of stage.grid!.children as HgPrimitiveMesh[]) {
      expect(child.geometry.positions.length).toBeGreaterThan(0);
      expect(child.geometry.indices.length).toBeGreaterThan(0);
    }
    stage.dispose();
    expect(stage.root.children).toHaveLength(0);
  });

  it('keeps floorless backdrops free of floor and grid', () => {
    const stage = createHgStudioStage(BACKDROPS.void, true);
    expect(stage.background).toBe('#000000');
    expect(stage.floor).toBeNull();
    expect(stage.grid).toBeNull();
    expect(stage.root.children).toHaveLength(0);
  });
});
