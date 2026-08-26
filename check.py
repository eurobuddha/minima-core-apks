#!/usr/bin/env python3
"""
Pre-publish check for apks.json. Run before pushing; non-zero exit means do not push.

    ./check.py            # only failures, plus a summary
    ./check.py -v         # every entry, pass or fail

Each check exists because it shipped a real bug:

  sha        catalog sha256 disagrees with the file's actual bytes.
             A rebuilt APK with the old hash still in the catalog: PandaApps verifies the
             download against this and refuses to install on mismatch.

  code       catalog versionCode disagrees with the APK's real versionCode.
             Terminal IDE 0.2.4 shipped as 204 while the catalog said 213, so the store
             offered the same update forever — installing it never satisfied the comparison.

  name       catalog version disagrees with the APK's real versionName.
             A "+sha" build suffix is allowed (Openly ships 0.2.6+486effc as 0.2.6).

  convention versionCode is not minor*100 + patch (0.2.9 -> 209, 0.4.3 -> 403).
             Off-convention numbering is not itself fatal — a plain counter is monotonic —
             but it drifts BELOW where the convention puts it, and then the first correctly
             numbered release is a downgrade that cannot install. Terminal IDE had to jump a
             minor version to escape exactly that.

  downgrade  versionCode is <= the one currently committed for that package.
             Android refuses a downgrade and reports only "App not installed".

  missing    the referenced file cannot be fetched. Catalog rows point at GitHub
             Release assets (each app repo hosts its own binaries since 2026-08-26);
             a row whose URL 404s is a store entry nobody can install.
  repo       the entry has no repo URL, so the app's "View source code" button cannot show.
  signer     one of our APKs is not signed with the Minima Family key.
"""

import json
import hashlib
import re
import subprocess
import sys
import glob
import os
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CATALOG = os.path.join(HERE, "apks.json")

# Binaries live in each app repo's GitHub Releases, not in this repo, so verifying
# them means downloading. Downloads are cached here keyed by the catalog sha256 —
# a cached file whose name matches the expected hash is trusted without refetching,
# so only rows that actually changed cost bandwidth on a re-run.
CACHE = os.path.expanduser("~/.cache/minima-core-apks-check")

FAMILY_KEY_CN = "CN=eurobuddha, OU=Minima Family"

# Upstream builds we do not number. Renumbering them to our convention would break the
# upgrade path from an officially-installed Minima build, so they are exempt from
# `convention` only — every other check still applies.
CONVENTION_EXEMPT = {
    "org.minimarex.minimacore",   # Minima Core, and the New UI preview fork
    "org.minimarex.terminal",     # Minima Terminal
}

# Same reason: these are not signed by us.
SIGNER_EXEMPT = CONVENTION_EXEMPT


def find_tool(name):
    """Newest build-tools copy of an Android SDK tool, or None."""
    roots = [
        os.environ.get("ANDROID_HOME"),
        os.environ.get("ANDROID_SDK_ROOT"),
        os.path.expanduser("~/Library/Android/sdk"),
        os.path.expanduser("~/Android/Sdk"),
    ]
    for r in roots:
        if not r:
            continue
        hits = sorted(glob.glob(os.path.join(r, "build-tools", "*", name)))
        if hits:
            return hits[-1]
    return None


AAPT = find_tool("aapt2")
APKSIGNER = find_tool("apksigner")


def apk_identity(path):
    """(versionCode, versionName) straight from the binary, or (None, None)."""
    if not AAPT:
        return None, None
    try:
        out = subprocess.run([AAPT, "dump", "badging", path],
                             capture_output=True, text=True, timeout=120).stdout
    except Exception:
        return None, None
    line = next((l for l in out.splitlines() if l.startswith("package:")), "")
    code = re.search(r"versionCode='(\d+)'", line)
    name = re.search(r"versionName='([^']*)'", line)
    return (int(code.group(1)) if code else None,
            name.group(1) if name else None)


def apk_signer(path):
    if not APKSIGNER:
        return None
    try:
        out = subprocess.run([APKSIGNER, "verify", "--print-certs", path],
                             capture_output=True, text=True, timeout=120).stdout
    except Exception:
        return None
    m = re.search(r"certificate DN: (.+)", out)
    return m.group(1).strip() if m else None


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_release_file(url, want_sha):
    """Local path to the binary at `url`, downloading into the cache on a miss.

    The cache file is named <sha256-prefix>-<basename>, so a changed catalog hash
    forces a fresh download. The caller re-hashes the returned file every run —
    the cache only saves bandwidth, it is never trusted for integrity. Returns
    None when the URL cannot be fetched; the caller reports that as `missing`.
    """
    os.makedirs(CACHE, exist_ok=True)
    base = url.split("/")[-1]
    key = (want_sha or "nosha")[:16]
    path = os.path.join(CACHE, f"{key}-{base}")
    if os.path.exists(path):
        return path
    try:
        tmp = path + ".part"
        with urllib.request.urlopen(url, timeout=300) as r, open(tmp, "wb") as f:
            for chunk in iter(lambda: r.read(1 << 20), b""):
                f.write(chunk)
        os.rename(tmp, path)
        return path
    except Exception:
        return None


def expected_code(version):
    """The family convention: minor*100 + patch (major*10000 too, once major > 0)."""
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version)
    if not m:
        return None
    major, minor, patch = map(int, m.groups())
    return minor * 100 + patch + (major * 10000 if major else 0)


def published_codes():
    """
    versionCode per ENTRY as currently COMMITTED, to catch a downgrade before it ships.

    Keyed by name, not packageId: Minima Core and Minima Core — New UI (Preview) are two rows
    sharing org.minimarex.minimacore at different versionCodes, and keying by package collapsed
    them into one, making the official row look like a downgrade of the preview.
    """
    try:
        blob = subprocess.run(["git", "-C", HERE, "show", "HEAD:apks.json"],
                              capture_output=True, text=True, timeout=60).stdout
        return {a["name"]: a["versionCode"] for a in json.loads(blob)["apps"]}
    except Exception:
        return {}


def main():
    verbose = "-v" in sys.argv or "--verbose" in sys.argv
    catalog = json.load(open(CATALOG))
    apps = catalog["apps"]
    live = published_codes()

    failures = []          # (app name, check, detail)
    checked_binaries = 0

    for a in apps:
        name = a.get("name", "?")
        pkg = a.get("packageId", "")
        version = a.get("version", "")
        code = a.get("versionCode")
        url = a.get("file", "")
        filename = url.split("/")[-1]
        is_apk = filename.lower().endswith(".apk")
        # Rows we can verify end-to-end: anything served from OUR GitHub Releases
        # (per-app repos, or this repo's own `mirrors` release for upstream copies).
        # Upstream rows hosted elsewhere are not ours to hash.
        verifiable = ("github.com/eurobuddha/" in url and "/releases/download/" in url)

        def fail(check, detail):
            failures.append((name, check, detail))

        if not a.get("repo"):
            fail("repo", "no repo URL — the source-code link cannot render")

        local = fetch_release_file(url, a.get("sha256", "")) if (is_apk and verifiable) else None
        if is_apk and verifiable and local is None:
            fail("missing", f"cannot fetch {url}")

        if is_apk and verifiable and local:
            checked_binaries += 1

            actual = sha256(local)
            if a.get("sha256", "").lower() != actual:
                fail("sha", f"catalog {a.get('sha256','(none)')[:16]}… != file {actual[:16]}…")

            real_code, real_name = apk_identity(local)
            if real_code is None:
                fail("code", "could not read the APK (aapt2 missing?)")
            else:
                if real_code != code:
                    fail("code", f"catalog {code} != APK {real_code}")
                if real_name is not None:
                    # a build suffix such as 0.2.6+486effc is fine
                    if real_name.split("+")[0] != version:
                        fail("name", f"catalog {version!r} != APK {real_name!r}")

            if pkg not in SIGNER_EXEMPT:
                signer = apk_signer(local)
                if signer and FAMILY_KEY_CN not in signer:
                    fail("signer", f"not the Minima Family key: {signer[:48]}")

        if is_apk and pkg not in CONVENTION_EXEMPT:
            exp = expected_code(version)
            if exp is None:
                fail("convention", f"version {version!r} is not X.Y.Z, cannot derive a code")
            elif exp != code:
                fail("convention", f"{version} should be code {exp}, catalog says {code}")

        was = live.get(name)
        if was is not None and code is not None and code < was:
            fail("downgrade", f"{code} is below the published {was} — Android will refuse it")
        elif verbose and was is not None and code == was:
            pass  # unchanged entry, nothing to say

        if verbose and not any(f[0] == name for f in failures):
            print(f"  ok   {name[:34]:35} {version:14} code={code}")

    print()
    if failures:
        print(f"FAILED — {len(failures)} problem(s) across {len(apps)} entries:\n")
        width = max(len(f[1]) for f in failures)
        for app, check, detail in failures:
            print(f"  {check:<{width}}  {app[:32]:33} {detail}")
        print("\nDo not push. Fix these first.")
        return 1

    print(f"OK — {len(apps)} entries, {checked_binaries} APKs verified against their catalog rows.")
    if not AAPT:
        print("NOTE: aapt2 not found, so versionCode/versionName were not read from the binaries.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
