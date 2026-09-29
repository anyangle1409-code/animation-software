import { IK_CHAIN_IDS } from '../ik/chains';
import type { IKChainId } from '../ik/types';
import type { IKHandleKind } from './ikHandleScene';

export const HG_IK_HANDLE_COLOURS = {
  target: '#4fd6a0',
  pole: '#6aa9ff',
  selected: '#ffb43a',
  emissiveOff: '#000000',
} as const;

export interface HgIKHandleVisual {
  readonly chain: IKChainId;
  readonly kind: IKHandleKind;
  readonly key: string;
  readonly geometry:
    | { readonly kind: 'box'; readonly size: readonly [number, number, number] }
    | { readonly kind: 'octahedron'; readonly radius: number };
  readonly material: {
    readonly colour: string;
    readonly transparent: boolean;
    readonly opacity: number;
    readonly depthTest: boolean;
  };
}

export interface HgIKHandleAppearance {
  readonly colour: string;
  readonly emissive: string;
  readonly emissiveIntensity: number;
}

export const hgIKHandleKey = (chain: IKChainId, kind: IKHandleKind): string =>
  `${chain}:${kind}`;

/** Renderer-neutral IK handle geometry/material configuration. */
export function buildHgIKHandleSceneModel(): HgIKHandleVisual[] {
  const out: HgIKHandleVisual[] = [];
  for (const chain of IK_CHAIN_IDS) {
    out.push({
      chain,
      kind: 'target',
      key: hgIKHandleKey(chain, 'target'),
      geometry: { kind: 'box', size: [0.045, 0.045, 0.045] },
      material: {
        colour: HG_IK_HANDLE_COLOURS.target,
        transparent: true,
        opacity: 0.9,
        depthTest: false,
      },
    });
    out.push({
      chain,
      kind: 'pole',
      key: hgIKHandleKey(chain, 'pole'),
      geometry: { kind: 'octahedron', radius: 0.032 },
      material: {
        colour: HG_IK_HANDLE_COLOURS.pole,
        transparent: true,
        opacity: 0.9,
        depthTest: false,
      },
    });
  }
  return out;
}

export function resolveHgIKHandleAppearance(
  chain: IKChainId,
  kind: IKHandleKind,
  selection: { chain: IKChainId; kind: IKHandleKind } | null,
): HgIKHandleAppearance {
  const selected = selection?.chain === chain && selection.kind === kind;
  const colour = selected
    ? HG_IK_HANDLE_COLOURS.selected
    : kind === 'target'
      ? HG_IK_HANDLE_COLOURS.target
      : HG_IK_HANDLE_COLOURS.pole;
  return {
    colour,
    emissive: selected ? HG_IK_HANDLE_COLOURS.selected : HG_IK_HANDLE_COLOURS.emissiveOff,
    emissiveIntensity: selected ? 0.5 : 0,
  };
}
