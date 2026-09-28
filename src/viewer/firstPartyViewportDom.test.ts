import { describe, expect, it } from 'vitest';
import { characterStore } from '../editor/characterStoreCore';
import { skeleton, studioStore } from '../editor/storeCore';
import type { FirstPartyViewportRuntime } from './firstPartyViewportRuntime';
import type { SceneHostBindings } from './sceneHostTypes';
import type { SceneState } from './sceneStateCore';
import type {
  StudioSceneController,
  StudioSceneControllerOptions,
} from './studioSceneController';
import {
  createFirstPartyViewportDom,
  type FirstPartyViewportDomDependencies,
} from './firstPartyViewportDom';

class FakeElement {
  readonly dataset: Record<string, string> = {};
  readonly style: Record<string, string> = {};
  readonly children: FakeElement[] = [];
  append(...nodes: FakeElement[]): void { this.children.push(...nodes); }
}

const fakeDocument = (): Pick<Document, 'createElement'> => ({
  createElement: (() => new FakeElement()) as unknown as Document['createElement'],
});

describe('first-party viewport DOM wrapper', () => {
  it('preserves the React host/canvas contract and runtime/controller wiring', () => {
    const order: string[] = [];
    const scene = {} as SceneState;
    const bindings = {} as SceneHostBindings;
    let runtimeArgs: unknown[] = [];
    let controllerOptions: StudioSceneControllerOptions | null = null;

    const runtime: FirstPartyViewportRuntime = {
      bindings,
      dispose() { order.push('runtime'); },
    };
    const controller: StudioSceneController = {
      dispose() { order.push('controller'); },
    };

    const dependencies: FirstPartyViewportDomDependencies = {
      createSceneState: () => scene,
      createRuntime: ((container, canvas, receivedScene) => {
        runtimeArgs = [container, canvas, receivedScene];
        return runtime;
      }) as FirstPartyViewportDomDependencies['createRuntime'],
      createController: ((options) => {
        controllerOptions = options;
        return controller;
      }) as FirstPartyViewportDomDependencies['createController'],
    };

    const viewport = createFirstPartyViewportDom(fakeDocument(), dependencies);
    const host = viewport.element as unknown as FakeElement;
    const canvas = viewport.canvas as unknown as FakeElement;

    expect(host.dataset.hgptSceneHost).toBe('first-party');
    expect(host.style).toEqual({
      width: '100%',
      height: '100%',
      minHeight: '0',
      position: 'relative',
    });
    expect(canvas.style).toEqual({
      display: 'block',
      width: '100%',
      height: '100%',
    });
    expect(host.children).toEqual([canvas]);
    expect(runtimeArgs).toEqual([viewport.element, viewport.canvas, scene]);
    expect(controllerOptions).toMatchObject({
      sceneState: scene,
      bindings,
      studioStore,
      characterStore,
      skeleton,
    });

    viewport.dispose();
    viewport.dispose();
    expect(order).toEqual(['controller', 'runtime']);
  });
});
