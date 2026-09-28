import { describe, expect, it } from 'vitest';
import { viewportHostFromSearch } from './viewportHostSelection';

describe('viewport host selection', () => {
  it('keeps R3F as the default reference path', () => {
    expect(viewportHostFromSearch('')).toBe('r3f');
    expect(viewportHostFromSearch('?sceneHost=r3f')).toBe('r3f');
    expect(viewportHostFromSearch('?sceneHost=unknown')).toBe('r3f');
  });

  it('enables the reversible first-party host explicitly', () => {
    expect(viewportHostFromSearch('?sceneHost=first-party')).toBe('first-party');
    expect(viewportHostFromSearch('?x=1&sceneHost=first-party')).toBe('first-party');
  });
});
