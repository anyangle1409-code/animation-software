import { Object3D } from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { createMapping, guessMapping, reportMapping } from './boneMap';
import type { BoneMapping, MappingReport } from './boneMap';
import { readCharacter } from './retarget';
import type { TargetCharacter } from './retarget';

export interface ImportedCharacter {
  name: string;
  character: TargetCharacter;
  mapping: BoneMapping;
  report: MappingReport;
}

/**
 * Load a rigged GLB and propose a bone mapping for it.
 *
 * The mapping is a starting point, not an answer: the panel shows exactly which
 * canonical bones were matched and which were not, so a rig the guesser does
 * not recognise can be finished by hand and then reused for every exercise.
 */
export async function importCharacter(file: File): Promise<ImportedCharacter> {
  const buffer = await file.arrayBuffer();
  const loader = new GLTFLoader();
  const gltf = await loader.parseAsync(buffer, '');
  const root = gltf.scene as Object3D;
  root.name = file.name.replace(/\.(glb|gltf)$/i, '');

  const character = readCharacter(root);
  if (character.bones.size === 0) {
    throw new Error(
      `"${file.name}" has no skeleton. Export the character from Meshy or Blender with its rig included.`,
    );
  }

  const mapping = createMapping(root.name, `${root.name} (${character.bones.size} bones)`);
  mapping.bones = guessMapping(character.boneNames);
  mapping.characterHeight = character.height;

  return { name: root.name, character, mapping, report: reportMapping(mapping) };
}

const STORAGE_KEY = 'hgpt-studio-bone-mappings';

/** Mappings persist on their own, so one import serves every exercise. */
export function saveMapping(mapping: BoneMapping): void {
  const all = loadMappings().filter((entry) => entry.id !== mapping.id);
  all.push(mapping);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(all));
}

export function loadMappings(): BoneMapping[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as BoneMapping[]) : [];
  } catch {
    return [];
  }
}

export function deleteMapping(id: string): void {
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify(loadMappings().filter((entry) => entry.id !== id)),
  );
}
