from pathlib import Path

p = Path('src/editor/store.test.ts')
text = p.read_text()
old = """    useStudio.getState().markVisualReview('import-v5');
    expect(useStudio.getState().visualReview).toEqual({ document: reviewed, characterSourceId: 'import-v5' });
"""
new = """    useStudio.getState().markVisualReview('import-v5', 3);
    expect(useStudio.getState().visualReview).toEqual({
      document: reviewed,
      characterSourceId: 'import-v5',
      deformationRevision: 3,
    });
"""
if old not in text:
    raise SystemExit('missing existing visual review test anchor')
p.write_text(text.replace(old, new, 1))
print('Migrated existing visual review identity regression')
