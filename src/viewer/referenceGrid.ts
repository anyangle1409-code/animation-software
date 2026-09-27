import { HgVec3 } from '../core/linearMath';

export interface HgGridLine {
  start: HgVec3;
  end: HgVec3;
  major: boolean;
}

export interface HgGridOptions {
  size?: number;
  cellSize?: number;
  sectionSize?: number;
  height?: number;
}

export interface HgGridBuffers {
  minor: Float32Array;
  major: Float32Array;
}

/** Build the studio reference grid as project-owned line geometry. */
export function buildHgReferenceGrid(options: HgGridOptions = {}): HgGridLine[] {
  const size = options.size ?? 12;
  const cellSize = options.cellSize ?? 0.25;
  const sectionSize = options.sectionSize ?? 1;
  const height = options.height ?? 0.001;

  if (size <= 0 || cellSize <= 0 || sectionSize <= 0) {
    throw new Error('Grid size, cellSize and sectionSize must be positive');
  }

  const steps = Math.round(size / cellSize);
  const half = size / 2;
  const lines: HgGridLine[] = [];

  const isMajor = (coordinate: number) => {
    const sections = coordinate / sectionSize;
    return Math.abs(sections - Math.round(sections)) < 1e-9;
  };

  for (let index = 0; index <= steps; index += 1) {
    const coordinate = -half + index * cellSize;
    const major = isMajor(coordinate);

    lines.push({
      start: new HgVec3(coordinate, height, -half),
      end: new HgVec3(coordinate, height, half),
      major,
    });
    lines.push({
      start: new HgVec3(-half, height, coordinate),
      end: new HgVec3(half, height, coordinate),
      major,
    });
  }

  return lines;
}

/** Pack the project-owned grid into renderer-neutral line-segment buffers. */
export function buildHgReferenceGridBuffers(options: HgGridOptions = {}): HgGridBuffers {
  const minor: number[] = [];
  const major: number[] = [];

  for (const line of buildHgReferenceGrid(options)) {
    const target = line.major ? major : minor;
    target.push(
      line.start.x,
      line.start.y,
      line.start.z,
      line.end.x,
      line.end.y,
      line.end.z,
    );
  }

  return {
    minor: new Float32Array(minor),
    major: new Float32Array(major),
  };
}
