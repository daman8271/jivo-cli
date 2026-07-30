#!/usr/bin/env python3
"""
scrub.py — G6 secret hygiene for the capture tree.

The live walk records the requests the app makes. Some of those carry secrets:
  - `authorization: Bearer <JWT>` headers
  - the ozone `refresh_token` body field ("<counter>.<session_id>", single-use)
  - `Abacus-Token` (the vendor lane's auth header)
  - presigned S3 query strings (X-Amz-Signature / X-Amz-Credential)
  - `x-signature` request-signing values
  - New Relic browser keys

G6 forbids any of those from reaching a capture file, a vault note, or a commit.
This script rewrites them to <redacted> IN PLACE and reports what it changed. Run
it after EVERY walk pull, before anything is read into a note.

Idempotent: running it twice is a no-op.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

PATTERNS = [
    # JWTs anywhere (header, body, localStorage dump)
    (re.compile(r'eyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}'),
     '<redacted:JWT>'),
    # ozone refresh token: "<counter>.<base64ish session id>"
    (re.compile(r'("refresh_token"\s*:\s*")[^"]+(")'), r'\1<redacted:refresh_token>\2'),
    (re.compile(r'("vendorRefreshToken"\s*:\s*")[^"]+(")'), r'\1<redacted>\2'),
    # auth headers in any casing.
    # NOTE the quote is matched INSIDE a group and put back: an earlier version used
    # `"?` outside the capture, which consumed the opening quote of a JSON value and
    # produced `"Abacus-Token":<redacted>"` — invalid JSON. That corrupted exactly one
    # capture file before it was caught by a validity sweep; both the pattern and the
    # file were fixed. Never let a redaction change the structure of the document.
    (re.compile(r'((?:authorization|abacus-token)"?\s*[:=]\s*"?)'
                r'(?:Bearer\s+)?[A-Za-z0-9._~+/=-]{20,}', re.I), r'\1<redacted>'),
    # request-signing value
    (re.compile(r'("?x-signature"?\s*[:=]\s*"?)[a-f0-9]{32,}', re.I), r'\1<redacted>'),
    # presigned S3
    (re.compile(r'(X-Amz-Signature=)[A-Za-z0-9%]+', re.I), r'\1<redacted>'),
    (re.compile(r'(X-Amz-Credential=)[^&"\s\\]+', re.I), r'\1<redacted>'),
    (re.compile(r'(X-Amz-Security-Token=)[^&"\s\\]+', re.I), r'\1<redacted>'),
    # telemetry keys
    (re.compile(r'(browser_monitoring_key=)[A-Za-z0-9]+'), r'\1<redacted>'),
    (re.compile(r'("NR_KEY"\s*:\s*")[^"]+(")'), r'\1<redacted>\2'),
    # OTP codes, just in case a login screen ever renders one
    (re.compile(r'("otp"\s*:\s*")\d{4,8}(")'), r'\1<redacted>\2'),
]

TEXT_EXT = {'.json', '.txt', '.har', '.md', '.tsv', '.log', '.html', '.js'}


def scrub_file(p):
    try:
        with open(p, encoding='utf-8', errors='replace') as f:
            s = f.read()
    except OSError:
        return 0
    orig = s
    n = 0
    for rx, rep in PATTERNS:
        s, k = rx.subn(rep, s)
        n += k
    if s != orig:
        with open(p, 'w', encoding='utf-8') as f:
            f.write(s)
    return n


def main(root=None):
    root = root or HERE
    total = 0
    touched = []
    for dp, _, fns in os.walk(root):
        for fn in fns:
            if os.path.splitext(fn)[1].lower() not in TEXT_EXT:
                continue
            p = os.path.join(dp, fn)
            if os.path.basename(p) == 'scrub.py':
                continue
            k = scrub_file(p)
            if k:
                total += k
                touched.append((os.path.relpath(p, root), k))
    print(f"scrubbed {total} secret occurrence(s) across {len(touched)} file(s)")
    for p, k in sorted(touched, key=lambda x: -x[1])[:40]:
        print(f"  {k:4d}  {p}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
