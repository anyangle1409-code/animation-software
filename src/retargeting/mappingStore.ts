import type { BoneMapping } from './boneMap';

const STORAGE_KEY = 'hgpt-studio-bone-mappings';

/** Persist a reviewed mapping without coupling mapping storage to any GLB loader. */
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
