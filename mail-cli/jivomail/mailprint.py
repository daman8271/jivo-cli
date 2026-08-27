"""Render one mail thread to PDF — the paper an outgoing payment carries.

The approval mail IS the authorisation for a vendor payment (correction C-0028),
so it has to reach SAP as a document, not as a quote in a chat. This module turns
a fetched MailMessage into a Gmail-print-alike PDF using headless Chrome, which
is the same shape as the prints already sitting on JIVO's posted payments
(e.g. "Jivo Wellness Mail - Payment to ASHOK KITAB GHAR (BFYPK7430L) 3.8.pdf").

Read-only with respect to the mailbox: it only ever renders what was fetched.
"""
from __future__ import annotations

import os

import html as _html
import shutil
import subprocess
import time
import tempfile
from pathlib import Path

# Windows first when we are on Windows: the operator boxes are Windows, and the
# absolute-path probe below only recognised POSIX paths, so a box with Chrome
# sitting in Program Files still reported "no Chrome found" (DESKTOP-EQ55Q8H,
# 2026-08-25). Edge is listed too — every Windows box has it even when Chrome
# is missing, and it is Chromium, so --headless --print-to-pdf behaves the same.
_WINDOWS_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "chrome",
    "msedge",
]

_POSIX_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "google-chrome",
    "chromium",
    "chromium-browser",
]

CHROME_CANDIDATES = (
    _WINDOWS_CANDIDATES if os.name == "nt" else _POSIX_CANDIDATES
)

_CSS = """
@page { size: A4; margin: 14mm 12mm; }
body { font-family: Arial, "Helvetica Neue", Helvetica, sans-serif;
       font-size: 11pt; color: #202124; line-height: 1.45; }
.hdr { border-bottom: 2px solid #dadce0; padding-bottom: 10px; margin-bottom: 16px; }
.brand { font-size: 9pt; color: #5f6368; letter-spacing: .04em; text-transform: uppercase; }
h1 { font-size: 15pt; margin: 6px 0 10px; font-weight: 600; }
table.meta { font-size: 9.5pt; color: #5f6368; border-collapse: collapse; }
table.meta td { padding: 1px 10px 1px 0; vertical-align: top; }
table.meta td.k { color: #80868b; white-space: nowrap; }
.body { font-size: 10.5pt; }
.body img { max-width: 100%; height: auto; }
.body table { border-collapse: collapse; max-width: 100%; }
.body td, .body th { border: 1px solid #dadce0; padding: 3px 6px; font-size: 9.5pt; }
.body blockquote, .gmail_quote {
    border-left: 2px solid #dadce0; margin: 10px 0 10px 4px; padding-left: 12px; color: #5f6368; }
pre.plain { white-space: pre-wrap; word-wrap: break-word; font-family: inherit; margin: 0; }
.att { margin-top: 18px; padding-top: 8px; border-top: 1px solid #dadce0;
       font-size: 9pt; color: #5f6368; }
"""


def find_chrome() -> str | None:
    for c in CHROME_CANDIDATES:
        # An absolute path is checked directly; a bare name goes through PATH.
        # os.path.isabs is what makes this work on both platforms — the old
        # c.startswith("/") test silently skipped every "C:\..." candidate.
        if os.path.isabs(c):
            if Path(c).exists():
                return c
            continue
        found = shutil.which(c)
        if found:
            return found
    return None


def build_html(msg) -> str:
    """Wrap the message in the print layout. Prefers the real HTML part."""
    if msg.body_html.strip():
        inner = msg.body_html
        # Strip a full document wrapper so our own <head>/CSS wins.
        low = inner.lower()
        if "<body" in low:
            inner = inner[low.index("<body"):]
            inner = inner[inner.index(">") + 1:]
            if "</body" in inner.lower():
                inner = inner[: inner.lower().rindex("</body")]
        body_block = f'<div class="body">{inner}</div>'
    else:
        body_block = ('<div class="body"><pre class="plain">'
                      f"{_html.escape(msg.body_text)}</pre></div>")

    rows = [("From", msg.sender), ("To", msg.to), ("Date", msg.date)]
    meta = "".join(
        f'<tr><td class="k">{k}</td><td>{_html.escape(v or "")}</td></tr>' for k, v in rows
    )
    att = ""
    if msg.attachments:
        names = ", ".join(_html.escape(a.filename) for a in msg.attachments)
        att = f'<div class="att">Attachments in this mail: {names}</div>'

    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<style>{_CSS}</style></head><body>"
        '<div class="hdr"><div class="brand">Jivo Wellness Mail</div>'
        f"<h1>{_html.escape(msg.subject or '(no subject)')}</h1>"
        f'<table class="meta">{meta}</table></div>'
        f"{body_block}{att}</body></html>"
    )


def render_pdf(msg, out_path: Path, chrome: str | None = None,
               timeout: int = 45) -> Path:
    """Render msg to out_path as PDF. Raises RuntimeError if Chrome is absent."""
    chrome = chrome or find_chrome()
    if not chrome:
        raise RuntimeError(
            "no Chrome/Chromium found to render the mail PDF — install one, or "
            "print the thread from Gmail and pass the file with --file"
        )
    out_path = Path(out_path).expanduser()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "mail.html"
        src.write_text(build_html(msg), encoding="utf-8")
        cmd = [
            chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
            "--no-first-run", "--no-default-browser-check", "--disable-extensions",
            f"--user-data-dir={td}/profile",
            "--no-pdf-header-footer",
            "--virtual-time-budget=10000",
            f"--print-to-pdf={out_path}",
            src.as_uri(),
        ]
        # Chrome writes the PDF and then sometimes lingers instead of exiting.
        # The file is what matters, so time-box the process and judge the result
        # by the artefact on disk, not by the exit code.
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Chrome writes the PDF and then sometimes lingers instead of exiting, so
        # judge the run by the artefact: poll until the file stops growing, then
        # stop waiting. The exit code is not the signal here.
        deadline, last, stable = time.time() + timeout, -1, 0
        while time.time() < deadline:
            if proc.poll() is not None:
                break
            size = out_path.stat().st_size if out_path.exists() else 0
            if size and size == last:
                stable += 1
                if stable >= 2:
                    break
            else:
                stable = 0
            last = size
            time.sleep(0.25)
        if proc.poll() is None:
            proc.kill()
        _, err = proc.communicate()
    if not out_path.exists() or out_path.stat().st_size == 0:
        raise RuntimeError(
            f"Chrome produced no PDF: {err.decode('utf-8', 'replace')[-400:]}"
        )
    return out_path
