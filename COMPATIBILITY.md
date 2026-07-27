# Node compatibility — which apps need the forked "Minima Core — New UI (Preview)"?

Audited 2026-07-27 against every app's bundled `minimaapi.aar` (compiled-constant inspection)
and full source grep for fork-only IPC surfaces. The fork (eurobuddha/minima-core-android,
"Minima Core — New UI (Preview)", 1.6.x) adds three IPC surfaces the official Spartacus-signed
Minima Core (1.2.5) does not have:

| Fork surface | Behavior on OFFICIAL core |
|---|---|
| `.FILE` bridge (list/stat/get/put/mkdir/move/delete) | broadcasts silently ignored → app times out |
| Large-response hand-off (`CMD_FILERESP` → `content://` file) | flag ignored → results >256KB return the "Result too long!" stub |
| Off-main-thread command executor | socket commands (`megammrsync`, `archive resync`) fail with a bogus "Could not connect to Archive host!" (upstream bug, fixed only in the fork) |

## Verdicts

### HARD — requires the fork, does NOT work on official Minima Core
| App | Why |
|---|---|
| **Filez** | The entire app is built on the `.FILE` bridge (every operation: list/stat/get/put/mkdir/move/delete). On official core no receiver handles the broadcasts → every action times out. Store description carries "Needs Minima Core 1.3.1+ (New UI preview)". |

### SOFT — works on official core, specific features need the fork
| App | On official core |
|---|---|
| **Minima Terminal** (1.2+) | Normal commands fine. Results >256KB → "Result too long!" stub (fork returns them in full). Socket commands (`megammrsync`/`archive resync`) fail with the bogus connect error (official-core main-thread bug). |
| **Terminal IDE** (0.1.5+) | Same two degradations as Terminal; everything else (editor, autocomplete, workbench) unaffected. |

### FULLY COMPATIBLE — identical behavior on official and forked core
casino, ethwallet, expert, faucet, futurecash, history, limit, mail, merch trio
(Shop/Inbox/Studio), minimaswap, usdtswap, AtomiX, pandapools, utxo wallet, vestr,
self-custody wallet — all bundle the pre-fork minimaapi (no fork constants compiled in;
verified byte-level), issue plain bounded commands, and never touch a fork surface.
Their IPC behavior is byte-identical against either node.

Notes:
- utxo wallet's unbounded `coins` query can exceed 256KB on a very heavy wallet — but its
  old AAR never opts into the fork hand-off, so that limit applies on BOTH nodes equally
  (not a fork dependency; fixable in the app by adopting the new AAR).
- history app pages adaptively (8→4→2→1) by design — tolerant of the cap everywhere.
- **PandaApps** (the store itself) and **FreezePeach** don't use the node IPC at all
  (catalog/download only; relay + embedded core respectively).
- The fork's node-internal features (Startup Params, Logs tab, MegaMMR import fixes,
  file-hand-off, admin file bridge) never affect apps that don't call them.
