import {
  Raycaster,
  Vector2,
  type Camera,
  type Object3D,
  type Scene,
} from 'three';
import type { HgSceneRayEvent } from './scenePointerTypes';

export type HgScenePointerKind = 'pointerdown' | 'pointermove' | 'pointerup' | 'pointercancel';

export interface HgScenePointerHandlers {
  pointerdown?: (event: HgSceneRayEvent) => void;
  pointermove?: (event: HgSceneRayEvent) => void;
  pointerup?: (event: HgSceneRayEvent) => void;
  pointercancel?: (event: HgSceneRayEvent) => void;
}

export interface HgScenePointerInput {
  pointerId: number;
  clientX: number;
  clientY: number;
  target: EventTarget | null;
}

export interface HgPointerSurface extends EventTarget {
  getBoundingClientRect(): Pick<DOMRect, 'left' | 'top' | 'width' | 'height'>;
  setPointerCapture?(pointerId: number): void;
  releasePointerCapture?(pointerId: number): void;
  hasPointerCapture?(pointerId: number): boolean;
}

function visibleThroughScene(object: Object3D, scene: Scene): boolean {
  let current: Object3D | null = object;
  while (current) {
    if (!current.visible) return false;
    if (current === scene) return true;
    current = current.parent;
  }
  return false;
}

/**
 * First-party DOM/raycast router for interactive scene objects.
 *
 * Targets register directly by Object3D. The nearest registered ancestor of
 * the nearest visible ray hit receives the event, then handlers bubble through
 * registered ancestors until stopPropagation is called. Pointer capture is
 * remembered after pointerdown so drag move/up events keep their original
 * scene target even when the ray leaves its geometry.
 */
export class HgScenePointerRouter {
  private readonly raycaster = new Raycaster();
  private readonly ndc = new Vector2();
  private readonly targets = new Map<Object3D, HgScenePointerHandlers>();
  private readonly captured = new Map<number, Object3D>();
  private mounted = false;

  constructor(
    private readonly camera: Camera,
    private readonly scene: Scene,
    private readonly element: HgPointerSurface,
    private readonly onMiss?: (input: HgScenePointerInput) => void,
  ) {}

  register(object: Object3D, handlers: HgScenePointerHandlers): () => void {
    this.targets.set(object, handlers);
    return () => {
      this.targets.delete(object);
      for (const [pointerId, captured] of this.captured) {
        if (captured === object || isDescendantOf(captured, object)) {
          this.element.releasePointerCapture?.(pointerId);
          this.captured.delete(pointerId);
        }
      }
    };
  }

  mount(): void {
    if (this.mounted) return;
    this.mounted = true;
    this.element.addEventListener('pointerdown', this.pointerDown as EventListener);
    this.element.addEventListener('pointermove', this.pointerMove as EventListener);
    this.element.addEventListener('pointerup', this.pointerUp as EventListener);
    this.element.addEventListener('pointercancel', this.pointerCancel as EventListener);
  }

  dispose(): void {
    if (this.mounted) {
      this.element.removeEventListener('pointerdown', this.pointerDown as EventListener);
      this.element.removeEventListener('pointermove', this.pointerMove as EventListener);
      this.element.removeEventListener('pointerup', this.pointerUp as EventListener);
      this.element.removeEventListener('pointercancel', this.pointerCancel as EventListener);
    }
    this.mounted = false;
    this.targets.clear();
    for (const pointerId of this.captured.keys()) {
      this.element.releasePointerCapture?.(pointerId);
    }
    this.captured.clear();
  }

  dispatch(kind: HgScenePointerKind, input: HgScenePointerInput): boolean {
    if (!this.updateRay(input.clientX, input.clientY)) return false;
    const captured = this.captured.get(input.pointerId);
    const target = captured ?? this.pickCurrentRay();

    if (!target) {
      if (kind === 'pointerdown') this.onMiss?.(input);
      if (kind === 'pointerup' || kind === 'pointercancel') this.captured.delete(input.pointerId);
      return false;
    }

    let stopped = false;
    const event: HgSceneRayEvent = {
      pointerId: input.pointerId,
      ray: {
        origin: {
          x: this.raycaster.ray.origin.x,
          y: this.raycaster.ray.origin.y,
          z: this.raycaster.ray.origin.z,
        },
        direction: {
          x: this.raycaster.ray.direction.x,
          y: this.raycaster.ray.direction.y,
          z: this.raycaster.ray.direction.z,
        },
      },
      target: input.target,
      stopPropagation() {
        stopped = true;
      },
    };

    let current: Object3D | null = target;
    while (current) {
      this.targets.get(current)?.[kind]?.(event);
      if (stopped || current === this.scene) break;
      current = current.parent;
    }

    if (
      kind === 'pointerdown' &&
      this.element.hasPointerCapture?.(input.pointerId)
    ) {
      this.captured.set(input.pointerId, target);
    }
    if (kind === 'pointerup' || kind === 'pointercancel') {
      this.captured.delete(input.pointerId);
    }
    return true;
  }

  private updateRay(clientX: number, clientY: number): boolean {
    const bounds = this.element.getBoundingClientRect();
    if (!(bounds.width > 0) || !(bounds.height > 0)) return false;

    this.ndc.set(
      ((clientX - bounds.left) / bounds.width) * 2 - 1,
      -((clientY - bounds.top) / bounds.height) * 2 + 1,
    );
    this.camera.updateMatrixWorld();
    this.scene.updateMatrixWorld(true);
    this.raycaster.setFromCamera(this.ndc, this.camera);
    return true;
  }

  private pickCurrentRay(): Object3D | null {
    for (const hit of this.raycaster.intersectObjects(this.scene.children, true)) {
      if (!visibleThroughScene(hit.object, this.scene)) continue;
      let current: Object3D | null = hit.object;
      while (current) {
        if (this.targets.has(current)) return current;
        if (current === this.scene) break;
        current = current.parent;
      }
    }
    return null;
  }

  private readonly pointerDown = (event: PointerEvent) => {
    this.dispatch('pointerdown', event);
  };

  private readonly pointerMove = (event: PointerEvent) => {
    this.dispatch('pointermove', event);
  };

  private readonly pointerUp = (event: PointerEvent) => {
    this.dispatch('pointerup', event);
  };

  private readonly pointerCancel = (event: PointerEvent) => {
    this.dispatch('pointercancel', event);
  };
}

function isDescendantOf(object: Object3D, ancestor: Object3D): boolean {
  let current: Object3D | null = object;
  while (current) {
    if (current === ancestor) return true;
    current = current.parent;
  }
  return false;
}
