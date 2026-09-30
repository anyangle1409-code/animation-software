import type { Skeleton } from '../rig/skeleton';
import { retargetedCharacterSource } from './retargetSource';
import type { ImportReport, RetargetedCharacterSource } from './retargetSource';

export const ORIGINAL_V1_BUNDLED_PATHS = {
  bare: 'characters/HomeGymPT_Male_ORIGINAL_v1.glb',
  dressed: 'characters/HomeGymPT_Male_ORIGINAL_v1_DRESSED.glb',
} as const;

export type OriginalV1BundledVariant = keyof typeof ORIGINAL_V1_BUNDLED_PATHS;

const labels: Record<OriginalV1BundledVariant, string> = {
  bare: 'Home Gym PT ORIGINAL v1',
  dressed: 'Home Gym PT ORIGINAL v1 — dressed',
};

const ids: Record<OriginalV1BundledVariant, string> = {
  bare: 'original-v1',
  dressed: 'original-v1-dressed',
};

function bundledPath(variant: OriginalV1BundledVariant): string {
  const path = ORIGINAL_V1_BUNDLED_PATHS[variant];
  if (!path) {
    throw new Error(`Unsupported ORIGINAL v1 bundled variant "${String(variant)}".`);
  }
  return path;
}

function validateGlbContainer(data: ArrayBuffer, label: string): void {
  if (data.byteLength < 20) {
    throw new Error(`${label} is too small to be a GLB 2.0 file.`);
  }

  const bytes = new Uint8Array(data);
  if (
    bytes[0] !== 0x67 ||
    bytes[1] !== 0x6c ||
    bytes[2] !== 0x54 ||
    bytes[3] !== 0x46
  ) {
    throw new Error(`${label} does not have GLB magic "glTF".`);
  }

  const view = new DataView(data);
  const version = view.getUint32(4, true);
  const declaredLength = view.getUint32(8, true);
  if (version !== 2) {
    throw new Error(`${label} is GLB version ${version}; production requires GLB 2.0.`);
  }
  if (declaredLength !== data.byteLength) {
    throw new Error(
      `${label} declares ${declaredLength} bytes but loaded ${data.byteLength} bytes.`,
    );
  }
}

/**
 * Read one exact, product-relative ORIGINAL v1 production asset.
 *
 * This is deliberately narrower than a generic URL loader:
 * - only the two production paths frozen in ORIGINAL_V1_PROMOTION_CONTRACT.json
 *   can be requested;
 * - no caller-supplied URL reaches fetch();
 * - a remote host, absolute path, candidate file or arbitrary local asset
 *   therefore cannot enter this path;
 * - the fetched bytes must at least be a well-formed GLB 2.0 container before
 *   the character parser sees them.
 *
 * The file is intentionally not imported by the live registry while promotion
 * mode is blocked. It is the prepared offline cutover seam, not an activation.
 */
export async function loadBundledOriginalV1Bytes(
  variant: OriginalV1BundledVariant,
): Promise<ArrayBuffer> {
  const url = bundledPath(variant);
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(
      `Unable to load bundled ORIGINAL v1 ${variant} asset "${url}": HTTP ${response.status}.`,
    );
  }

  const data = await response.arrayBuffer();
  validateGlbContainer(data, `Bundled ORIGINAL v1 ${variant}`);
  return data;
}

/**
 * Production-source wrapper that preserves the GLB's authored skeleton, bind
 * matrices and skin weights through the existing first-party preserved
 * character path.
 *
 * It remains dormant until the promotion contract is explicitly approved and
 * the registry/default-character cutover is made in a separate reviewed step.
 */
export function bundledOriginalV1Source(
  variant: OriginalV1BundledVariant = 'dressed',
): RetargetedCharacterSource {
  const id = ids[variant];
  const label = labels[variant];
  const note =
    'Project-authored ORIGINAL v1 production asset loaded only from the exact packaged release path.';

  const source: RetargetedCharacterSource = {
    id,
    label,
    note,
    capabilities: { anatomy: false, textured: true },
    lastReport: null as ImportReport | null,

    async build(rig: Skeleton) {
      const data = await loadBundledOriginalV1Bytes(variant);
      const preserved = retargetedCharacterSource({
        id,
        label,
        note,
        data,
      });
      const build = await preserved.build(rig);
      source.lastReport = preserved.lastReport;
      return build;
    },
  };

  return source;
}
