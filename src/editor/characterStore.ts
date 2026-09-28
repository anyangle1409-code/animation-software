import { bindReactStore } from '../core/store';
import { characterStore } from './characterStoreCore';

export * from './characterStoreCore';

/** Temporary React hook adapter over the framework-neutral character store. */
export const useCharacter = bindReactStore(characterStore);
