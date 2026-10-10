# Windows c001 record reproduction — 2026-10-10

Scope: portable evidence-path serialization only. No candidate record, source
bytes, skeleton, landmark, geometry, motion, acceptance flag or frozen review
artifact changes. The inherited full suite remains red.

## Reproduced cause and minimal correction

Base: `f679af40f52420cbac5391b587e1bad5587d5aa7`, on isolated branch
`codex/windows-c001-source-paths-20261010` in the clean short verification
checkout `C:/Users/Mark/Documents/Codex/hgpt-source-blender-audit`.

Before editing, the two unchanged tests
`test_shoulder_proposal_c001.Identity.test_record_reproduces` and
`test_shoulder_proposal_c001.VerticalRelationAudit.test_reproduces` both
failed in laptop Blender 5.2.1 LTS. The complete comparison reported only two
candidate input paths and four vertical-relation hash dictionary keys:
Windows `str(Path.relative_to(...))` produced backslashes where the committed
records use forward slashes. Neither comparison reported geometry or hash
value changes. This independently reproduces the corresponding historical
failures rather than assuming every report mismatch is a path issue.

Three serialization expressions now use `Path.relative_to(...).as_posix()`:
the candidate's base and solution paths, and the vertical audit's input hash
keys. No numerical expressions, SHA calculations or tests were edited.

After editing, all **15 unchanged c001 tests passed** in actual laptop Blender
5.2.1 LTS (6.228 seconds of test execution), and the same 15 tests passed in
laptop Python (0.224 seconds). These include complete committed
record comparisons, source and review artifact hashes, candidate scope,
bilateral geometry, preserved arm lengths, CP2 verdicts and the explicitly
unresolved shoulder-height defect. `git diff --check` passed. CI now runs the
same tests in Windows Python and actual Ubuntu Blender, alongside the existing
source safety checks. Hosted results are pending at this checkpoint; local
success is not a substitute for hosted verification.

## Resume without repeating completed work

Do not rewrite a003, c001–c004, the source skeleton or frozen audit records to
make inherited failures green. Do not repeat the expensive full suite or 135
motion sweeps. Candidate and anatomical readiness remain unchanged.

Next isolated regression action: reproduce c002's unchanged record-comparison
test, inspect the complete difference list, and determine whether its base
path and input hash keys are the only differences before touching its builder.
Other historical lumbar, evidence-integrity, P003, production-control and
Windows symlink failures remain separate unresolved cases; this correction
does not classify or close them.
