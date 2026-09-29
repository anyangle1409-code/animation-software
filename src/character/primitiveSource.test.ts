import { describe, expect, it } from 'vitest';
import {
  characterPrimitiveSource,
  setCharacterPrimitiveSource,
} from './primitiveSource';

describe('character primitive source registry', () => {
  it('retains exact GLB primitive identity independently of the scene implementation', () => {
    const object = {};
    setCharacterPrimitiveSource(object, {
      nodeIndex: 3,
      meshIndex: 2,
      primitiveIndex: 1,
      targetNames: ['bend'],
    });
    expect(characterPrimitiveSource(object)).toEqual({
      nodeIndex: 3,
      meshIndex: 2,
      primitiveIndex: 1,
      targetNames: ['bend'],
    });
  });

  it('copies target-name arrays so callers cannot mutate provenance', () => {
    const object = {};
    const names = ['one'];
    setCharacterPrimitiveSource(object, {
      nodeIndex: 0,
      meshIndex: 0,
      primitiveIndex: 0,
      targetNames: names,
    });
    names.push('two');
    expect(characterPrimitiveSource(object)?.targetNames).toEqual(['one']);
  });
});
