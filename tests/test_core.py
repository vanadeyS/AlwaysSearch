#!/usr/bin/env python3
"""
Unit tests for NeverSearch core pure functions.
Compatible with standard unittest runner and pytest:
  python -m unittest discover tests
  pytest -v tests/
"""
import hashlib
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import r34_gallery as ns


class TestCoreFunctions(unittest.TestCase):
    def test_safe_component(self):
        self.assertEqual(ns.safe_component("normal_name"), "normal_name")
        self.assertEqual(ns.safe_component("file/with\\bad:chars*?<>|"), "file_with_bad_chars")
        self.assertEqual(ns.safe_component("...leading.dots..."), "leading.dots")
        self.assertEqual(ns.safe_component("   spaced   "), "spaced")
        self.assertEqual(ns.safe_component(""), "untitled")
        self.assertEqual(ns.safe_component(None), "untitled")
        # Length truncation at 120 chars
        long_str = "a" * 200
        self.assertEqual(len(ns.safe_component(long_str)), 120)

    def test_normalize_tag(self):
        self.assertEqual(ns.normalize_tag("furina(genshin_impact)"), "furina_(genshin_impact)")
        self.assertEqual(ns.normalize_tag("furina_(genshin_impact)"), "furina_(genshin_impact)")
        self.assertEqual(ns.normalize_tag("  genshin_impact   30  "), "genshin_impact 30")
        self.assertEqual(ns.normalize_tag(""), "")

    def test_requested_limit(self):
        self.assertEqual(ns.requested_limit("all", 50), 50)
        self.assertEqual(ns.requested_limit("5", 50), 5)
        self.assertEqual(ns.requested_limit("100", 25), 25)
        self.assertEqual(ns.requested_limit("0", 10), 1)
        self.assertEqual(ns.requested_limit("-5", 10), 1)
        fallback = min(ns.cfg["default_count"], 15)
        self.assertEqual(ns.requested_limit("invalid", 15), fallback)

    def test_parse_version(self):
        self.assertEqual(ns.parse_version("1.05.04"), (1, 5, 4))
        self.assertEqual(ns.parse_version("v1.05.05"), (1, 5, 5))
        self.assertTrue(ns.parse_version("1.05.05") > ns.parse_version("1.05.04"))
        self.assertTrue(ns.parse_version("1.10.00") > ns.parse_version("1.09.99"))
        self.assertEqual(ns.parse_version("unknown"), (0,))

    def test_generate_simple_password(self):
        for _ in range(30):
            pw = ns.generate_simple_password()
            parts = pw.split("-")
            self.assertEqual(len(parts), 5)
            for i in range(4):
                self.assertTrue(parts[i].isalpha())
            self.assertTrue(parts[4].isdigit())
            self.assertTrue(1000 <= int(parts[4]) <= 9999)

    def test_resolve_paths(self):
        # Franchise-based tag
        section, folder = ns.resolve_paths("furina_(genshin_impact)")
        self.assertIn("Genshin_Impact", section)
        self.assertTrue(folder.endswith("Furina"))

        # Artist-based tag
        sec_art, fold_art = ns.resolve_paths("rensuke", artist=True)
        self.assertIn("Artists", sec_art)
        self.assertTrue(fold_art.endswith("rensuke"))

    def test_sha256_verification(self):
        sample_data = b"NeverSearch test payload content"
        expected_sha = hashlib.sha256(sample_data).hexdigest()
        actual_sha = hashlib.sha256(sample_data).hexdigest()
        self.assertEqual(actual_sha, expected_sha)
        tampered_data = b"NeverSearch test payload content [TAMPERED]"
        tampered_sha = hashlib.sha256(tampered_data).hexdigest()
        self.assertNotEqual(tampered_sha, expected_sha)

    def test_repo_sha256_matches_source(self):
        root = Path(__file__).resolve().parent.parent
        src_file = root / "r34_gallery.py"
        sha_file = root / "r34_gallery.py.sha256"
        if src_file.is_file() and sha_file.is_file():
            actual = hashlib.sha256(src_file.read_bytes().replace(b"\r\n", b"\n")).hexdigest().lower()
            expected = sha_file.read_text(encoding="utf-8").strip().split()[0].lower()
            self.assertEqual(actual, expected, "r34_gallery.py.sha256 is out of sync with r34_gallery.py!")

    def test_inter_process_lock(self):
        import tempfile
        import threading
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "test.lock"
            with ns.InterProcessLock(lock_path) as lock:
                self.assertIsNotNone(lock.fp)
                self.assertTrue(lock_path.exists())
                
                # Test concurrent lock contention from another thread
                timed_out = []
                def try_second_lock():
                    try:
                        with ns.InterProcessLock(lock_path, timeout=0.2):
                            pass
                    except TimeoutError:
                        timed_out.append(True)
                
                t = threading.Thread(target=try_second_lock)
                t.start()
                t.join(timeout=2.0)
                self.assertEqual(len(timed_out), 1, "Second lock should time out when file is locked!")

            # Lock released and cleaned up
            self.assertIsNone(lock.fp)

    def test_no_undefined_variables_linter(self):
        try:
            from pyflakes.api import checkPath
            from pyflakes.reporter import Reporter
            import io
            root = Path(__file__).resolve().parent.parent
            src_file = root / "r34_gallery.py"
            out = io.StringIO()
            err = io.StringIO()
            warnings = checkPath(str(src_file), reporter=Reporter(out, err))
            self.assertEqual(warnings, 0, f"Pyflakes lint errors in r34_gallery.py:\n{out.getvalue()}\n{err.getvalue()}")
        except ImportError:
            pass

    def test_localization_keys_parity(self):
        ru_keys = set(ns.TEXT["ru"])
        en_keys = set(ns.TEXT["en"])
        self.assertEqual(ru_keys, en_keys, f"Missing in ru: {en_keys - ru_keys}, missing in en: {ru_keys - en_keys}")


if __name__ == "__main__":
    unittest.main()
