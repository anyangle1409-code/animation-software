/**
 * First-party glTF runtime naming.
 *
 * The scene adapter and the preserved-GLB exporter must agree on the name a
 * glTF node receives at runtime. Keeping the rule here prevents either side
 * from depending on Three PropertyBinding internals.
 */
const RESERVED_BINDING_CHARS = /[\[\].:\/]/g;

export function hgRuntimeNodeName(
  name: string,
  used: Map<string, number>,
): string {
  const sanitized = name.replace(/\s/g, '_').replace(RESERVED_BINDING_CHARS, '');
  if (!sanitized) return '';
  const seen = used.get(sanitized);
  if (seen === undefined) {
    used.set(sanitized, 0);
    return sanitized;
  }
  const next = seen + 1;
  used.set(sanitized, next);
  return `${sanitized}_${next}`;
}

export function hgRuntimeNodeNames(names: readonly string[]): string[] {
  const used = new Map<string, number>();
  return names.map((name) => hgRuntimeNodeName(name, used));
}
