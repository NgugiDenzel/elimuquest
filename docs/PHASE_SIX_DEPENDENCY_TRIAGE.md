# Phase Six Dependency and Expo SDK Triage

**Review date:** 2026-10-29  
**Expo SDK:** 58

## Changes and checks

- Aligned installed direct packages to the SDK 58 compatibility matrix:
  Expo `~58.0.21`, Expo Router `~58.0.28`, React Native `0.88.1`, React/React DOM
  `19.3.0`, and SDK-matched Expo modules.
- Installed the required `expo-font` peer (`~58.0.11`) and added its config plugin.
- Updated the React Native Testing Library to `14.1.0`, Jest to `~30.5.2`,
  jest-expo to `~58.0.13`, and the matching `react-test-renderer` to `19.3.0`.
- Migrated the custom tab-bar type and navigation callback to
  `expo-router/js-tabs`, then moved lesson detail routes to an authenticated root-stack
  group. The local browser journey verified the resulting routes.
- Removed unused direct `query-string` and `zod` dependencies after confirming there
  were no imports in app, source, or backend code. Expo CLI still pulls a vulnerable
  Zod version transitively.
- `npx expo install --check`: dependencies up to date.
- `npx expo-doctor`: 20/20 checks passed.
- `npx expo export --platform web`: passed after the routing changes.

## Remaining npm advisories

`npm audit --omit=dev` reports **14 advisories: 3 high, 11 low, 0 moderate, 0 critical**.
The remaining high findings are in the Expo CLI configuration dependency chain:

- `deepmerge` prototype-poisoning advisory, reachable through Expo config/CLI tooling.
- Zod's high-severity oversized constrained-collection memory-exhaustion advisory,
  pulled transitively by Expo CLI.

The suggested automatic fix would downgrade Expo to 51, which is an incompatible SDK
change. No force fix or unsafe major downgrade was applied. Current advisories require
continued review in a supported Expo dependency update; this report does not claim the
tree is vulnerability-free. The direct unused `query-string` dependency was removed,
eliminating its previous moderate advisory from the final audit.

`npm audit` also reports low-severity items. Review the current lockfile and advisory
paths again before any external beta or production build. Native iOS/Android builds were
not run in this phase.
