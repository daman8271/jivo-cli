"""IMAP access for jmail — READ ONLY, enforced in one place.

HARD RULE: this module opens every mailbox with EXAMINE (readonly=True) and
fetches with BODY.PEEK[], so reading a message never sets \\Seen on the live
mailbox. There is deliberately no code path here that stores flags, appends,
moves, expunges or deletes. Sending mail is not implemented at all.
"""
from __future__ import annotations

import email
import imaplib
import re
import socket
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.header import decode_header, make_header
from email.message import Message

from .config import MailConfig

# Anything that could mutate the mailbox. Kept as a tripwire: if a future edit
# reaches for one of these, the guard test fails loudly instead of silently
# changing somebody's live inbox.
FORBIDDEN_IMAP_VERBS = frozenset(
    {"store", "uid_store", "append", "expunge", "copy", "move", "delete", "rename", "create"}
)

DEFAULT_TIMEOUT = 60


def decode(value: str | None) -> str:
    """RFC 2047 header decode that never raises on malformed input."""
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


@dataclass
class Attachment:
    filename: str
    content_type: str
    size: int
    part_index: int


@dataclass
class MailMessage:
    uid: str
    folder: str
    date: str
    sender: str
    to: str
    subject: str
    message_id: str
    attachments: list[Attachment] = field(default_factory=list)
    body_text: str = ""
    body_html: str = ""
    raw: bytes = b""

    @property
    def pdfs(self) -> list[Attachment]:
        return [a for a in self.attachments if a.filename.lower().endswith(".pdf")]


class ReadOnlyIMAP:
    """Thin wrapper over imaplib that only ever reads."""

    def __init__(self, cfg: MailConfig, timeout: int = DEFAULT_TIMEOUT):
        self.cfg = cfg
        self.timeout = timeout
        self._conn: imaplib.IMAP4_SSL | None = None
        self._folder: str | None = None

    def connect(self) -> None:
        socket.setdefaulttimeout(self.timeout)
        self._conn = imaplib.IMAP4_SSL(self.cfg.imap_host, self.cfg.imap_port)
        self._conn.login(self.cfg.user, self.cfg.password)

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.logout()
            except Exception:
                pass
            self._conn = None

    @property
    def conn(self) -> imaplib.IMAP4_SSL:
        if self._conn is None:
            raise RuntimeError("not connected — call connect() first")
        return self._conn

    def folders(self) -> list[str]:
        typ, data = self.conn.list()
        if typ != "OK":
            return []
        names = []
        for row in data:
            if not row:
                continue
            text = row.decode(errors="replace")
            m = re.match(r'\([^)]*\)\s+"[^"]*"\s+"?([^"]+)"?$', text.strip())
            names.append(m.group(1) if m else text)
        return names

    def select(self, folder: str = "INBOX") -> int:
        """EXAMINE, never SELECT — the mailbox stays read-only for this session."""
        typ, data = self.conn.select(f'"{folder}"', readonly=True)
        if typ != "OK":
            raise RuntimeError(f"cannot open folder {folder!r}: {data}")
        self._folder = folder
        return int(data[0])

    def search(
        self,
        sender: str | None = None,
        subject: str | None = None,
        since: str | None = None,
        before: str | None = None,
        text: str | None = None,
        unseen: bool = False,
    ) -> list[str]:
        crit: list[str] = []
        if sender:
            crit += ["FROM", f'"{sender}"']
        if subject:
            crit += ["SUBJECT", f'"{subject}"']
        if text:
            crit += ["TEXT", f'"{text}"']
        if since:
            crit += ["SINCE", _imap_date(since)]
        if before:
            crit += ["BEFORE", _imap_date(before)]
        if unseen:
            crit += ["UNSEEN"]
        if not crit:
            crit = ["ALL"]
        typ, data = self.conn.search(None, *crit)
        if typ != "OK" or not data or not data[0]:
            return []
        return [b.decode() for b in data[0].split()]

    def fetch(self, uid: str, peek: bool = True) -> MailMessage:
        """BODY.PEEK[] keeps \\Seen untouched even on servers that ignore EXAMINE."""
        item = "(BODY.PEEK[])" if peek else "(RFC822)"
        typ, data = self.conn.fetch(uid, item)
        if typ != "OK" or not data or not isinstance(data[0], tuple):
            raise RuntimeError(f"cannot fetch message {uid}")
        raw = data[0][1]
        return parse_message(raw, uid=uid, folder=self._folder or "INBOX")


def parse_message(raw: bytes, uid: str, folder: str) -> MailMessage:
    msg: Message = email.message_from_bytes(raw)
    atts: list[Attachment] = []
    body = ""
    html = ""
    for idx, part in enumerate(msg.walk()):
        if part.is_multipart():
            continue
        disp = str(part.get("Content-Disposition") or "")
        fname = decode(part.get_filename())
        ctype = part.get_content_type()
        if fname or "attachment" in disp.lower():
            payload = part.get_payload(decode=True) or b""
            atts.append(
                Attachment(
                    filename=fname or f"(unnamed).{ctype.split('/')[-1]}",
                    content_type=ctype,
                    size=len(payload),
                    part_index=idx,
                )
            )
        elif ctype == "text/plain" and not body:
            payload = part.get_payload(decode=True) or b""
            body = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        elif ctype == "text/html" and not html:
            payload = part.get_payload(decode=True) or b""
            html = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
    return MailMessage(
        uid=uid,
        folder=folder,
        date=decode(msg.get("Date")),
        sender=decode(msg.get("From")),
        to=decode(msg.get("To")),
        subject=decode(msg.get("Subject")),
        message_id=(msg.get("Message-ID") or "").strip(),
        attachments=atts,
        body_text=body,
        body_html=html,
        raw=raw,
    )


def attachment_bytes(raw: bytes, part_index: int) -> bytes:
    msg = email.message_from_bytes(raw)
    for idx, part in enumerate(msg.walk()):
        if idx == part_index:
            return part.get_payload(decode=True) or b""
    return b""


def _imap_date(value: str) -> str:
    """Accept YYYY-MM-DD or a plain day count like '30d'."""
    v = value.strip()
    m = re.fullmatch(r"(\d+)\s*d", v, re.I)
    if m:
        dt = datetime.now() - timedelta(days=int(m.group(1)))
    else:
        dt = datetime.strptime(v, "%Y-%m-%d")
    return dt.strftime("%d-%b-%Y")


@contextmanager
def session(cfg: MailConfig, folder: str | None = "INBOX", timeout: int = DEFAULT_TIMEOUT):
    client = ReadOnlyIMAP(cfg, timeout=timeout)
    client.connect()
    try:
        if folder:
            client.select(folder)
        yield client
    finally:
        client.close()
