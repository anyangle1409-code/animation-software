export type ViewportHostKind = 'r3f' | 'first-party';

/** Parse the reversible viewport-host selector without coupling it to React. */
export function viewportHostFromSearch(search: string): ViewportHostKind {
  const value = new URLSearchParams(search).get('sceneHost');
  return value === 'r3f' ? 'r3f' : 'first-party';
}
