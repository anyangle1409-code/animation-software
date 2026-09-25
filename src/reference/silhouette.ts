export interface SilhouetteBounds {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
  width: number;
  height: number;
}

export interface SilhouetteMetrics {
  width: number;
  height: number;
  foregroundPixels: number;
  areaRatio: number;
  bounds: SilhouetteBounds | null;
  centroid: { x: number; y: number } | null;
  touches: { left: boolean; right: boolean; top: boolean; bottom: boolean };
}

export interface SilhouetteSanity {
  passed: boolean;
  issues: string[];
}

/**
 * Analyse a black-background / white-foreground RGBA render.
 *
 * WebGL readRenderTargetPixels returns rows bottom-up. Returned metrics use
 * normal image coordinates: x=0 left, y=0 top, all normalized to [0,1].
 */
export function analyseSilhouetteRgba(
  rgba: Uint8Array,
  width: number,
  height: number,
  threshold = 127,
): SilhouetteMetrics {
  if (width <= 0 || height <= 0) throw new Error('Silhouette dimensions must be positive.');
  if (rgba.length !== width * height * 4) {
    throw new Error(`RGBA length ${rgba.length} does not match ${width}x${height}.`);
  }

  let count = 0;
  let minX = width;
  let maxX = -1;
  let minYTop = height;
  let maxYTop = -1;
  let sumX = 0;
  let sumYTop = 0;
  let left = false;
  let right = false;
  let top = false;
  let bottom = false;

  for (let yBottom = 0; yBottom < height; yBottom += 1) {
    const yTop = height - 1 - yBottom;
    for (let x = 0; x < width; x += 1) {
      const index = (yBottom * width + x) * 4;
      const alpha = rgba[index + 3];
      if (alpha <= threshold) continue;
      const luminance = (rgba[index] + rgba[index + 1] + rgba[index + 2]) / 3;
      if (luminance <= threshold) continue;

      count += 1;
      minX = Math.min(minX, x);
      maxX = Math.max(maxX, x);
      minYTop = Math.min(minYTop, yTop);
      maxYTop = Math.max(maxYTop, yTop);
      sumX += x + 0.5;
      sumYTop += yTop + 0.5;
      if (x === 0) left = true;
      if (x === width - 1) right = true;
      if (yTop === 0) top = true;
      if (yTop === height - 1) bottom = true;
    }
  }

  const bounds =
    count === 0
      ? null
      : {
          minX: minX / width,
          minY: minYTop / height,
          maxX: (maxX + 1) / width,
          maxY: (maxYTop + 1) / height,
          width: (maxX - minX + 1) / width,
          height: (maxYTop - minYTop + 1) / height,
        };

  return {
    width,
    height,
    foregroundPixels: count,
    areaRatio: count / (width * height),
    bounds,
    centroid:
      count === 0
        ? null
        : {
            x: sumX / count / width,
            y: sumYTop / count / height,
          },
    touches: { left, right, top, bottom },
  };
}

/**
 * Basic capture sanity only. This is deliberately not a biomechanical verdict.
 * It catches empty renders, obvious camera clipping and pathological framing.
 */
export function silhouetteSanity(
  metrics: SilhouetteMetrics,
  options: { minAreaRatio?: number; maxAreaRatio?: number } = {},
): SilhouetteSanity {
  const minArea = options.minAreaRatio ?? 0.005;
  const maxArea = options.maxAreaRatio ?? 0.9;
  const issues: string[] = [];

  if (metrics.foregroundPixels === 0 || !metrics.bounds || !metrics.centroid) {
    issues.push('silhouette is empty');
  } else {
    if (metrics.areaRatio < minArea) issues.push(`silhouette occupies only ${(metrics.areaRatio * 100).toFixed(2)}% of the frame`);
    if (metrics.areaRatio > maxArea) issues.push(`silhouette occupies ${(metrics.areaRatio * 100).toFixed(2)}% of the frame`);
    const touched = Object.entries(metrics.touches)
      .filter(([, value]) => value)
      .map(([edge]) => edge);
    if (touched.length > 0) issues.push(`silhouette touches frame edge: ${touched.join(', ')}`);
  }

  return { passed: issues.length === 0, issues };
}

export interface SilhouetteComparison {
  areaRatioDelta: number;
  centroidDistance: number | null;
  boundsEdgeMaxDelta: number | null;
}

/**
 * Compare two already-normalized mask summaries. This is deliberately a
 * measurement, not a pass/fail rule; a future certified reference decides what
 * amount of difference is acceptable.
 */
export function compareSilhouetteMetrics(
  candidate: SilhouetteMetrics,
  reference: SilhouetteMetrics,
): SilhouetteComparison {
  const centroidDistance =
    candidate.centroid && reference.centroid
      ? Math.hypot(
          candidate.centroid.x - reference.centroid.x,
          candidate.centroid.y - reference.centroid.y,
        )
      : null;

  const boundsEdgeMaxDelta =
    candidate.bounds && reference.bounds
      ? Math.max(
          Math.abs(candidate.bounds.minX - reference.bounds.minX),
          Math.abs(candidate.bounds.minY - reference.bounds.minY),
          Math.abs(candidate.bounds.maxX - reference.bounds.maxX),
          Math.abs(candidate.bounds.maxY - reference.bounds.maxY),
        )
      : null;

  return {
    areaRatioDelta: candidate.areaRatio - reference.areaRatio,
    centroidDistance,
    boundsEdgeMaxDelta,
  };
}
