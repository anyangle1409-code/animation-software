import { bindReactStore } from '../core/store';
import { generationStore } from './generationStoreCore';

export * from './generationStoreCore';

/** Temporary React adapter over the framework-neutral generation session store. */
export const useGeneration = bindReactStore(generationStore);
