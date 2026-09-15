# Graph Report - desktop/minima-core-apks  (2026-09-04)

## Corpus Check
- 8 files · ~90,595 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 36 nodes · 36 edges · 12 communities (5 shown, 7 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `11f77bc5`
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

## God Nodes (most connected - your core abstractions)
1. `main()` - 7 edges
2. `User instructions — AUTHORITATIVE. These override default behavior and must be followed exactly.` - 4 edges
3. `Verdicts` - 4 edges
4. `PandaApps catalog (minima-core-apks)` - 4 edges
5. `apk_identity()` - 3 edges
6. `fetch_release_file()` - 3 edges
7. `expected_code()` - 3 edges
8. `published_codes()` - 3 edges
9. `find_tool()` - 2 edges
10. `apk_signer()` - 2 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `apk_identity()`  [EXTRACTED]
  desktop/minima-core-apks/check.py → desktop/minima-core-apks/check.py  _Bridges community 5 → community 4_
- `main()` --calls--> `fetch_release_file()`  [EXTRACTED]
  desktop/minima-core-apks/check.py → desktop/minima-core-apks/check.py  _Bridges community 7 → community 4_
- `main()` --calls--> `expected_code()`  [EXTRACTED]
  desktop/minima-core-apks/check.py → desktop/minima-core-apks/check.py  _Bridges community 6 → community 4_
- `main()` --calls--> `published_codes()`  [EXTRACTED]
  desktop/minima-core-apks/check.py → desktop/minima-core-apks/check.py  _Bridges community 9 → community 4_

## Import Cycles
- None detected.

## Communities (12 total, 7 thin omitted)

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

## Knowledge Gaps
- **10 isolated node(s):** `Changelog`, `RULE 0 (highest priority) — Follow the user's explicit instructions. They are BLOCKING, not suggestions.`, `RULE — binaries NEVER go in this repo's git`, `Before publishing: run `./check.py``, `HARD — requires the fork, does NOT work on official Minima Core` (+5 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `check.py` to `published_codes`, `apk_identity`, `expected_code`, `fetch_release_file`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Why does `find_tool()` connect `find_tool` to `check.py`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Why does `apk_identity()` connect `apk_identity` to `check.py`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **What connects `Changelog`, `RULE 0 (highest priority) — Follow the user's explicit instructions. They are BLOCKING, not suggestions.`, `RULE — binaries NEVER go in this repo's git` to the rest of the system?**
  _10 weakly-connected nodes found - possible documentation gaps or missing edges._