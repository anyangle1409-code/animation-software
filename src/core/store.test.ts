import { describe, expect, it, vi } from 'vitest';
import { createStoreHook } from './store';

interface CounterState {
  count: number;
  label: string;
  increment: () => void;
}

describe('first-party store core', () => {
  it('supports synchronous get/set and functional updates', () => {
    const useCounter = createStoreHook<CounterState>((set, get) => ({
      count: 1,
      label: 'one',
      increment: () => set({ count: get().count + 1 }),
    }));

    expect(useCounter.getState().count).toBe(1);
    useCounter.getState().increment();
    expect(useCounter.getState().count).toBe(2);

    useCounter.setState((state) => ({ label: String(state.count) }));
    expect(useCounter.getState().label).toBe('2');
  });

  it('notifies subscribers once per update and unsubscribes cleanly', () => {
    const useCounter = createStoreHook(() => ({ count: 0 }));
    const listener = vi.fn();
    const unsubscribe = useCounter.subscribe(listener);

    useCounter.setState({ count: 1 });
    expect(listener).toHaveBeenCalledTimes(1);

    unsubscribe();
    useCounter.setState({ count: 2 });
    expect(listener).toHaveBeenCalledTimes(1);
  });
});
