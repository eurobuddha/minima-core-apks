import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('catalog_check', ROOT / 'check.py')
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


class CatalogIdentityTests(unittest.TestCase):
    def validate(self, package, signer=None, **overrides):
        row = dict(name='Minima Core PandaBear', packageId='com.eurobuddha.minimacore',
                   version='1.9.4-PandaBear', versionCode=75,
                   file='https://github.com/eurobuddha/minima-core-android/releases/download/v1.9.4-PandaBear/core-1.9.4.apk',
                   repo='https://github.com/eurobuddha/minima-core-android', sha256='verified-hash')
        row.update(overrides)
        with tempfile.TemporaryDirectory() as directory, contextlib.ExitStack() as stack:
            catalog = Path(directory) / 'apks.json'
            catalog.write_text(json.dumps({'apps': [row]}))
            for name, value in [('CATALOG', str(catalog)), ('AAPT', 'aapt2')]:
                stack.enter_context(patch.object(check, name, value))
            for name, value in [('published_codes', {}), ('fetch_release_file', 'fixture.apk'),
                                ('sha256', row['sha256']), ('apk_identity', (row['versionCode'], row['version'])),
                                ('apk_package', package), ('apk_signer', signer if signer is not None else check.FAMILY_CERT_SHA256)]:
                stack.enter_context(patch.object(check, name, return_value=value))
            output = io.StringIO()
            stack.enter_context(contextlib.redirect_stdout(output))
            return check.main(), output.getvalue()

    def test_matching_family_identity_passes(self):
        code, output = self.validate('com.eurobuddha.minimacore')
        self.assertEqual(0, code, output)

    def test_wrong_or_unreadable_package_cannot_be_listed(self):
        for package in ('com.example.unrelated', None):
            with self.subTest(package=package):
                code, output = self.validate(package)
                self.assertEqual(1, code)
                self.assertIn('package', output)

    def test_family_core_cannot_bypass_signer_check(self):
        code, output = self.validate('com.eurobuddha.minimacore', 'CN=Wrong publisher')
        self.assertEqual(1, code)
        self.assertIn('signer', output)

    def test_exact_historical_artifact_keeps_its_counter(self):
        digest = next(iter(check.HISTORICAL_COUNTER_SHA256))
        code, output = self.validate('com.example.historical', packageId='com.example.historical',
                                     sha256=digest, version='1.7.4-PandaBear', versionCode=69)
        self.assertEqual(0, code, output)

    def test_changed_historical_artifact_gets_no_counter_exception(self):
        code, output = self.validate('com.example.historical', packageId='com.example.historical',
                                     sha256='new-artifact', version='1.7.4-PandaBear', versionCode=69)
        self.assertEqual(1, code)
        self.assertIn('convention', output)

    def test_family_name_cannot_impersonate_the_signing_key(self):
        code, output = self.validate('com.eurobuddha.minimacore', check.FAMILY_KEY_CN)
        self.assertEqual(1, code)
        self.assertIn('signer', output)
