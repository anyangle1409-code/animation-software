# Windows c001/c002 record reproduction — 2026-10-10

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

The next c002 record comparison was independently reproduced before editing:
one failure, 0.207 seconds. Its complete difference list contains only the
base record path and four input SHA dictionary keys. Those two serialization
expressions now also use `as_posix()`, with numerical code, source hashes,
candidate geometry and frozen tests unchanged. All **31 unchanged c001/c002
tests pass** in laptop Python (2.424 seconds) and actual Blender 5.2.1
(2.797 seconds), including retained closure failure and unaccepted status.

Initial hosted run `38092898558` at `16050424` passed the Windows and source
safety jobs. The added native Ubuntu c001 step failed before tests could load
because the distro Blender Python had no NumPy; the pre-existing real-render
and source-triangle tests passed. The workflow now explicitly installs its
existing reconstruction dependency `python3-numpy` with Blender. This is a
runner setup correction, not a skipped test or relaxed assertion. Hosted
31-test verification remains pending at this checkpoint.

Next isolated regression action: verify all jobs at the latest PR #45 head,
then reproduce c003 or the shoulder ANSUR acromion audit and inspect all
differences before deciding whether any further path-only fix is justified.
Other historical lumbar, evidence-integrity, P003, production-control and
Windows symlink failures remain separate unresolved cases; this correction
does not classify or close them.
