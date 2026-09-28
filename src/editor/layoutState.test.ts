import { describe, expect, it } from 'vitest';
import { studioLayoutStore } from './layoutState';

describe('framework-neutral Studio layout state', () => {
  it('owns the current tab and panel defaults', () => {
    studioLayoutStore.setState({
      leftTab: 'joint',
      rightTab: 'exercise',
      panelsOpen: true,
    });
    expect(studioLayoutStore.getState().leftTab).toBe('joint');
    expect(studioLayoutStore.getState().rightTab).toBe('exercise');
    expect(studioLayoutStore.getState().panelsOpen).toBe(true);
  });

  it('switches tabs and panel visibility without React', () => {
    const state = studioLayoutStore.getState();
    state.setLeftTab('equipment');
    state.setRightTab('review');
    state.togglePanels();

    expect(studioLayoutStore.getState().leftTab).toBe('equipment');
    expect(studioLayoutStore.getState().rightTab).toBe('review');
    expect(studioLayoutStore.getState().panelsOpen).toBe(false);

    studioLayoutStore.getState().setPanelsOpen(true);
    expect(studioLayoutStore.getState().panelsOpen).toBe(true);
  });
});
