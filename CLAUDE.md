# User instructions — AUTHORITATIVE. These override default behavior and must be followed exactly.

## RULE 0 (highest priority) — Follow the user's explicit instructions. They are BLOCKING, not suggestions.

When the user gives an explicit instruction, do exactly that, first, before anything else. The user's instruction
takes priority over your own plan, your preferred approach, and your judgment about a "better" way. You must never
substitute your own idea for what the user told you to do.

1. **Reuse before you reinvent.** If the user points you at existing code, a file, a sibling app, or an existing
   solution, read and use it FIRST — before you propose, design, diagnose, or build anything new. Reinventing is
   permitted only after you have read the named source and can state specifically why it does not fit.
2. **"Look at X", "use Y", "do Z first", "don't do W" are hard, blocking instructions.** Act on them immediately, in
   the same turn. They are never something to get to later.
3. **Never silently substitute your own approach.** The moment you notice you are about to build, diagnose, or design
   something new when the user has named an existing source or given a direct instruction, stop and follow the
   instruction.
4. **Disagree openly; never disobey quietly.** If you genuinely believe an instruction is wrong or will not work, say
   so plainly and ask — in the same turn, before acting. Quietly doing something else instead is not acceptable.

When your instinct conflicts with the user's instruction, follow the instruction. Ignoring it wastes the user's time,
tokens, and money, and is the most serious mistake you can make.

## RULE — binaries NEVER go in this repo's git

This repo is the **manifest only**: `apks.json`, `icons/`, docs, `scripts/`, `hooks/`.
Every APK/dmg/installer lives as a **GitHub Release asset on its own app's repo**, and
the catalog row's `file` field points at `https://github.com/eurobuddha/<app-repo>/releases/download/v<version>/<file>`.
Committing a binary here is a defect — the repo hit 13 GB that way and its history had to
be rewritten on 2026-08-26. The only binaries associated with this repo are its own
Releases: `mirrors` (upstream Minima Core APKs, which publish no releases of their own).

**Publish flow for a new app version** (in this order):
1. In the app's repo: `gh release create v<ver> <apk> --title "<App> <ver>" --notes "<one line>"`.
2. Here: `scripts/publish-app.py <packageId> <ver>` — surgically updates the row's
   version/versionCode/file/sha256 after fetching the release asset it points at.
3. `./check.py`, then commit + push (the pre-push hook re-runs check.py).

## Before publishing: run `./check.py`

`apks.json` is the only thing users' stores read, and nothing else validates it. Every field in it
can drift from the APK it describes, and each way it has drifted shipped a real bug:

| check | what it caught |
|---|---|
| `sha` | a rebuilt APK left with the old hash — PandaApps verifies the download and refuses to install |
| `code` | Terminal IDE 0.2.4 shipped as versionCode 204 while the catalog said 213, so the store offered the same update forever |
| `name` | catalog version disagreeing with the APK's versionName (a `+sha` build suffix is allowed) |
| `convention` | versionCode off `minor*100 + patch`, which drifts below the convention until the first correct number is an unnstallable downgrade |
| `downgrade` | a versionCode at or below the published one — Android refuses it and says only "App not installed" |
| `missing` / `repo` / `signer` | a referenced APK absent from the repo, an entry with no source link, one of our APKs not on the Minima Family key |

```bash
./check.py        # failures only; non-zero exit means do not push
./check.py -v     # every entry
```

Takes ~6s over the whole catalog. A `pre-push` hook runs it automatically; it is not versioned, so
reinstall it in a fresh clone with:

```bash
cp hooks/pre-push .git/hooks/pre-push && chmod +x .git/hooks/pre-push
```

`git push --no-verify` bypasses it for a docs-only push.

**Exemptions** (in `check.py`): the upstream Minima builds — `org.minimarex.minimacore` (both Core
rows) and `org.minimarex.terminal` — are exempt from `convention` and `signer`, because we neither
number nor sign them and renumbering would break upgrades from an officially-installed build. Every
other check still applies to them.
