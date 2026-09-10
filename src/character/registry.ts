import { builtinCharacter, proceduralCharacter } from './builtin';
import { glbCharacterSource } from './glbSource';
import type { GlbCharacterOptions } from './glbSource';
import type { CharacterSource } from './types';

/**
 * The character registry.
 *
 * Sources register themselves here and the rest of the app asks for one by id.
 * Nothing outside this module imports a mesh builder, which is what makes the
 * visible character replaceable: a new source is one registration, and the
 * viewport, the exporter and the panels pick it up without changing.
 */

const sources = new Map<string, CharacterSource>();
let fallback = builtinCharacter.id;

export function registerCharacterSource<T extends CharacterSource>(source: T): T {
  sources.set(source.id, source);
  return source;
}

export function unregisterCharacterSource(id: string): void {
  sources.delete(id);
  if (fallback === id) fallback = builtinCharacter.id;
}

/** Every registered source, presentation characters before diagnostic ones. */
export function characterSources(): CharacterSource[] {
  return [...sources.values()].sort(
    (one, two) => Number(one.diagnostic ?? false) - Number(two.diagnostic ?? false),
  );
}

/** A source by id, falling back to the default rather than failing to render. */
export function characterSource(id?: string | null): CharacterSource {
  return (id && sources.get(id)) || sources.get(fallback) || builtinCharacter;
}

export function defaultCharacterId(): string {
  return fallback;
}

/** Choose which source new sessions and the exporter use when none is named. */
export function setDefaultCharacter(id: string): void {
  if (sources.has(id)) fallback = id;
}

registerCharacterSource(builtinCharacter);
registerCharacterSource(proceduralCharacter);

/**
 * Register a GLB shipped with the app and make it the default.
 *
 * This is the whole of the work needed to put a higher-quality character in
 * front of the existing animation: drop the file in `public/characters/`, call
 * this once at startup, and the studio, the anatomy fallback and the exporter
 * all follow. Nothing is registered yet — there is no asset to register.
 */
export function registerBundledCharacter(options: GlbCharacterOptions): CharacterSource {
  const source = registerCharacterSource(glbCharacterSource(options));
  setDefaultCharacter(source.id);
  return source;
}
