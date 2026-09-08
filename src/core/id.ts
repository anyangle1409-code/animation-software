let counter = 0;

/** Deterministic-enough unique id for editor entities (keyframes, targets…). */
export function nextId(prefix: string): string {
  counter += 1;
  return `${prefix}_${counter.toString(36)}_${Date.now().toString(36)}`;
}
