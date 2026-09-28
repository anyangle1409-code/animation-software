import { beforeEach, describe, expect, it } from 'vitest';
import { studioLayoutStore } from '../layoutState';
import {
  createReviewPanelMount,
  type ReviewPanelSurface,
} from './reviewPanelMount';

class FakeElement {
  readonly children: FakeElement[] = [];
  parentElement: FakeElement | null = null;

  append(...nodes: FakeElement[]): void {
    for (const node of nodes) {
      node.parentElement = this;
      this.children.push(node);
    }
  }

  remove(): void {
    if (!this.parentElement) return;
    const index = this.parentElement.children.indexOf(this);
    if (index >= 0) this.parentElement.children.splice(index, 1);
    this.parentElement = null;
  }
}

beforeEach(() => {
  studioLayoutStore.setState({ rightTab: 'exercise' });
});

describe('Review panel mount lifecycle', () => {
  it('exists only while Review is active and disposes on right-tab changes', () => {
    const slot = new FakeElement() as unknown as HTMLElement;
    let created = 0;
    let disposed = 0;

    const mount = createReviewPanelMount(
      slot,
      () => {
        created += 1;
        const surface: ReviewPanelSurface = {
          element: new FakeElement() as unknown as HTMLElement,
          dispose() { disposed += 1; },
        };
        return surface;
      },
      studioLayoutStore,
    );

    expect(created).toBe(0);
    studioLayoutStore.getState().setRightTab('review');
    expect(created).toBe(1);
    expect((slot as unknown as FakeElement).children).toHaveLength(1);

    studioLayoutStore.getState().setRightTab('export');
    expect(disposed).toBe(1);
    expect((slot as unknown as FakeElement).children).toHaveLength(0);

    studioLayoutStore.getState().setRightTab('review');
    expect(created).toBe(2);

    mount.dispose();
    expect(disposed).toBe(2);
    expect((slot as unknown as FakeElement).children).toHaveLength(0);

    studioLayoutStore.getState().setRightTab('review');
    expect(created).toBe(2);
  });
});
