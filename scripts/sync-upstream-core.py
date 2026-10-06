#!/usr/bin/env python3
"""Keep the Official "Minima Core" catalog row in sync with spartacusrex's latest build.

    scripts/sync-upstream-core.py [--push] [--dry-run]

spartacusrex publishes NO GitHub releases. His node app ships as a committed file
`dist/minima-<version>.apk` on spartacusrex-minima/minima-core-android, signed with
the pinned Minima Global key. This catalog's "Minima Core" (source:
Official) row mirrors that file: we re-host the exact upstream APK on our own
`mirrors` release and point the row at it. The hourly GitHub Action runs this script automatically.

What it does, in order — each gate fails loudly rather than shipping a bad row:

  1. List upstream dist/, pick the highest `minima-X.Y[.Z].apk` by semver.
  2. Never downgrade; verify unchanged versions too, refusing replaced APKs.
  3. Download the upstream APK.
  4. VERIFY before trusting it:
       - packageId == org.minima.core
       - versionName == the version from the filename
       - versionCode increases for a new version; unchanged builds match code and hash
       - signer certificate SHA-256 == the PINNED Minima Global cert (the security gate:
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
PACKAGE_ID = "org.minima.core"
ROW_NAME = "Minima Core"                 # the Official mirror row (NOT the fork "PandaBear")
MIRROR_REPO = "eurobuddha/minima-core-apks"
MIRROR_TAG = "mirrors"
# Shared with the store validator: a new signer requires explicit review.
PINNED_CERT_SHA256 = checkmod.OFFICIAL_CORE_CERT_SHA256

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
    return checkmod.apk_signer(path, certificate_digest=True)


def download(url, path):
    with urllib.request.urlopen(url, timeout=300) as response, open(path, "wb") as output:
        for chunk in iter(lambda: response.read(1 << 20), b""):
            output.write(chunk)


def ensure_mirror(apk, new_sha, tmpdir):
    """Reuse an identical asset after an interrupted run; never overwrite one."""
    new_base = os.path.basename(apk)
    release = gh_json(f"repos/{MIRROR_REPO}/releases/tags/{MIRROR_TAG}")
    existing = [a for a in release["assets"] if a["name"] == new_base]
    if not existing:
        up = subprocess.run(["gh", "release", "upload", MIRROR_TAG, apk, "--repo", MIRROR_REPO],
                            capture_output=True, text=True)
        if up.returncode != 0:
            die(f"gh release upload failed: {up.stderr.strip()}")
    new_url = f"https://github.com/{MIRROR_REPO}/releases/download/{MIRROR_TAG}/{new_base}"
    mirror = os.path.join(tmpdir, "mirror.apk")
    download(new_url, mirror)  # fresh readback, not a previously cached asset
    if checkmod.sha256(mirror) != new_sha:
        die("mirrored asset hash differs from upstream; refusing to overwrite or publish it")
    return new_url


def main():
    push = "--push" in sys.argv
    dry = "--dry-run" in sys.argv
    if not checkmod.AAPT or not checkmod.APKSIGNER:
        die("aapt2/apksigner not found — set ANDROID_HOME to an SDK with build-tools installed")

    if push and not dry:
        for args in (["diff", "--quiet"], ["diff", "--cached", "--quiet"]):
            if subprocess.run(["git", "-C", HERE, *args]).returncode != 0:
                die("--push requires a clean tracked working tree and index")

    # --- 1. latest upstream version ------------------------------------------------
    revision = gh_json(f"repos/{UPSTREAM_REPO}/commits/main")["sha"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        die("invalid upstream commit SHA")
    listing = gh_json(f"repos/{UPSTREAM_REPO}/contents/{DIST_DIR}?ref={revision}")
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

    if semver(latest) < semver(cur_ver):
        die(f"upstream {latest} is OLDER than the catalog's {cur_ver} — refusing to downgrade")

    # --- 3. download upstream ------------------------------------------------------
    new_base = f"minima-{latest}.apk"
    raw_url = f"https://raw.githubusercontent.com/{UPSTREAM_REPO}/{revision}/{DIST_DIR}/{new_base}"
    tmpdir = tempfile.mkdtemp(prefix="sync-upstream-core-")
    import atexit
    import shutil
    atexit.register(shutil.rmtree, tmpdir, ignore_errors=True)
    apk = os.path.join(tmpdir, new_base)
    print(f"downloading {raw_url}")
    try:
        download(raw_url, apk)
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

    badging = subprocess.run([checkmod.AAPT, "dump", "badging", apk],
                             capture_output=True, text=True, timeout=120)
    package = re.search(r"^package: name='([^']+)'", badging.stdout, re.MULTILINE)
    if badging.returncode != 0 or not package or package.group(1) != PACKAGE_ID:
        die(f"APK package is not {PACKAGE_ID}")
    if real_name is None or real_name.split("+")[0] != latest:
        die(f"APK versionName {real_name!r} != dist version {latest!r}")
    unchanged = semver(latest) == semver(cur_ver)
    if real_code is None or (real_code != cur_code if unchanged else real_code <= cur_code):
        die(f"APK versionCode {real_code} is not a valid upgrade from {cur_code}")
    if cert != PINNED_CERT_SHA256:
        die(f"SIGNER MISMATCH — cert {cert} != pinned {PINNED_CERT_SHA256}. "
            f"Refusing: this is either an upstream re-key or a tampered file. "
            f"If spartacusrex genuinely rotated keys, update check.py OFFICIAL_CORE_CERT_SHA256 by hand "
            f"after confirming the new cert out-of-band.")
    print("verified: matches the pinned Minima Global cert and expected package/version.")

    if unchanged:
        if new_sha != row.get("sha256"):
            die("upstream replaced an already published version; manual review required")
        print("up to date — upstream APK verified; nothing to do.")
        return 0

    if dry:
        print(f"\n--dry-run: WOULD mirror {new_base} and bump {ROW_NAME} "
              f"{cur_ver} (code {cur_code}) -> {latest} (code {real_code}).")
        return 0

    # --- 5. mirror to our releases -------------------------------------------------
    print(f"uploading {new_base} to {MIRROR_REPO} release {MIRROR_TAG} …")
    new_url = ensure_mirror(apk, new_sha, tmpdir)
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
                 f"(upstream Minima Global-signed build, versionCode {real_code}), synced automatically "
                 f"from {UPSTREAM_REPO}/{DIST_DIR}/{new_base} at {revision}. Same signing cert "
                 f"(SHA-256 {PINNED_CERT_SHA256}); APK sha256 {new_sha}. Catalog-only.\n")
        cl = cl.replace("# Changelog\n\n", f"# Changelog\n\n{entry}", 1)
        open(changelog, "w").write(cl)

    subprocess.run(["git", "-C", HERE, "add", "apks.json", "CHANGELOG.md"], check=True)
    msg = (f"catalog — auto-sync Official Minima Core mirror {cur_ver} -> {latest} "
           f"(upstream Minima Global build)\n\n"
           f"Detected {new_base} in {UPSTREAM_REPO}/{DIST_DIR}. Verified versionName "
           f"{latest}, versionCode {real_code}, package {PACKAGE_ID}, signer cert "
           f"SHA-256 {PINNED_CERT_SHA256} (pinned Minima Global key). Mirrored to the "
           f"{MIRROR_TAG} release; APK sha256 {new_sha}. Upstream {revision}. check.py green.")
    subprocess.run(["git", "-C", HERE, "commit", "-m", msg], check=True)
    subprocess.run(["git", "-C", HERE, "push", "origin", "HEAD:main"], check=True)
    print("pushed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
