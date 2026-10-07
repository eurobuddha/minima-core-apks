import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sync_core', ROOT / 'scripts/sync-upstream-core.py')
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.catalog = self.root / 'apks.json'
        self.original = json.loads((ROOT / 'apks.json').read_text())
        self.catalog.write_text(json.dumps(self.original, indent=2) + '\n')
        self.latest = '1.8'
        self.code = 33
        self.package = 'org.minima.core'
        self.cert = sync.PINNED_CERT_SHA256
        self.existing = False
        self.mismatch = False
        self.downloads = []
        self.commands = []
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        self.stack.enter_context(contextlib.redirect_stderr(io.StringIO()))
        for target, name, value in [(sync, 'CATALOG', str(self.catalog)), (sync, 'HERE', str(self.root)),
                                    (sync.checkmod, 'AAPT', 'aapt2'), (sync.checkmod, 'APKSIGNER', 'apksigner')]:
            self.stack.enter_context(patch.object(target, name, value))
        self.stack.enter_context(patch.object(sync, 'gh_json', side_effect=self.api))
        self.stack.enter_context(patch.object(sync, 'download', side_effect=self.download))
        self.stack.enter_context(patch.object(sync.checkmod, 'apk_identity', side_effect=lambda _: (self.code, self.latest)))
        self.stack.enter_context(patch.object(sync.checkmod, 'apk_signer', side_effect=lambda *a, **kw: self.cert))
        self.gate = self.stack.enter_context(patch.object(sync.checkmod, 'main', return_value=0))
        self.stack.enter_context(patch.object(sync.subprocess, 'run', side_effect=self.run_command))
        self.stack.enter_context(patch.object(sync.sys, 'argv', ['sync-upstream-core.py']))

    def api(self, endpoint):
        if '/commits/' in endpoint:
            return {'sha': 'a' * 40}
        if '/contents/' in endpoint:
            self.assertIn('?ref=' + 'a' * 40, endpoint)
            return [{'name': 'minima-' + self.latest + '.apk'}]
        if '/releases/' in endpoint:
            return {'assets': [{'name': 'minima-' + self.latest + '.apk'}] if self.existing else []}
        self.fail(endpoint)

    def download(self, url, path):
        self.downloads.append(url)
        Path(path).write_bytes(b'wrong' if self.mismatch and '/releases/' in url else b'verified apk')

    def run_command(self, args, **kwargs):
        self.commands.append(args)
        output = "package: name='%s' versionCode='%s' versionName='%s'\n" % (self.package, self.code, self.latest)
        return subprocess.CompletedProcess(args, 0, output if args[0] == 'aapt2' else '', '')

    def official(self):
        return next(a for a in json.loads(self.catalog.read_text())['apps'] if a['name'] == 'Minima Core')

    def assert_not_published(self):
        self.assertEqual(json.loads(self.catalog.read_text()), self.original)
        self.assertFalse(any(c[:3] == ['gh', 'release', 'upload'] for c in self.commands))

    def test_new_release_changes_only_official_row(self):
        self.assertEqual(sync.main(), 0)
        updated = json.loads(self.catalog.read_text())
        self.assertEqual([r for r in updated['apps'] if r['name'] != 'Minima Core'],
                         [r for r in self.original['apps'] if r['name'] != 'Minima Core'])
        self.assertEqual(self.official()['version'], '1.8')
        self.assertEqual(self.official()['versionCode'], 33)
        self.assertIn('/' + 'a' * 40 + '/dist/', self.downloads[0])
        self.gate.assert_called_once()

    def test_dry_run_cannot_upload_or_edit(self):
        with patch.object(sync.sys, 'argv', ['sync', '--push', '--dry-run']):
            self.assertEqual(sync.main(), 0)
        self.assert_not_published()

    def test_existing_identical_asset_is_retryable(self):
        self.existing = True
        self.assertEqual(sync.main(), 0)
        self.assertFalse(any(c[:3] == ['gh', 'release', 'upload'] for c in self.commands))
        self.assertEqual(self.official()['version'], '1.8')

    def test_existing_conflicting_asset_is_never_overwritten(self):
        self.existing = self.mismatch = True
        with self.assertRaises(SystemExit): sync.main()
        self.assert_not_published()

    def test_same_version_verified_noop(self):
        self.latest, self.code = '1.7', 32
        row = next(r for r in self.original['apps'] if r['name'] == 'Minima Core')
        import hashlib
        row['sha256'] = hashlib.sha256(b'verified apk').hexdigest()
        self.catalog.write_text(json.dumps(self.original))
        self.assertEqual(sync.main(), 0)
        self.assert_not_published()
        self.assertEqual(len(self.downloads), 1)

    def test_same_version_replacement_is_refused(self):
        self.latest, self.code = '1.7', 32
        with self.assertRaises(SystemExit): sync.main()
        self.assert_not_published()

    def test_wrong_or_missing_signer_is_refused(self):
        for self.cert in ('0' * 64, None):
            with self.subTest(cert=self.cert), self.assertRaises(SystemExit): sync.main()
        self.assert_not_published()

    def test_wrong_package_is_refused(self):
        self.package = 'com.eurobuddha.minimacore'
        with self.assertRaises(SystemExit): sync.main()
        self.assert_not_published()

    def test_nonincreasing_code_is_refused(self):
        self.code = 32
        with self.assertRaises(SystemExit): sync.main()
        self.assert_not_published()

    def test_older_upstream_refused_without_download(self):
        self.latest = '1.6'
        with self.assertRaises(SystemExit): sync.main()
        self.assert_not_published()
        self.assertFalse(self.downloads)

    def test_catalog_validation_failure_cannot_commit(self):
        self.gate.return_value = 1
        with patch.object(sync.sys, 'argv', ['sync', '--push']), self.assertRaises(SystemExit): sync.main()
        self.assertFalse(any('commit' in c or 'push' in c for c in self.commands))

    def test_dirty_index_cannot_be_committed(self):
        with patch.object(sync.sys, 'argv', ['sync', '--push']), patch.object(sync.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1)):
            with self.assertRaises(SystemExit): sync.main()
        self.assert_not_published()
        self.assertFalse(self.downloads)

    def test_successful_push_stages_only_catalog_and_changelog(self):
        (self.root / 'CHANGELOG.md').write_text('# Changelog\n\n')
        with patch.object(sync.sys, 'argv', ['sync', '--push']):
            self.assertEqual(sync.main(), 0)
        self.assertIn(['git', '-C', str(self.root), 'add', 'apks.json', 'CHANGELOG.md'], self.commands)
        self.assertIn(['git', '-C', str(self.root), 'push', 'origin', 'HEAD:main'], self.commands)
        self.assertIn('a' * 40, (self.root / 'CHANGELOG.md').read_text())

    def test_version_name_mismatch_is_refused(self):
        with patch.object(sync.checkmod, 'apk_identity', return_value=(33, '9.9')):
            with self.assertRaises(SystemExit): sync.main()
        self.assert_not_published()

    def test_invalid_apk_signature_exit_is_refused(self):
        # Test the shared real signature parser, not the mock used by main's fixtures.
        self.stack.close()
        with patch.object(sync.checkmod, 'APKSIGNER', 'apksigner'), patch.object(sync.checkmod.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, 'certificate SHA-256 digest: ' + sync.PINNED_CERT_SHA256)):
            self.assertIsNone(sync.apk_cert_sha256('bad.apk'))


if __name__ == '__main__':
    unittest.main()
