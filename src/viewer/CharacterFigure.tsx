import { useEffect } from 'react';
import { skeleton, studioStore } from '../editor/store';
import { useCharacter } from '../editor/characterStore';
import type { CharacterVariant } from '../character';
import { useSceneState } from './sceneState';
import { useSceneHostBindings } from './sceneHostBindings';
import { createCharacterViewRuntime } from './characterViewRuntime';

export interface CharacterFigureProps {
  opacity?: number;
  /** Multiplies the body's own vertex colours; white leaves them as authored. */
  colour?: string;
  /** A ghosted body must not write depth or it hides the muscle layer. */
  depthWrite?: boolean;
  variant?: CharacterVariant;
}

/** Temporary React adapter over the framework-neutral character runtime. */
export function CharacterFigure({
  opacity = 1,
  colour = '#ffffff',
  depthWrite = true,
  variant = 'skin',
}: CharacterFigureProps) {
  const sceneState = useSceneState();
  const { scene: root } = useSceneHostBindings();

  useEffect(() => {
    const runtime = createCharacterViewRuntime({
      sceneState,
      root,
      studioStore,
      characterStore: useCharacter,
      skeleton,
      opacity,
      colour,
      depthWrite,
      variant,
    });
    return () => runtime.dispose();
  }, [sceneState, root, opacity, colour, depthWrite, variant]);

  return null;
}
