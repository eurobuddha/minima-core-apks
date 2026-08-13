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

  missing    the referenced file is not in the repo (catalog-hosted files only).
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

HERE = os.path.dirname(os.path.abspath(__file__))
CATALOG = os.path.join(HERE, "apks.json")

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
        filename = a.get("file", "").split("/")[-1]
        local = os.path.join(HERE, filename)
        is_apk = filename.lower().endswith(".apk")
        # Files served from someone else's repo or a GitHub Release are not ours to hash.
        hosted_here = "raw.githubusercontent.com/eurobuddha/minima-core-apks" in a.get("file", "")

        def fail(check, detail):
            failures.append((name, check, detail))

        if not a.get("repo"):
            fail("repo", "no repo URL — the source-code link cannot render")

        if is_apk and hosted_here and not os.path.exists(local):
            fail("missing", f"{filename} is not in the repo")

        if is_apk and hosted_here and os.path.exists(local):
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
