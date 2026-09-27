# One-command ORIGINAL v1 start

After the final V15f legacy benchmark is preserved, switch to:

`work/standalone-first-party-audit-20260927`

Then run:

```bat
PREPARE_ORIGINAL_V1_CLEAN_ROOM.bat
```

It:
1. refuses the wrong branch;
2. creates/refreshes the clean project-authored procedural scaffold;
3. runs the Blender clean-room audit;
4. opens the Blend only after the audit passes.

It does **not**:
- reset or clean Git;
- import V15f/V8/MakeHuman;
- promote the scaffold;
- alter the live source branch.

The verified Blend is:
`ORIGINAL_V1_WORK/HomeGymPT_Male_ORIGINAL_v1.blend`

This is the preferred Work entry point once V15f becomes reference-only.
