import { defineConfig } from 'vitest/config';
import { fileURLToPath } from 'node:url';

// Scratch harness only. Runs the measurement files in this folder against the
// real src/ production path, without adding anything to the repo's own suite.
export default defineConfig({
  resolve: {
    alias: { '@': fileURLToPath(new URL('../../src', import.meta.url)) },
  },
  test: {
    environment: 'node',
    include: ['scratchpad/repair/**/*.test.mts'],
    setupFiles: ['./src/test/setup.ts'],
    testTimeout: 300000,
    hookTimeout: 300000,
  },
});
