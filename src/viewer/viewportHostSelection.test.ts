import { describe, expect, it } from 'vitest';
import { viewportHostFromSearch } from './viewportHostSelection';

describe('viewport host selection', () => {
  it('uses the first-party host by default', () => {
    expect(viewportHostFromSearch('')).toBe('first-party');
    expect(viewportHostFromSearch('?sceneHost=unknown')).toBe('first-party');
    expect(viewportHostFromSearch('?sceneHost=first-party')).toBe('first-party');
  });

  it('keeps R3F available only as an explicit rollback/reference path', () => {
    expect(viewportHostFromSearch('?sceneHost=r3f')).toBe('r3f');
    expect(viewportHostFromSearch('?x=1&sceneHost=r3f')).toBe('r3f');
  });
});
