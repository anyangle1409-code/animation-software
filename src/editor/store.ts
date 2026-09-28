import { bindReactStore } from '../core/store';
import { studioStore } from './storeCore';

export * from './storeCore';

/** Temporary React hook adapter over the framework-neutral Studio store. */
export const useStudio = bindReactStore(studioStore);
