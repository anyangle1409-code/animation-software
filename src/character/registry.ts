import { proceduralCharacter } from './procedural';
import type { CharacterSource } from './types';

/**
 * The character registry.
 *
 * The active built-in fallback is the clean project-authored procedural
 * scaffold. The legacy anatomical/MakeHuman-derived character is intentionally
 * not registered on the standalone branch.
 */
const sources = new Map<string, CharacterSource>();
let fallback = proceduralCharacter.id;

export function registerCharacterSource<T extends CharacterSource>(source: T): T {
  sources.set(source.id, source);
  return source;
}

export function unregisterCharacterSource(id: string): void {
  sources.delete(id);
  if (fallback === id) fallback = proceduralCharacter.id;
}

/** Every registered source, presentation characters before diagnostic ones. */
export function characterSources(): CharacterSource[] {
  return [...sources.values()].sort(
    (one, two) => Number(one.diagnostic ?? false) - Number(two.diagnostic ?? false),
  );
}

/** A source by id, falling back to the clean first-party scaffold. */
export function characterSource(id?: string | null): CharacterSource {
  return (id && sources.get(id)) || sources.get(fallback) || proceduralCharacter;
}

export function defaultCharacterId(): string {
  return fallback;
}

/** Choose which source new sessions and the exporter use when none is named. */
export function setDefaultCharacter(id: string): void {
  if (sources.has(id)) fallback = id;
}

registerCharacterSource(proceduralCharacter);
