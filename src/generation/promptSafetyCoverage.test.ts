import { describe, expect, it } from 'vitest';
import { EXERCISES } from '../exercises/library';
import { parsePrompt } from './parse';

const blockingCodes = (prompt: string) =>
  parsePrompt(prompt).issues.filter((issue) => issue.blocking).map((issue) => issue.code);

describe('prompt-safety coverage across the registered exercise library', () => {
  it('never drops unsupported programming, support, stance, grip-width or negated-tempo constraints', () => {
    for (const exercise of EXERCISES) {
      const name = exercise.name;
      expect(blockingCodes(`exercise: ${name} for 10 reps`), name).toContain('programming');
      expect(blockingCodes(`exercise: ${name} 3x10`), name).toContain('programming');
      expect(blockingCodes(`exercise: ${name} 3 rounds`), name).toContain('programming');
      expect(blockingCodes(`exercise: ${name} 3-second lowering`), name).toContain('tempo');
      expect(blockingCodes(`exercise: kneeling ${name}`), name).toContain('support');
      expect(blockingCodes(`exercise: wide stance ${name}`), name).toContain('variant');
      expect(blockingCodes(`exercise: wide grip ${name}`), name).toContain('grip');
      expect(blockingCodes(`exercise: ${name} not slow`), name).toContain('tempo');
      expect(blockingCodes(`exercise: ${name} tempo 30x0`), name).toContain('tempo');
      expect(blockingCodes(`exercise: ${name} using right leg`), name).toContain('execution');
      const base = parsePrompt(`exercise: ${name}`);
      if (base.intent?.equipment === 'bodyweight') {
        const weightedCodes = blockingCodes(`exercise: weighted ${name}`);
        expect(weightedCodes.length, name).toBeGreaterThan(0);
        expect(weightedCodes.some((code) => code === 'load' || code === 'variant' || code === 'equipment'), name).toBe(true);
      }
    }
  });

  it('never treats negated certified equipment as a positive equipment request', () => {
    for (const exercise of EXERCISES) {
      const base = parsePrompt(`exercise: ${exercise.name}`);
      expect(base.issues.filter((issue) => issue.blocking), exercise.id).toEqual([]);
      expect(base.intent, exercise.id).not.toBeNull();

      if (base.intent!.equipment === 'dumbbell') {
        expect(blockingCodes(`exercise: ${exercise.name} without dumbbells`), exercise.id)
          .toContain('equipment');
      } else if (base.intent!.equipment === 'cable') {
        expect(blockingCodes(`exercise: ${exercise.name} without cable`), exercise.id)
          .toContain('equipment');
      }
    }
  });
});
