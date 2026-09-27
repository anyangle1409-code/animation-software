import { useSyncExternalStore } from 'react';

export type StoreSet<T> = (
  update: Partial<T> | ((state: T) => Partial<T>),
) => void;

export type StoreGet<T> = () => T;
export type StoreListener = () => void;

export interface StoreHook<T> {
  (): T;
  <U>(selector: (state: T) => U): U;
  getState(): T;
  setState(update: Partial<T> | ((state: T) => Partial<T>)): void;
  subscribe(listener: StoreListener): () => void;
}

/**
 * Minimal project-owned observable store.
 *
 * This intentionally implements only the state semantics Home Gym PT uses:
 * synchronous get/set, shallow object updates, subscriptions, and a React
 * selector hook. React is temporary here; when the UI moves off React this
 * store remains usable through getState/subscribe without changing the state
 * model again.
 */
export function createStoreHook<T>(
  initialise: (set: StoreSet<T>, get: StoreGet<T>) => T,
): StoreHook<T> {
  let state!: T;
  const listeners = new Set<StoreListener>();

  const get: StoreGet<T> = () => state;

  const set: StoreSet<T> = (update) => {
    const patch = typeof update === 'function' ? update(state) : update;
    if (!patch || typeof patch !== 'object') return;

    const next = Object.assign({}, state, patch);
    if (Object.is(next, state)) return;
    state = next;

    for (const listener of [...listeners]) listener();
  };

  const subscribe = (listener: StoreListener): (() => void) => {
    listeners.add(listener);
    return () => listeners.delete(listener);
  };

  state = initialise(set, get);

  function useStore(): T;
  function useStore<U>(selector: (state: T) => U): U;
  function useStore<U>(selector?: (state: T) => U): T | U {
    // Subscribe to the whole state object. It is replaced on every set(), so
    // React receives a stable snapshot until the store actually changes.
    //
    // Applying the selector *after* useSyncExternalStore is deliberate:
    // selectors in the editor are commonly inline functions. Caching a selected
    // object against selector identity can make getSnapshot unstable across
    // renders even when the store has not changed. Whole-state subscription is
    // a little less selective, but it is deterministic and preserves semantics
    // for selectors that close over current component values.
    const current = useSyncExternalStore(subscribe, get, get);
    return selector ? selector(current) : current;
  }

  const hook = useStore as StoreHook<T>;
  hook.getState = get;
  hook.setState = set;
  hook.subscribe = subscribe;
  return hook;
}
