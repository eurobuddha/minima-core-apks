#!/usr/bin/env python3
"""Keep the Official "Minima Core" catalog row in sync with spartacusrex's latest build.

    scripts/sync-upstream-core.py [--push] [--dry-run]

spartacusrex publishes NO GitHub releases. His node app ships as a committed file
`dist/minima-<version>.apk` on spartacusrex-minima/minima-core-android, signed with
his own key (O=Minima, CN=Spartacus Rex). This catalog's "Minima Core" (source:
Official) row mirrors that file: we re-host the exact upstream APK on our own
`mirrors` release and point the row at it. Nothing pulls a new upstream version in
automatically, so the row drifts until someone bumps it by hand — which is what this
script (and the daily GitHub Action that runs it) exists to end.

What it does, in order — each gate fails loudly rather than shipping a bad row:

  1. List upstream dist/, pick the highest `minima-X.Y[.Z].apk` by semver.
  2. If the catalog already serves that version -> "up to date", exit 0. Never downgrade.
  3. Download the upstream APK.
  4. VERIFY before trusting it:
       - packageId == org.minimarex.minimacore
       - versionName == the version from the filename
       - versionCode > the versionCode the catalog currently serves
       - signer certificate SHA-256 == the PINNED Spartacus cert (the security gate:
         a different key means either a re-key or tampering, and an in-place update
         from a different key hard-fails on-device with "App not installed" anyway)
  5. Mirror it to our `mirrors` release (a version-named asset, so nothing is clobbered
     and the previous version stays for rollback); confirm it is fetchable and re-hashes.
  6. Surgically replace exactly four values in apks.json (version, versionCode, file,
     sha256) — the same edit publish-app.py makes, anchored on the row's unique file URL.
  7. Run check.py; a non-zero result aborts without committing.
  8. With --push: commit and push (catalog-only, no app version bump). The pre-push
     hook runs check.py again.

--dry-run does 1-4 (fetch + verify) and reports what WOULD change, touching nothing.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request

# check.py (repo root) already finds aapt2/apksigner and reads an APK's identity/hash —
# reuse it rather than duplicating the SDK-probing logic.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import check as checkmod

# --- what we track ----------------------------------------------------------------
UPSTREAM_REPO = "spartacusrex-minima/minima-core-android"
DIST_DIR = "dist"
ASSET_RE = re.compile(r"^minima-(\d+\.\d+(?:\.\d+)?)\.apk$")
PACKAGE_ID = "org.minimarex.minimacore"
ROW_NAME = "Minima Core"                 # the Official mirror row (NOT the fork "PandaBear")
MIRROR_REPO = "eurobuddha/minima-core-apks"
MIRROR_TAG = "mirrors"
# The Spartacus signing certificate. An upstream APK signed with anything else is
# refused: verified from minima-1.2.5.apk and minima-1.2.6.apk, both this cert.
PINNED_CERT_SHA256 = "d4b3901a73f55d00728fce1d5a9167f3f873b2e52d8361fe5ab2c86a89dbc7d1"

CATALOG = checkmod.CATALOG
HERE = checkmod.HERE


def die(msg):
    print(f"sync-upstream-core: {msg}", file=sys.stderr)
    sys.exit(1)


def gh_json(*args):
    out = subprocess.run(["gh", "api", *args], capture_output=True, text=True)
    if out.returncode != 0:
        die(f"gh api {' '.join(args)} failed: {out.stderr.strip()}")
    return json.loads(out.stdout)


def semver(v):
    parts = [int(x) for x in v.split(".")]
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def apk_cert_sha256(path):
    """Signer #1 certificate SHA-256 digest, lowercased, or None."""
    if not checkmod.APKSIGNER:
        return None
    try:
        out = subprocess.run([checkmod.APKSIGNER, "verify", "--print-certs", path],
                             capture_output=True, text=True, timeout=120).stdout
    except Exception:
        return None
    m = re.search(r"certificate SHA-256 digest:\s*([0-9a-fA-F]+)", out)
    return m.group(1).lower() if m else None


def main():
    push = "--push" in sys.argv
    dry = "--dry-run" in sys.argv
    if not checkmod.AAPT or not checkmod.APKSIGNER:
        die("aapt2/apksigner not found — set ANDROID_HOME to an SDK with build-tools installed")

    # --- 1. latest upstream version ------------------------------------------------
    listing = gh_json(f"repos/{UPSTREAM_REPO}/contents/{DIST_DIR}")
    versions = []
    for entry in listing:
        m = ASSET_RE.match(entry["name"])
        if m:
            versions.append(m.group(1))
    if not versions:
        die(f"no minima-*.apk found in {UPSTREAM_REPO}/{DIST_DIR}")
    latest = max(versions, key=semver)
    print(f"upstream latest: {latest}  (dist has: {', '.join(sorted(versions, key=semver))})")

    # --- 2. compare against the catalog row ---------------------------------------
    cat = json.loads(open(CATALOG).read())
    rows = [a for a in cat["apps"] if a["packageId"] == PACKAGE_ID and a["name"] == ROW_NAME]
    if len(rows) != 1:
        die(f"expected exactly one {ROW_NAME!r} row for {PACKAGE_ID}, found {len(rows)}")
    row = rows[0]
    cur_ver, cur_code = row["version"], row["versionCode"]
    print(f"catalog serves:  {cur_ver}  (versionCode {cur_code})")

    if semver(latest) == semver(cur_ver):
        print("up to date — nothing to do.")
        return 0
    if semver(latest) < semver(cur_ver):
        die(f"upstream {latest} is OLDER than the catalog's {cur_ver} — refusing to downgrade")

    # --- 3. download upstream ------------------------------------------------------
    new_base = f"minima-{latest}.apk"
    raw_url = f"https://github.com/{UPSTREAM_REPO}/raw/main/{DIST_DIR}/{new_base}"
    tmpdir = tempfile.mkdtemp(prefix="sync-upstream-core-")
    apk = os.path.join(tmpdir, new_base)
    print(f"downloading {raw_url}")
    try:
        with urllib.request.urlopen(raw_url, timeout=300) as r, open(apk, "wb") as f:
            for chunk in iter(lambda: r.read(1 << 20), b""):
                f.write(chunk)
    except Exception as e:
        die(f"cannot download upstream APK: {e}")

    # --- 4. verify -----------------------------------------------------------------
    real_code, real_name = checkmod.apk_identity(apk)
    cert = apk_cert_sha256(apk)
    new_sha = checkmod.sha256(apk)
    print(f"  package     {PACKAGE_ID} (expected)")
    print(f"  versionName {real_name}")
    print(f"  versionCode {real_code}")
    print(f"  cert sha256 {cert}")
    print(f"  apk  sha256 {new_sha}")

    badging_pkg = subprocess.run([checkmod.AAPT, "dump", "badging", apk],
                                 capture_output=True, text=True).stdout
    if f"name='{PACKAGE_ID}'" not in badging_pkg:
        die(f"APK package is not {PACKAGE_ID}")
    if real_name is None or real_name.split("+")[0] != latest:
        die(f"APK versionName {real_name!r} != dist version {latest!r}")
    if real_code is None or real_code <= cur_code:
        die(f"APK versionCode {real_code} is not above the catalog's {cur_code}")
    if cert != PINNED_CERT_SHA256:
        die(f"SIGNER MISMATCH — cert {cert} != pinned {PINNED_CERT_SHA256}. "
            f"Refusing: this is either an upstream re-key or a tampered file. "
            f"If spartacusrex genuinely rotated keys, update PINNED_CERT_SHA256 by hand "
            f"after confirming the new cert out-of-band.")
    print("verified: matches the pinned Spartacus cert and is a real upgrade.")

    if dry:
        print(f"\n--dry-run: WOULD mirror {new_base} and bump {ROW_NAME} "
              f"{cur_ver} (code {cur_code}) -> {latest} (code {real_code}).")
        return 0

    # --- 5. mirror to our releases -------------------------------------------------
    print(f"uploading {new_base} to {MIRROR_REPO} release {MIRROR_TAG} …")
    up = subprocess.run(["gh", "release", "upload", MIRROR_TAG, apk, "--repo", MIRROR_REPO],
                        capture_output=True, text=True)
    if up.returncode != 0:
        die(f"gh release upload failed: {up.stderr.strip()}")
    new_url = f"https://github.com/{MIRROR_REPO}/releases/download/{MIRROR_TAG}/{new_base}"
    check_dl = checkmod.fetch_release_file(new_url, new_sha)
    if check_dl is None or checkmod.sha256(check_dl) != new_sha:
        die(f"mirrored asset at {new_url} is not fetchable or its hash does not match")
    print(f"mirrored + verified: {new_url}")

    # --- 6. surgical catalog edit (version, versionCode, file, sha256) -------------
    src = open(CATALOG).read()
    old_url = row["file"]
    edits = [
        ("version", row["version"], latest),
        ("versionCode", row["versionCode"], real_code),
        ("file", old_url, new_url),
        ("sha256", row.get("sha256", ""), new_sha),
    ]
    for key, old_val, new_val in edits:
        needle = f'"{key}": {json.dumps(old_val)}'
        repl = f'"{key}": {json.dumps(new_val)}'
        if key in ("file", "sha256"):        # globally unique — must be exactly one
            if src.count(needle) != 1:
                die(f"{needle!r} occurs {src.count(needle)}x — aborting to avoid a wrong edit")
            src = src.replace(needle, repl)
        else:                                 # version/code repeat across rows: edit within this row only
            anchor = json.dumps(old_url if key != "file" else new_url)
            row_at = src.index(anchor)
            obj_start = src.rindex("{", 0, row_at)
            obj_end = src.index("}", row_at)
            chunk = src[obj_start:obj_end]
            if chunk.count(needle) != 1:
                die(f"{needle!r} occurs {chunk.count(needle)}x in the row — aborting")
            src = src[:obj_start] + chunk.replace(needle, repl) + src[obj_end:]
    open(CATALOG, "w").write(src)
    print(f"catalog: {ROW_NAME} {cur_ver} -> {latest} (code {real_code})")

    # --- 7. gate -------------------------------------------------------------------
    if checkmod.main() != 0:
        die("check.py FAILED after the edit — not committing. The working tree carries the change.")

    # --- 8. commit + push ----------------------------------------------------------
    if not push:
        print("\ncheck.py green. Not pushing (no --push). Review, then commit.")
        return 0

    changelog = os.path.join(HERE, "CHANGELOG.md")
    if os.path.exists(changelog):
        import datetime
        today = datetime.date.today().isoformat()
        cl = open(changelog).read()
        entry = (f"- {today} · catalog — Official **Minima Core** mirror {cur_ver} -> **{latest}** "
                 f"(upstream Spartacus-signed build, versionCode {real_code}), synced automatically "
                 f"from {UPSTREAM_REPO}/{DIST_DIR}/{new_base}. Same signing cert "
                 f"(SHA-256 {PINNED_CERT_SHA256}); APK sha256 {new_sha}. Catalog-only.\n")
        cl = cl.replace("# Changelog\n\n", f"# Changelog\n\n{entry}", 1)
        open(changelog, "w").write(cl)

    subprocess.run(["git", "-C", HERE, "add", "apks.json", "CHANGELOG.md"], check=True)
    msg = (f"catalog — auto-sync Official Minima Core mirror {cur_ver} -> {latest} "
           f"(upstream Spartacus build)\n\n"
           f"Detected {new_base} in {UPSTREAM_REPO}/{DIST_DIR}. Verified versionName "
           f"{latest}, versionCode {real_code}, package {PACKAGE_ID}, signer cert "
           f"SHA-256 {PINNED_CERT_SHA256} (pinned Spartacus key). Mirrored to the "
           f"{MIRROR_TAG} release; APK sha256 {new_sha}. check.py green.\n\n"
           f"Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>")
    subprocess.run(["git", "-C", HERE, "commit", "-m", msg], check=True)
    subprocess.run(["git", "-C", HERE, "push"], check=True)
    print("pushed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
