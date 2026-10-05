# Graph Report - desktop/minima-core-apks  (2026-09-15)

## Corpus Check
- 9 files · ~94,753 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 43 nodes · 52 edges · 13 communities (6 shown, 7 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 1 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `bb6ab829`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Verdicts
- PandaApps catalog (minima-core-apks)
- User instructions — AUTHORITATIVE. These override default behavior and must be followed exactly.
- CHANGELOG.md
- check.py
- apk_identity
- expected_code
- fetch_release_file
- find_tool
- published_codes
- pre-push
- main

## God Nodes (most connected - your core abstractions)
1. `main()` - 9 edges
2. `main()` - 8 edges
3. `apk_identity()` - 4 edges
4. `fetch_release_file()` - 4 edges
5. `User instructions — AUTHORITATIVE. These override default behavior and must be followed exactly.` - 4 edges
6. `Verdicts` - 4 edges
7. `PandaApps catalog (minima-core-apks)` - 4 edges
8. `sha256()` - 3 edges
9. `expected_code()` - 3 edges
10. `published_codes()` - 3 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `apk_identity()`  [EXTRACTED]
  desktop/minima-core-apks/scripts/sync-upstream-core.py → desktop/minima-core-apks/check.py
- `main()` --calls--> `sha256()`  [EXTRACTED]
  desktop/minima-core-apks/scripts/sync-upstream-core.py → desktop/minima-core-apks/check.py
- `main()` --calls--> `fetch_release_file()`  [EXTRACTED]
  desktop/minima-core-apks/scripts/sync-upstream-core.py → desktop/minima-core-apks/check.py
- `main()` --calls--> `main()`  [EXTRACTED]
  desktop/minima-core-apks/scripts/sync-upstream-core.py → desktop/minima-core-apks/check.py

## Import Cycles
- None detected.

## Communities (13 total, 7 thin omitted)

### Community 0 - "Verdicts"
Cohesion: 0.33
Nodes (5): FULLY COMPATIBLE — identical behavior on official and forked core, HARD — requires the fork, does NOT work on official Minima Core, Node compatibility — which apps need the forked "Minima Core — New UI (Preview)"?, SOFT — works on official core, specific features need the fork, Verdicts

### Community 1 - "PandaApps catalog (minima-core-apks)"
Cohesion: 0.40
Nodes (4): History, PandaApps catalog (minima-core-apks), Publishing a new app version, Verification

### Community 2 - "User instructions — AUTHORITATIVE. These override default behavior and must be followed exactly."
Cohesion: 0.40
Nodes (4): Before publishing: run `./check.py`, RULE 0 (highest priority) — Follow the user's explicit instructions. They are BLOCKING, not suggestions., RULE — binaries NEVER go in this repo's git, User instructions — AUTHORITATIVE. These override default behavior and must be followed exactly.

### Community 4 - "check.py"
Cohesion: 0.83
Nodes (3): apk_signer(), main(), sha256()

### Community 12 - "main"
Cohesion: 0.52
Nodes (6): apk_cert_sha256(), die(), gh_json(), main(), Signer #1 certificate SHA-256 digest, lowercased, or None., semver()

## Knowledge Gaps
- **10 isolated node(s):** `Changelog`, `RULE 0 (highest priority) — Follow the user's explicit instructions. They are BLOCKING, not suggestions.`, `RULE — binaries NEVER go in this repo's git`, `Before publishing: run `./check.py``, `HARD — requires the fork, does NOT work on official Minima Core` (+5 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `main` to `check.py`, `apk_identity`, `fetch_release_file`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Why does `main()` connect `check.py` to `apk_identity`, `expected_code`, `fetch_release_file`, `published_codes`, `main`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Why does `apk_identity()` connect `apk_identity` to `check.py`, `main`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **What connects `Changelog`, `RULE 0 (highest priority) — Follow the user's explicit instructions. They are BLOCKING, not suggestions.`, `RULE — binaries NEVER go in this repo's git` to the rest of the system?**
  _10 weakly-connected nodes found - possible documentation gaps or missing edges._