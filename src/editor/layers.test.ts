import { describe, expect, it } from 'vitest';
import { layersForViewMode, useStudio } from './store';

describe('view layers', () => {
  it('opens with the character visible alongside the skeleton', () => {
    const { layers } = useStudio.getState();
    expect(layers.character).toBe(true);
    expect(layers.skeleton).toBe(true);
  });

  it('lets skeleton, muscles and character all be on together', () => {
    const store = useStudio.getState();
    if (!useStudio.getState().layers.muscles) store.toggleLayer('muscles');
    const { layers } = useStudio.getState();
    expect(layers).toEqual({ skeleton: true, muscles: true, character: true });
    store.toggleLayer('muscles');
  });

  it('keeps the old single view modes as presets', () => {
    expect(layersForViewMode('character').layers).toEqual({ skeleton: false, muscles: false, character: true });
    expect(layersForViewMode('combined').layers).toEqual({ skeleton: true, muscles: true, character: false });
    expect(layersForViewMode('anatomy').characterStyle).toBe('anatomy');
  });
});
