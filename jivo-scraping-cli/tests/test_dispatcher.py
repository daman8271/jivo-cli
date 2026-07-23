"""Dispatcher regression tests: broken-pipe exit 0, clean bad-arg exits, root env."""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = os.path.join(HERE, "..", "bin", "jivo-scrape")
ALIAS = os.path.join(HERE, "..", "bin", "jivo-desk")


class TestDispatcher(unittest.TestCase):
    def test_broken_pipe_exits_zero_and_silent(self):
        """Early-exiting reader (| head) must yield exit 0 with no stderr noise."""
        p = subprocess.Popen(
            [sys.executable, BIN, "files"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        p.stdout.close()  # simulate the downstream reader hanging up immediately
        p.wait()
        stderr = p.stderr.read().decode()
        self.assertEqual(p.returncode, 0, f"stderr was: {stderr}")
        self.assertNotIn("BrokenPipeError", stderr)

    def test_bad_date_exits_2_with_clean_message(self):
        out = subprocess.run(
            [sys.executable, BIN, "today", "--date", "garbage"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(out.returncode, 2)
        self.assertIn("bad argument", out.stderr)
        self.assertNotIn("Traceback", out.stderr)

    def test_alias_entrypoint_still_works(self):
        out = subprocess.run(
            [sys.executable, ALIAS, "--version"], capture_output=True, text=True
        )
        self.assertEqual(out.returncode, 0)
        self.assertIn("jivo-scrape", out.stdout)

    def test_show_directory_exits_3_no_traceback(self):
        """`vault --show <dir>` maps IsADirectoryError to a clean exit 3."""
        tmp = tempfile.mkdtemp(prefix="jivo-disp-")
        try:
            os.makedirs(os.path.join(tmp, "vault", "daily"))
            env = dict(os.environ, JIVO_SCRAPE_ROOT=tmp)
            out = subprocess.run(
                [sys.executable, BIN, "vault", "--show", "daily"],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(out.returncode, 3)
            self.assertNotIn("Traceback", out.stderr)
            self.assertIn("directory", out.stderr)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_root_env_is_respected(self):
        """JIVO_SCRAPE_ROOT must redirect every data path to the given checkout."""
        env = dict(os.environ, JIVO_SCRAPE_ROOT="/nonexistent-godown-xyz")
        out = subprocess.run(
            [sys.executable, BIN, "doctor", "--json"],
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertIn("/nonexistent-godown-xyz", out.stdout)


if __name__ == "__main__":
    unittest.main()
