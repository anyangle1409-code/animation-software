import { describe, expect, it } from 'vitest';
import { buildHgReferenceGrid } from './referenceGrid';

describe('first-party reference grid geometry', () => {
  it('recreates the current 12 m / 0.25 m / 1 m studio grid', () => {
    const lines = buildHgReferenceGrid();
    expect(lines).toHaveLength(98);
    expect(lines.filter((line) => line.major)).toHaveLength(26);
  });

  it('places the grid just above the floor to avoid z fighting', () => {
    const lines = buildHgReferenceGrid();
    for (const line of lines) {
      expect(line.start.y).toBeCloseTo(0.001, 12);
      expect(line.end.y).toBeCloseTo(0.001, 12);
    }
  });

  it('rejects invalid spacing rather than producing corrupt geometry', () => {
    expect(() => buildHgReferenceGrid({ cellSize: 0 })).toThrow(/positive/);
    expect(() => buildHgReferenceGrid({ sectionSize: -1 })).toThrow(/positive/);
  });
});
