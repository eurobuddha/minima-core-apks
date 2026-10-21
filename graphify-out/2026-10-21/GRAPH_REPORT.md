# Graph Report - /Users/eurobuddha/Projects/minima/desktop/minima-core-apks  (2026-10-20)

## Corpus Check
- 1 files · ~402 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 75 nodes · 91 edges · 10 communities (8 shown, 2 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 1 edges (avg confidence: 0.5)
- Token cost: 1,044 input · 8,327 output

## Community Hubs (Navigation)
- check.py
- Release Publication and Handoff
- Release Publication and Handoff
- main
- Verdicts
- Release Publication and Handoff
- User instructions — AUTHORITATIVE. These override default behavior and must be followed exactly.
- PandaApps catalog (minima-core-apks)
- CHANGELOG.md
- pre-push

## God Nodes (most connected - your core abstractions)
1. `Canonical Android mainline` - 12 edges
2. `main()` - 9 edges
3. `minima-core-apks catalogue` - 9 edges
4. `main()` - 8 edges
5. `ETH Wallet 0.2.11/code211` - 6 edges
6. `AtomiX 0.1.82/code182` - 6 edges
7. `Release and convergence handoff — 2026-10-20` - 5 edges
8. `apk_identity()` - 4 edges
9. `fetch_release_file()` - 4 edges
10. `User instructions — AUTHORITATIVE. These override default behavior and must be followed exactly.` - 4 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `apk_identity()`  [EXTRACTED]
  scripts/sync-upstream-core.py → check.py
- `main()` --calls--> `sha256()`  [EXTRACTED]
  scripts/sync-upstream-core.py → check.py
- `main()` --calls--> `fetch_release_file()`  [EXTRACTED]
  scripts/sync-upstream-core.py → check.py
- `main()` --calls--> `main()`  [EXTRACTED]
  scripts/sync-upstream-core.py → check.py

## Import Cycles
- None detected.

## Communities (10 total, 2 thin omitted)

### Community 0 - "check.py"
Cohesion: 0.17
Nodes (13): apk_identity(), apk_signer(), expected_code(), fetch_release_file(), find_tool(), main(), published_codes(), Local path to the binary at `url`, downloading into the cache on a miss. The… (+5 more)

### Community 1 - "Release Publication and Handoff"
Cohesion: 0.18
Nodes (16): AtomiX-0.1.82.apk, AtomiX 0.1.82/code182, Hetzner build_ipfs_store.sh, minima-core-apks catalogue, ethwallet-0.2.11.apk, ETH Wallet 0.2.11/code211, Family certificate, Release and convergence handoff — 2026-10-20 (+8 more)

### Community 2 - "Release Publication and Handoff"
Cohesion: 0.20
Nodes (10): ARTIFACTS JSON, Canonical Android mainline, BlackBear 2.0.28/code223, Convergence archive, CONVERGENCE_2.0.30_2026-10-20.txt, base/integrated, PandaBear, Independent full code review and interactive smoke (+2 more)

### Community 3 - "main"
Cohesion: 0.52
Nodes (6): apk_cert_sha256(), die(), gh_json(), main(), Signer #1 certificate SHA-256 digest, lowercased, or None., semver()

### Community 4 - "Verdicts"
Cohesion: 0.33
Nodes (5): FULLY COMPATIBLE — identical behavior on official and forked core, HARD — requires the fork, does NOT work on official Minima Core, Node compatibility — which apps need the forked "Minima Core — New UI (Preview)"?, SOFT — works on official core, specific features need the fork, Verdicts

### Community 5 - "Release Publication and Handoff"
Cohesion: 0.33
Nodes (6): Bears all-flavor build 2.0.30/code226, Bears bundle, Fold R3GL805K7MB, Keets1.2.3, Pandamonium 2.0.30/code226, prepare-keets.py

### Community 6 - "User instructions — AUTHORITATIVE. These override default behavior and must be followed exactly."
Cohesion: 0.40
Nodes (4): Before publishing: run `./check.py`, RULE 0 (highest priority) — Follow the user's explicit instructions. They are BLOCKING, not suggestions., RULE — binaries NEVER go in this repo's git, User instructions — AUTHORITATIVE. These override default behavior and must be followed exactly.

### Community 7 - "PandaApps catalog (minima-core-apks)"
Cohesion: 0.40
Nodes (4): History, PandaApps catalog (minima-core-apks), Publishing a new app version, Verification

## Knowledge Gaps
- **26 isolated node(s):** `Changelog`, `RULE 0 (highest priority) — Follow the user's explicit instructions. They are BLOCKING, not suggestions.`, `RULE — binaries NEVER go in this repo's git`, `Before publishing: run `./check.py``, `HARD — requires the fork, does NOT work on official Minima Core` (+21 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Canonical Android mainline` connect `Release Publication and Handoff` to `Release Publication and Handoff`, `Release Publication and Handoff`?**
  _High betweenness centrality (0.122) - this node is a cross-community bridge._
- **Why does `Release and convergence handoff — 2026-10-20` connect `Release Publication and Handoff` to `Release Publication and Handoff`?**
  _High betweenness centrality (0.088) - this node is a cross-community bridge._
- **What connects `Changelog`, `RULE 0 (highest priority) — Follow the user's explicit instructions. They are BLOCKING, not suggestions.`, `RULE — binaries NEVER go in this repo's git` to the rest of the system?**
  _26 weakly-connected nodes found - possible documentation gaps or missing edges._

## Update scope — 2026-10-20

Added verified release/convergence facts from RELEASE_PUBLICATION_2026-10-20.txt. Existing code nodes preserved. This is a release-record update, not a full code re-index; legacy manifest scan roots require reconciliation before pruning. Backups: 2026-10-20-before-release-memory/.
