# PandaApps catalog (minima-core-apks)

The **manifest** of the PandaApps native Android store: `apks.json` + the app icons.
This repo hosts **no binaries in git** — every APK, dmg and installer is a GitHub
Release asset on its own app's repository, and each catalog row's `file` field
points straight at that release asset:

```
https://github.com/eurobuddha/<app-repo>/releases/download/v<version>/<file>
```

Consumers of `apks.json` (all URL-driven, all follow redirects):

- **PandaApps** (the on-phone store, [minima-core-android-pandaapps](https://github.com/eurobuddha/minima-core-android-pandaapps)) — fetches the catalog via the GitHub API with raw-CDN and IPFS fallbacks, downloads the `file` URL and refuses to install on a sha256 mismatch.
- **minimaCore App Store** ([minimacore-appstore](https://github.com/eurobuddha/minimacore-appstore)) — MDS MiniDapp mirroring this catalog into MiniHub; downloads via the node.
- **IPFS mirror** — `build_ipfs_store.sh` (in [dappstore](https://github.com/eurobuddha/dappstore)) snapshots the catalog and every referenced binary to IPFS hourly, so the store works if GitHub is unreachable.

Two special releases on **this** repo hold binaries that have no home of their own:
`mirrors` (upstream Minima Core APKs by spartacusrex, which publishes no releases)
and the historical `miniMall-Studio-v0.1.1` (superseded by
[minimall-core](https://github.com/eurobuddha/minimall-core)'s own releases).

> ⚠️ **All apps here are in active development — use at your own risk.** They are experimental software provided **AS IS**, without warranty of any kind. They interact with a live blockchain and real funds; despite testing, bugs may exist. Back up your seed, test with small amounts, and only risk what you can afford to lose. Nothing here is financial advice.

## Publishing a new app version

```bash
# 1. In the app's own repo: tag + release with the APK attached
gh release create v0.4.3 app-release.apk --repo eurobuddha/<app-repo> \
    --title "<App> 0.4.3" --notes "<one line: what changed>"

# 2. In this repo: update the catalog row and verify end-to-end
scripts/publish-app.py <packageId> 0.4.3        # edits version/versionCode/file/sha256
./check.py                                      # downloads + verifies every row
git commit -am "<App> 0.4.3" && git push
```

`scripts/publish-app.py` does step 2 surgically (never rewrites the whole JSON) and
computes the sha256 from the release asset it just verified.

## Verification

`./check.py` is the gate — it downloads every catalog binary (cached in
`~/.cache/minima-core-apks-check`) and checks sha256, versionCode/versionName
(via aapt2), the Minima Family signing key, version-code convention
(`minor*100 + patch`), and downgrade protection against the committed catalog.
The `pre-push` hook runs it automatically; reinstall in a fresh clone with:

```bash
cp hooks/pre-push .git/hooks/pre-push && chmod +x .git/hooks/pre-push
```

## History

Until 2026-08-26 this repo carried every APK ever shipped inside git (13 GB
working tree). All of them were migrated to per-app GitHub Releases — current
versions onto their real `v<version>` tags, tagless historical builds onto each
repo's `apk-archive` pre-release — and the git history was rewritten to remove
the binaries. Old raw.githubusercontent URLs into this repo are gone; the
release URLs are permanent.

**License:** the catalog itself (`apks.json`, docs, icons) is [MIT](LICENSE) © 2026 eurobuddha. The distributed `.apk` files are release builds of their respective apps and carry those apps' own licenses (which include Apache-2.0 Minima components).
