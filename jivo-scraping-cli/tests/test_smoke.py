"""Smoke: dispatcher loads every command and --help works."""

import os
import subprocess
import sys

BIN = os.path.join(os.path.dirname(__file__), "..", "bin", "jivo-desk")


def test_help():
    out = subprocess.run(
        [sys.executable, BIN, "--help"], capture_output=True, text=True
    )
    assert out.returncode == 0 and "price" in out.stdout and "product" in out.stdout


if __name__ == "__main__":
    test_help()
    print("smoke OK")
