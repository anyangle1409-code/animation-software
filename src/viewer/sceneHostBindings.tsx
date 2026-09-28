import { createContext, useContext } from 'react';
import type { ReactNode } from 'react';
import type { Camera, Scene } from 'three';

export interface SceneHostBindings {
  camera: Camera;
  scene: Scene;
  element: HTMLCanvasElement;
}

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
