import { describe, expect, it, vi } from 'vitest';
import { createStore } from './observableStore';

interface CounterState {
  count: number;
  label: string;
  increment: () => void;
}

describe('framework-neutral first-party store', () => {
  it('supports synchronous get/set and functional updates without React', () => {
    const store = createStore<CounterState>((set, get) => ({
      count: 1,
      label: 'one',
      increment: () => set({ count: get().count + 1 }),
    }));

    expect(store.getState().count).toBe(1);
    store.getState().increment();
    expect(store.getState().count).toBe(2);

    store.setState((state) => ({ label: String(state.count) }));
    expect(store.getState().label).toBe('2');
  });

  it('notifies subscribers once per update and unsubscribes cleanly', () => {
    const store = createStore(() => ({ count: 0 }));
    const listener = vi.fn();
    const unsubscribe = store.subscribe(listener);

    store.setState({ count: 1 });
    expect(listener).toHaveBeenCalledTimes(1);

    unsubscribe();
    store.setState({ count: 2 });
    expect(listener).toHaveBeenCalledTimes(1);
  });
});
