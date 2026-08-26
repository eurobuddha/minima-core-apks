#!/usr/bin/env python3
"""Update one catalog row after a new version has been released in the app's repo.

    scripts/publish-app.py <packageId> <version> [--name "<row name>"]

Steps, in order — each one fails loudly rather than half-updating the catalog:

  1. Find the catalog row by packageId (use --name when two rows share a package,
     e.g. the two org.minimarex.minimacore rows).
  2. Build the new release-asset URL from the row's `repo` field and the new
     version, keeping the same filename pattern as the current row
     (everything before the version stays; only the version changes).
  3. Download that asset NOW — publishing a row nobody can fetch is the failure
     mode this script exists to prevent — and compute its sha256.
  4. Surgically replace exactly four values in apks.json (version, versionCode,
     file, sha256) with count==1 asserts. The whole file is never re-serialized:
     a full json.dump reindents all ~500 lines and buries the real diff.
  5. Remind you to run ./check.py (the pre-push hook runs it anyway).

versionCode follows the family convention minor*100 + patch (+ major*10000),
matching check.py's `convention` check.
"""
import json
import hashlib
import re
import sys

# check.py (same repo root) already knows how to find aapt2 and read an APK's real
# versionCode/versionName — reuse it rather than duplicating the SDK-probing logic.
sys.path.insert(0, __file__.rsplit('/', 2)[0])
import check as checkmod

CATALOG = __file__.rsplit('/', 2)[0] + '/apks.json'


def die(msg):
    print(f"publish-app: {msg}", file=sys.stderr)
    sys.exit(1)


args = [a for a in sys.argv[1:] if not a.startswith('--')]
name_filter = None
if '--name' in sys.argv:
    name_filter = sys.argv[sys.argv.index('--name') + 1]
if len(args) != 2:
    die(__doc__.strip().splitlines()[2].strip())
pkg, version = args

src = open(CATALOG).read()
cat = json.loads(src)
rows = [a for a in cat['apps'] if a['packageId'] == pkg
        and (name_filter is None or a['name'] == name_filter)]
if not rows:
    die(f"no catalog row for packageId {pkg}" + (f" name {name_filter!r}" if name_filter else ""))
if len(rows) > 1:
    die(f"{len(rows)} rows share packageId {pkg} — disambiguate with --name "
        + " / ".join(repr(r['name']) for r in rows))
row = rows[0]

# New URL: same repo, same filename shape, new version. The old file URL is the
# template — swapping the version string in the basename keeps naming consistent
# (AtomiX-0.1.43.apk -> AtomiX-0.1.44.apk) without hardcoding per-app patterns.
old_url = row['file']
old_base = old_url.split('/')[-1]
if row['version'] not in old_base:
    die(f"cannot derive filename: {row['version']!r} not in {old_base!r}")
new_base = old_base.replace(row['version'], version)
repo = row['repo'].split('github.com/')[1].rstrip('/')
new_url = f"https://github.com/{repo}/releases/download/v{version}/{new_base}"

print(f"fetching {new_url} …")
local = checkmod.fetch_release_file(new_url, "")
if local is None:
    die("release asset not fetchable — create the release first")
h = hashlib.sha256()
with open(local, 'rb') as f:
    for chunk in iter(lambda: f.read(1 << 20), b''):
        h.update(chunk)
new_sha = h.hexdigest()

m = re.match(r'^(\d+)\.(\d+)\.(\d+)$', version)
if not m:
    die(f"version {version!r} is not X.Y.Z")
major, minor, patch = map(int, m.groups())
convention_code = minor * 100 + patch + (major * 10000 if major else 0)

# The APK itself is the authority on versionCode — convention-exempt apps
# (org.minimarex.*, see check.py CONVENTION_EXEMPT) use a plain counter, and
# writing the convention number for them would trip check.py's `code` check.
real_code, real_name = checkmod.apk_identity(local) if new_base.endswith('.apk') else (None, None)
new_code = real_code if real_code is not None else convention_code
if real_code is not None and real_code != convention_code and pkg not in checkmod.CONVENTION_EXEMPT:
    die(f"APK versionCode {real_code} breaks the convention ({convention_code} expected "
        f"for {version}) — fix the app's build.gradle before publishing")
if real_name is not None and real_name.split('+')[0] != version:
    die(f"APK versionName {real_name!r} does not match requested version {version!r}")

# Surgical replacement: each needle is the full JSON-encoded "key": value pair of
# THIS row, so identical values on other rows can never be touched by accident.
for key, old_val, new_val in [
    ('version', row['version'], version),
    ('versionCode', row['versionCode'], new_code),
    ('file', old_url, new_url),
    ('sha256', row.get('sha256', ''), new_sha),
]:
    needle = f'"{key}": {json.dumps(old_val)}'
    repl = f'"{key}": {json.dumps(new_val)}'
    n = src.count(needle)
    if key in ('file', 'sha256'):        # globally unique values — must be exactly one
        assert n == 1, f"{needle!r} occurs {n}x"
        src = src.replace(needle, repl)
    else:
        # version/versionCode values repeat across rows; anchor on this row's
        # unique file URL by editing only within the row's JSON object.
        row_start = src.index(json.dumps(old_url if key != 'file' else new_url))
        obj_start = src.rindex('{', 0, row_start)
        obj_end = src.index('}', row_start)
        chunk = src[obj_start:obj_end]
        assert chunk.count(needle) == 1, f"{needle!r} occurs {chunk.count(needle)}x in row"
        src = src[:obj_start] + chunk.replace(needle, repl) + src[obj_end:]

open(CATALOG, 'w').write(src)
print(f"updated {row['name']}: {row['version']} -> {version} (code {new_code})")
print(f"  file   {new_url}")
print(f"  sha256 {new_sha}")
print("now run ./check.py and commit.")
