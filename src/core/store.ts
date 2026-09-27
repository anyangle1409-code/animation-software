import { useRef, useSyncExternalStore } from 'react';

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
    const select = selector ?? ((value: T) => value as unknown as U);

    // React requires getSnapshot to return the same identity while the store
    // state is unchanged. Cache selector output per hook instance so selectors
    // that construct a small object/array do not create a render loop.
    const cache = useRef<{
      state: T | undefined;
      selector: ((state: T) => U) | undefined;
      value: U | undefined;
      ready: boolean;
    }>({ state: undefined, selector: undefined, value: undefined, ready: false });

    const snapshot = (): U => {
      const current = get();
      if (
        cache.current.ready &&
        cache.current.state === current &&
        cache.current.selector === select
      ) {
        return cache.current.value as U;
      }
      const value = select(current);
      cache.current = { state: current, selector: select, value, ready: true };
      return value;
    };

    return useSyncExternalStore(subscribe, snapshot, snapshot);
  }

  const hook = useStore as StoreHook<T>;
  hook.getState = get;
  hook.setState = set;
  hook.subscribe = subscribe;
  return hook;
}
