import { createContext, useContext } from 'react';
import type { ReactNode } from 'react';
import type { SceneHostBindings } from './sceneHostTypes';

export type { SceneHostBindings } from './sceneHostTypes';

const SceneHostBindingsContext = createContext<SceneHostBindings | null>(null);

export function SceneHostBindingsProvider({
  value,
  children,
}: {
  value: SceneHostBindings;
  children: ReactNode;
}) {
  return (
    <SceneHostBindingsContext.Provider value={value}>
      {children}
    </SceneHostBindingsContext.Provider>
  );
}

export function useSceneHostBindings(): SceneHostBindings {
  const value = useContext(SceneHostBindingsContext);
  if (!value) throw new Error('useSceneHostBindings must be used inside a scene host');
  return value;
}
