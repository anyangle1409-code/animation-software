import { useFrame } from '@react-three/fiber';
import { useCharacter } from '../editor/characterStore';
import { applyRetarget } from '../retargeting/retarget';
import { useSceneState } from './sceneState';

/**
 * An imported character, driven by the same pose the mannequin uses. The
 * animation is not re-authored for it — it is retargeted every frame, which is
 * the whole point of keeping animation data independent of the visible model.
 */
export function CharacterView() {
  const scene = useSceneState();
  const character = useCharacter((state) => state.character);
  const binding = useCharacter((state) => state.binding);

  useFrame(() => {
    if (!binding || !scene.frame) return;
    applyRetarget(binding, scene.frame.pose);
  });

  if (!character) return null;
  return <primitive object={character.root} />;
}
