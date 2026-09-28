import { useEffect } from 'react';
import { studioStore } from '../editor/store';
import { useCharacter } from '../editor/characterStore';
import { useSceneState } from './sceneState';
import { useSceneHostBindings } from './sceneHostBindings';
import { createEquipmentViewRuntime } from './equipmentViewRuntime';

/** Temporary React adapter over the framework-neutral equipment runtime. */
export function EquipmentView() {
  const sceneState = useSceneState();
  const { scene: root, pointers } = useSceneHostBindings();

  useEffect(() => {
    const runtime = createEquipmentViewRuntime({
      sceneState,
      root,
      pointers,
      store: studioStore,
      characterStore: useCharacter,
    });
    return () => runtime.dispose();
  }, [sceneState, root, pointers]);

  return null;
}
