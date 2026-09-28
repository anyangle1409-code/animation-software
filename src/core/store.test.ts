import { describe, expect, it, vi } from 'vitest';
import { createStore } from './observableStore';

interface CounterState {
  count: number;
  label: string;
  increment: () => void;
}

describe('first-party observable store', () => {
  it('supports synchronous get/set and functional updates', () => {
    const counter = createStore<CounterState>((set, get) => ({
      count: 1,
      label: 'one',
      increment: () => set({ count: get().count + 1 }),
    }));

    expect(counter.getState().count).toBe(1);
    counter.getState().increment();
    expect(counter.getState().count).toBe(2);

    counter.setState((state) => ({ label: String(state.count) }));
    expect(counter.getState().label).toBe('2');
  });

  it('notifies subscribers once per update and unsubscribes cleanly', () => {
    const counter = createStore(() => ({ count: 0 }));
    const listener = vi.fn();
    const unsubscribe = counter.subscribe(listener);

    counter.setState({ count: 1 });
    expect(listener).toHaveBeenCalledTimes(1);

    unsubscribe();
    counter.setState({ count: 2 });
    expect(listener).toHaveBeenCalledTimes(1);
  });
});
