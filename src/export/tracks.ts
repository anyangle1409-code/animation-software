export interface CompressedTrack {
  values: number[];
  constant: boolean;
}

/**
 * Shrink a sampled track.
 *
 * A track that never changes is reduced to two keys — but only dropped
 * altogether when its constant value is the bone's rest value. Dropping a
 * constant track that differs from rest would silently reset the bone: a
 * planted foot, a closed grip or a set stance would all snap back on export.
 */
export function compressTrack(
  values: number[],
  stride: number,
  restValue: number[],
): CompressedTrack | null {
  if (values.length < stride) return null;
  if (!isStatic(values, stride)) return { values, constant: false };

  const first = values.slice(0, stride);
  const atRest = first.every((value, index) => Math.abs(value - restValue[index]) < 1e-6);
  if (atRest) return null;
  return { values: [...first, ...first], constant: true };
}

/** True when every sample of a track is the same, so the track can be dropped. */
function isStatic(values: number[], stride: number): boolean {
  if (values.length <= stride) return true;
  for (let index = stride; index < values.length; index += 1) {
    if (Math.abs(values[index] - values[index % stride]) > 1e-6) return false;
  }
  return true;
}
