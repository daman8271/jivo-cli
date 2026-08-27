"""Configuration for jmail — read from the repo-root .env, never from argv.

Credentials live in <repo-root>/.env, which .gitignore blocks (this repo is
public). Nothing here ever prints a secret.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def repo_root(start: Path | None = None) -> Path:
    """Walk up from this file until we find the checkout root (.git or CLAUDE.md)."""
    p = (start or Path(__file__).resolve()).parent
    for cand in [p, *p.parents]:
        if (cand / ".git").exists() or (cand / "CLAUDE.md").exists():
            return cand
    return Path.cwd()


def load_env(path: Path) -> dict[str, str]:
    """Minimal .env reader: KEY=VALUE, # comments, optional surrounding quotes."""
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for raw in path.read_text(errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        out[key] = val
    return out


@dataclass(frozen=True)
class MailConfig:
    user: str
    password: str
    imap_host: str
    imap_port: int

    @property
    def redacted(self) -> str:
        return "*" * 8

    def missing(self) -> list[str]:
        miss = []
        if not self.user:
            miss.append("ZOHO_MAIL_USER")
        if not self.password:
            miss.append("ZOHO_MAIL_APP_PASSWORD")
        if not self.imap_host:
            miss.append("ZOHO_MAIL_IMAP_HOST")
        return miss


def load_config() -> tuple[MailConfig, Path]:
    """Environment wins over .env, so a one-off run can override without editing the file."""
    root = repo_root()
    env_path = root / ".env"
    env = load_env(env_path)

    def get(key: str, default: str = "") -> str:
        return os.environ.get(key) or env.get(key, default)

    cfg = MailConfig(
        user=get("ZOHO_MAIL_USER"),
        password=get("ZOHO_MAIL_APP_PASSWORD"),
        imap_host=get("ZOHO_MAIL_IMAP_HOST", "imap.zoho.in"),
        imap_port=int(get("ZOHO_MAIL_IMAP_PORT", "993") or 993),
    )
    return cfg, env_path
