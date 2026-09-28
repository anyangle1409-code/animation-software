import { describe, expect, it } from 'vitest';
import { solvedGripFor } from './solvedGrip';

describe('solved cylindrical grip registry', () => {
  it('ships no legacy character-specific solved grip during the clean-room transition', () => {
    expect(solvedGripFor('legacy-baseline', 'dumbbell')).toBeNull();
    expect(solvedGripFor('original-v1', 'dumbbell')).toBeNull();
  });

  it('falls back to the authored grip profile when no solution id is supplied', () => {
    expect(solvedGripFor(undefined, 'dumbbell')).toBeNull();
    expect(solvedGripFor(undefined, 'bar')).toBeNull();
    expect(solvedGripFor(undefined, 'floor')).toBeNull();
  });
});
