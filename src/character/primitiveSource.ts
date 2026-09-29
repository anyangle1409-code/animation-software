export interface HgCharacterPrimitiveSource {
  readonly nodeIndex: number;
  readonly meshIndex: number;
  readonly primitiveIndex: number;
  readonly targetNames: readonly string[];
}

const primitiveSources = new WeakMap<object, HgCharacterPrimitiveSource>();

/** Record the exact source GLB primitive represented by one runtime mesh. */
export function setCharacterPrimitiveSource(
  object: object,
  source: HgCharacterPrimitiveSource,
): void {
  primitiveSources.set(object, {
    nodeIndex: source.nodeIndex,
    meshIndex: source.meshIndex,
    primitiveIndex: source.primitiveIndex,
    targetNames: [...source.targetNames],
  });
}

/** Exact source GLB primitive represented by one runtime mesh. */
export function characterPrimitiveSource(
  object: object,
): HgCharacterPrimitiveSource | null {
  return primitiveSources.get(object) ?? null;
}
