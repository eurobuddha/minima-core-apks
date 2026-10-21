# Graph Report - minima-core-apks  (2026-10-21)

## Corpus Check
- 11 files · ~102,002 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 113 nodes · 152 edges · 11 communities (7 shown, 4 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 1 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0ca996fd`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- check.py
- minima-core-apks catalogue
- Canonical Android mainline
- main
- Verdicts
- SyncTests
- User instructions — AUTHORITATIVE. These override default behavior and must be followed exactly.
- PandaApps catalog (minima-core-apks)
- CHANGELOG.md
- pre-push
- CatalogIdentityTests

## God Nodes (most connected - your core abstractions)
1. `SyncTests` - 22 edges
2. `Canonical Android mainline` - 12 edges
3. `main()` - 10 edges
4. `main()` - 9 edges
5. `minima-core-apks catalogue` - 9 edges
6. `CatalogIdentityTests` - 8 edges
7. `ensure_mirror()` - 7 edges
8. `PandaApps catalog (minima-core-apks)` - 6 edges
9. `ETH Wallet 0.2.11/code211` - 6 edges
10. `AtomiX 0.1.82/code182` - 6 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `apk_identity()`  [EXTRACTED]
  scripts/sync-upstream-core.py → check.py
- `apk_cert_sha256()` --calls--> `apk_signer()`  [EXTRACTED]
  scripts/sync-upstream-core.py → check.py
- `main()` --calls--> `main()`  [EXTRACTED]
  scripts/sync-upstream-core.py → check.py
- `ensure_mirror()` --calls--> `sha256()`  [EXTRACTED]
  scripts/sync-upstream-core.py → check.py
- `main()` --calls--> `sha256()`  [EXTRACTED]
  scripts/sync-upstream-core.py → check.py

## Import Cycles
- None detected.

## Communities (11 total, 4 thin omitted)

### Community 0 - "check.py"
Cohesion: 0.16
Nodes (14): apk_identity(), apk_package(), apk_signer(), expected_code(), fetch_release_file(), find_tool(), main(), published_codes() (+6 more)

### Community 1 - "minima-core-apks catalogue"
Cohesion: 0.20
Nodes (15): AtomiX-0.1.82.apk, AtomiX 0.1.82/code182, Hetzner build_ipfs_store.sh, minima-core-apks catalogue, ethwallet-0.2.11.apk, ETH Wallet 0.2.11/code211, Family certificate, Release and convergence handoff — 2026-10-20 (+7 more)

### Community 2 - "Canonical Android mainline"
Cohesion: 0.12
Nodes (17): ARTIFACTS JSON, Bears all-flavor build 2.0.30/code226, Bears bundle, Canonical Android mainline, BlackBear 2.0.28/code223, Convergence archive, CONVERGENCE_2.0.30_2026-10-20.txt, Fold R3GL805K7MB (+9 more)

### Community 3 - "main"
Cohesion: 0.44
Nodes (9): sha256(), apk_cert_sha256(), die(), download(), ensure_mirror(), gh_json(), main(), Reuse an identical asset after an interrupted run; never overwrite one. (+1 more)

### Community 4 - "Verdicts"
Cohesion: 0.33
Nodes (5): FULLY COMPATIBLE — identical behavior on official and forked core, HARD — requires the fork, does NOT work on official Minima Core, Node compatibility — which apps need the forked "Minima Core — New UI (Preview)"?, SOFT — works on official core, specific features need the fork, Verdicts

### Community 6 - "User instructions — AUTHORITATIVE. These override default behavior and must be followed exactly."
Cohesion: 0.40
Nodes (4): Before publishing: run `./check.py`, RULE 0 (highest priority) — Follow the user's explicit instructions. They are BLOCKING, not suggestions., RULE — binaries NEVER go in this repo's git, User instructions — AUTHORITATIVE. These override default behavior and must be followed exactly.

### Community 7 - "PandaApps catalog (minima-core-apks)"
Cohesion: 0.29
Nodes (6): Automatic official Minima Core updates, Deprecated apps — do not relist, History, PandaApps catalog (minima-core-apks), Publishing a new app version, Verification

## Knowledge Gaps
- **28 isolated node(s):** `Changelog`, `RULE 0 (highest priority) — Follow the user's explicit instructions. They are BLOCKING, not suggestions.`, `RULE — binaries NEVER go in this repo's git`, `Before publishing: run `./check.py``, `HARD — requires the fork, does NOT work on official Minima Core` (+23 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Canonical Android mainline` connect `Canonical Android mainline` to `minima-core-apks catalogue`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `Release and convergence handoff — 2026-10-20` connect `minima-core-apks catalogue` to `Canonical Android mainline`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **What connects `Changelog`, `RULE 0 (highest priority) — Follow the user's explicit instructions. They are BLOCKING, not suggestions.`, `RULE — binaries NEVER go in this repo's git` to the rest of the system?**
  _28 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Canonical Android mainline` be split into smaller, more focused modules?**
  _Cohesion score 0.11764705882352941 - nodes in this community are weakly interconnected._
- **Should `SyncTests` be split into smaller, more focused modules?**
  _Cohesion score 0.13438735177865613 - nodes in this community are weakly interconnected._