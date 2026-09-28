export interface HgSceneStopEvent {
  stopPropagation(): void;
}

export interface HgSceneRayEvent extends HgSceneStopEvent {
  readonly pointerId: number;
  readonly ray: {
    readonly origin: { x: number; y: number; z: number };
    readonly direction: { x: number; y: number; z: number };
  };
  readonly target: EventTarget | null;
}
