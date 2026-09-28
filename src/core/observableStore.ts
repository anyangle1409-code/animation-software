export type StoreSet<T> = (
  update: Partial<T> | ((state: T) => Partial<T>),
) => void;

export type StoreGet<T> = () => T;
export type StoreListener = () => void;

export interface ObservableStore<T> {
  getState(): T;
  setState(update: Partial<T> | ((state: T) => Partial<T>)): void;
  subscribe(listener: StoreListener): () => void;
}

/**
 * Framework-neutral first-party observable store.
 *
 * This is the durable state primitive for the Studio. React, DOM or any future
 * UI layer may subscribe to it without changing state semantics.
 */
export function createStore<T>(
  initialise: (set: StoreSet<T>, get: StoreGet<T>) => T,
): ObservableStore<T> {
  let state!: T;
  const listeners = new Set<StoreListener>();

  const get: StoreGet<T> = () => state;

  const set: StoreSet<T> = (update) => {
    const patch = typeof update === 'function' ? update(state) : update;
    if (!patch || typeof patch !== 'object') return;

    state = Object.assign({}, state, patch);
    for (const listener of [...listeners]) listener();
  };

  const subscribe = (listener: StoreListener): (() => void) => {
    listeners.add(listener);
    return () => listeners.delete(listener);
  };

  state = initialise(set, get);
  return {
    getState: get,
    setState: set,
    subscribe,
  };
}
