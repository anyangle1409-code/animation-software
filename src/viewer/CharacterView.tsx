import { useCharacter } from '../editor/characterStore';

/**
 * An imported character, driven by the same pose the mannequin uses. The
 * animation is not re-authored for it — it is retargeted every frame, which is
 * the whole point of keeping animation data independent of the visible model.
 */
export function CharacterView() {
  const character = useCharacter((state) => state.character);

  if (!character) return null;
  return <primitive object={character.root} />;
}
