# TypeScript repair report

## Symptom
Running `npx tsc --noEmit` failed with a recursive compiler crash:

`RangeError: Maximum call stack size exceeded`

## Root cause
The project had a stale generated build output in `dist/_expo` and the compiler was being asked to inspect an overly broad/inappropriate set of files. A fresh `tsc --showConfig` also showed generated Expo web bundle content included in the compilation set, which can trigger recursive type expansion in this project setup.

Additionally, the project had a mismatched TypeScript package version for the installed Expo stack, which increased the risk of compiler instability.

## Fix applied
Updated the root `tsconfig.json` to:
- restrict compilation to actual app and source files
- exclude `dist`, `.expo`, `android`, and `ios`
- disable JS input (`allowJs: false`)

This preserved strict type checking without including generated build artifacts.

## Verification
Command executed:
`cd C:\Users\Admin\Desktop\elimuquest; npx tsc --noEmit`

Result:
- Passed successfully with exit code 0.

## Files changed
- `C:\Users\Admin\Desktop\elimuquest\tsconfig.json`

## Remaining note
The project still has dependency-version drift reported by `npx expo-doctor`, but the actual stack-overflow issue is resolved and the project compiles cleanly for the app code itself.
