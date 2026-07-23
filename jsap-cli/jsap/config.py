"""JSAP CLI configuration — reads credentials from the project .env.

READ-ONLY LAW: this file only reads credentials; it never writes to JSAP.
"""

from __future__ import annotations

import os
from pathlib import Path

# Walk up from this file to find the repo root that holds .env
_HERE = Path(__file__).resolve()
_REPO_ROOT = _HERE.parents[3]  # jsap/ -> jsap-cli/ -> CLI/ -> repo root
_ENV_PATH = _REPO_ROOT / ".env"

# Where we cache the session cookie (our own store — allowed by the law).
STATE_DIR = Path(os.environ.get("JSAP_STATE_DIR", Path.home() / ".jsap"))
COOKIE_FILE = STATE_DIR / "session.json"

DEFAULTS = {
    "JSAP_URL": "http://103.89.45.75:5001",
    "JSAP_USERNAME": "",
    "JSAP_PASSWORD": "",
    "JSAP_USER_ID": "68",
}


def _parse_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        out[key.strip()] = val.strip().strip('"').strip("'")
    return out


class Config:
    def __init__(self) -> None:
        env = _parse_env(_ENV_PATH)

        def pick(key: str) -> str:
            return os.environ.get(key) or env.get(key) or DEFAULTS.get(key, "")

        self.base_url = pick("JSAP_URL").rstrip("/")
        self.username = pick("JSAP_USERNAME")
        self.password = pick("JSAP_PASSWORD")
        self.user_id = int(pick("JSAP_USER_ID") or 68)
        # Two companies live behind this login.
        self.companies = {1: "JIVO OIL", 2: "JIVO BEVERAGE"}

    def require_creds(self) -> None:
        missing = [
            k
            for k, v in (
                ("JSAP_USERNAME", self.username),
                ("JSAP_PASSWORD", self.password),
            )
            if not v
        ]
        if missing:
            raise SystemExit(
                f"Missing {', '.join(missing)} — set them in {_ENV_PATH} or the environment."
            )


CONFIG = Config()
