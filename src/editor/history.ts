/** Undo/redo over immutable document snapshots. */
export interface History<T> {
  past: T[];
  future: T[];
  limit: number;
}

export const emptyHistory = <T,>(limit = 100): History<T> => ({ past: [], future: [], limit });

export function pushHistory<T>(history: History<T>, previous: T): History<T> {
  const past = [...history.past, previous];
  return {
    past: past.length > history.limit ? past.slice(past.length - history.limit) : past,
    future: [],
    limit: history.limit,
  };
}

export function undo<T>(history: History<T>, current: T): { history: History<T>; value: T } | null {
  const previous = history.past.at(-1);
  if (previous === undefined) return null;
  return {
    history: {
      past: history.past.slice(0, -1),
      future: [current, ...history.future],
      limit: history.limit,
    },
    value: previous,
  };
}

export function redo<T>(history: History<T>, current: T): { history: History<T>; value: T } | null {
  const next = history.future[0];
  if (next === undefined) return null;
  return {
    history: {
      past: [...history.past, current],
      future: history.future.slice(1),
      limit: history.limit,
    },
    value: next,
  };
}
