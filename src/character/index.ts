export type {
  CharacterBuild,
  CharacterBuildOptions,
  CharacterCapabilities,
  CharacterSource,
  CharacterVariant,
  DeformationContext,
  DeformationSampler,
  DeformationStack,
} from './types';
export { assembleCharacter } from './build';
export { buildCanonicalBones } from './bones';
export { builtinCharacter, proceduralCharacter } from './builtin';
export { glbCharacterSource } from './glbSource';
export type { GlbCharacterOptions, GlbCharacterSource } from './glbSource';
export { rebindToCanonical } from './rebind';
export type { RebindReport } from './rebind';
export {
  characterSource,
  characterSources,
  defaultCharacterId,
  registerBundledCharacter,
  registerCharacterSource,
  setDefaultCharacter,
  unregisterCharacterSource,
} from './registry';
export { applyCharacterPose } from './pose';
