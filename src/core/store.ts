import { useSyncExternalStore } from 'react';
import {
  createStore,
  type ObservableStore,
  type StoreGet,
  type StoreListener,
  type StoreSet,
} from './observableStore';

export type { ObservableStore, StoreGet, StoreListener, StoreSet } from './observableStore';

export interface StoreHook<T> extends ObservableStore<T> {
  (): T;
  <U>(selector: (state: T) => U): U;
}

/**
 * Temporary React adapter over the framework-neutral observable store.
 *
 * React may be removed without changing the store itself or any non-React
 * caller that uses getState/setState/subscribe.
 */
export function bindReactStore<T>(store: ObservableStore<T>): StoreHook<T> {
  function useStore(): T;
  function useStore<U>(selector: (state: T) => U): U;
  function useStore<U>(selector?: (state: T) => U): T | U {
    const current = useSyncExternalStore(store.subscribe, store.getState, store.getState);
    return selector ? selector(current) : current;
  }

  const hook = useStore as StoreHook<T>;
  hook.getState = store.getState;
  hook.setState = store.setState;
  hook.subscribe = store.subscribe;
  return hook;
}

/** Compatibility helper while React components still consume hook-shaped stores. */
export function createStoreHook<T>(
  initialise: (set: StoreSet<T>, get: StoreGet<T>) => T,
): StoreHook<T> {
  return bindReactStore(createStore(initialise));
}
