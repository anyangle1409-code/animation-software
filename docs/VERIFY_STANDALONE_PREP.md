# Standalone preparation verification

After checking out:
`work/standalone-first-party-audit-20260927`

run:

```bat
VERIFY_STANDALONE_PREP.bat
```

It performs, in order:
1. typecheck;
2. focused first-party foundation tests;
3. full test suite;
4. production build;
5. runtime dependency anti-creep gate;
6. external runtime resource gate.

Prepared foundation tests currently cover:
- first-party observable store;
- first-party vectors/quaternions/matrices;
- first-party GLB 2.0 container;
- first-party glTF typed accessor reading;
- existing studio/character stores.

A PASS means the prepared migration foundation is safe enough to continue. It
**does not** mean the finished product is already standalone.

After it passes, run:
`npm run audit:standalone`

The standalone audit is expected to continue failing until all third-party
runtime dependencies and legacy/MakeHuman production paths are removed.
