import { registerBundledCharacter, registerCharacterSource, setDefaultCharacter } from './registry';
import { retargetedCharacterSource } from './retargetSource';

/**
 * The character the app ships with.
 *
 * Two files, because they answer different questions. `BASELINE` is the body on
 * its own, which is what a deformation review needs; `DRESSED` is the same body
 * with the shorts mesh over it, which is what the app should show. Both are the
 * same skeleton, the same weights and the same vertices — the garment is an
 * extra mesh in the file, not a different character — so switching between them
 * in the Character panel changes what is worn and nothing else.
 *
 * The files are not in the repository: they are large binaries, and the studio
 * has to work for anyone who clones it without them. So this probes for them and
 * registers what it finds, leaving the built-in procedural character as the
 * default when it finds nothing. A missing asset is not an error.
 */

export const BASELINE_CHARACTER_URL = 'characters/HomeGymPT_Male_BASELINE_v6.glb';
export const DRESSED_CHARACTER_URL = 'characters/HomeGymPT_Male_BASELINE_v6_SHORTS.glb';

async function present(url: string): Promise<boolean> {
  try {
    // One byte, not a HEAD: static file middleware does not reliably answer
    // HEAD for files it serves out of the public directory, and a probe that
    // reports a present file as missing would silently drop the character.
    const response = await fetch(url, { headers: { Range: 'bytes=0-0' } });
    if (!response.ok && response.status !== 206) return false;
    // A dev server answers a missing path with index.html rather than a 404,
    // so the type has to be checked as well as the status.
    return !(response.headers.get('content-type') ?? '').includes('text/html');
  } catch {
    return false;
  }
}

/**
 * Register whichever bundled characters are available, and make the dressed one
 * the default when it is there. Returns the ids that were registered.
 */
export async function registerBundledCharacters(): Promise<string[]> {
  const registered: string[] = [];

  if (await present(BASELINE_CHARACTER_URL)) {
    registerCharacterSource(
      retargetedCharacterSource({
        id: 'baseline',
        label: 'Home Gym PT male',
        note: 'Production baseline body, no clothing — for deformation review',
        url: BASELINE_CHARACTER_URL,
      }),
    );
    registered.push('baseline');
  }

  if (await present(DRESSED_CHARACTER_URL)) {
    registerBundledCharacter({
      id: 'baseline-dressed',
      label: 'Home Gym PT male (shorts)',
      note: 'Production baseline body with the athletic shorts layer',
      url: DRESSED_CHARACTER_URL,
    });
    registered.push('baseline-dressed');
  } else if (registered.includes('baseline')) {
    setDefaultCharacter('baseline');
  }

  return registered;
}
