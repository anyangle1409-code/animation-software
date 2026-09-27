export interface HgOrbitInputDelta {
  rotateX?: number;
  rotateY?: number;
  zoomFactor?: number;
}

interface PointerPosition {
  x: number;
  y: number;
}

const distance = (one: PointerPosition, two: PointerPosition) =>
  Math.hypot(two.x - one.x, two.y - one.y);

/** Renderer-neutral pointer tracking for mouse and mobile orbit gestures. */
export class HgOrbitPointerTracker {
  private readonly pointers = new Map<number, PointerPosition>();

  pointerDown(id: number, x: number, y: number): void {
    this.pointers.set(id, { x, y });
  }

  pointerMove(id: number, x: number, y: number): HgOrbitInputDelta | null {
    const previous = this.pointers.get(id);
    if (!previous) return null;

    if (this.pointers.size === 1) {
      this.pointers.set(id, { x, y });
      return { rotateX: x - previous.x, rotateY: y - previous.y };
    }

    const pairBefore = [...this.pointers.values()].slice(0, 2);
    const previousDistance = distance(pairBefore[0], pairBefore[1]);
    this.pointers.set(id, { x, y });
    const pairAfter = [...this.pointers.values()].slice(0, 2);
    const currentDistance = distance(pairAfter[0], pairAfter[1]);

    if (previousDistance <= 1e-6 || currentDistance <= 1e-6) return null;
    return { zoomFactor: previousDistance / currentDistance };
  }

  pointerUp(id: number): void {
    this.pointers.delete(id);
  }

  clear(): void {
    this.pointers.clear();
  }
}

/** Match wheel deltas to a stable multiplicative zoom independent of units. */
export function wheelZoomFactor(deltaY: number): number {
  if (!Number.isFinite(deltaY)) return 1;
  const bounded = Math.max(-500, Math.min(500, deltaY));
  return Math.exp(bounded * 0.0015);
}
