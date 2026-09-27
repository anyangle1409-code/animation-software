@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo Home Gym PT standalone preparation verification
echo ============================================================

echo.
echo [1/7] TypeScript typecheck
call npm run typecheck
if errorlevel 1 goto :fail

echo.
echo [2/7] Focused first-party foundation tests
call npm test -- src/core/store.test.ts src/core/linearMath.test.ts src/core/linearMath.parity.test.ts src/core/glbContainer.test.ts src/core/gltfAccessors.test.ts src/core/gltfBuilder.test.ts src/core/frameLoop.test.ts src/rig/firstPartySkeleton.parity.test.ts src/ik/firstPartyOrient.parity.test.ts src/rig/firstPartyPose.parity.test.ts src/editor/store.test.ts src/editor/characterStore.test.ts
if errorlevel 1 goto :fail

echo.
echo [3/7] Full current test suite
call npm test
if errorlevel 1 goto :fail

echo.
echo [4/7] Production build
call npm run build
if errorlevel 1 goto :fail

echo.
echo [5/7] Runtime dependency anti-creep gate
node scripts\check-runtime-dependency-creep.mjs
if errorlevel 1 goto :fail

echo.
echo [6/7] External runtime resource gate
node scripts\audit-external-runtime-resources.mjs
if errorlevel 1 goto :fail

echo.
echo [7/7] Runtime network/API gate
node scripts\audit-runtime-network.mjs
if errorlevel 1 goto :fail

echo.
echo ============================================================
echo PREP VERIFICATION PASS
echo ============================================================
echo.
echo The project is NOT yet standalone. This only proves the prepared
echo replacement foundations are safe enough to continue migrating.
echo.
echo Now run:
echo   npm run audit:standalone
echo.
echo That audit is expected to report remaining migration blockers.
exit /b 0

:fail
echo.
echo ============================================================
echo PREP VERIFICATION FAILED
echo ============================================================
echo Do not remove a dependency or switch production implementation.
echo Fix the isolated first-party preparation first.
exit /b 1
