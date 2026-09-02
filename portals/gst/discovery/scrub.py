#!/usr/bin/env python3
"""Scrub a raw capture for use as a tracked test fixture: keeps keys/types/shape, replaces
GSTINs, ARNs, names, phones, emails, addresses and passwords with synthetic values.
usage: scrub.py IN.json OUT.json"""
import json, re, sys
GSTIN = re.compile(r'\b\d{2}[A-Z]{5}\d{4}[A-Z][A-Z\d]Z[A-Z\d]\b')
ARN = re.compile(r'\b[A-Z]{2}\d{12}[A-Z\d]\b')
EMAIL = re.compile(r'[\w.+-]+@[\w-]+\.[\w.]+')
PHONE = re.compile(r'\b[6-9]\d{9}\b')
NAMEKEYS = {'filedBy', 'auth_name', 'name', 'trdnm', 'tradeNam', 'lgnm', 'bname', 'ln', 'tn', 'bn', 'regName'}
# Redact by KEY NAME, not just by value pattern: a secret that does not look like a
# GSTIN/ARN (a password, a captcha answer, the device fingerprint, a session cookie)
# is invisible to the regexes below. Deny-by-key is the layer that catches those.
DROPKEYS = {'password', 'user_pass', 'pwd', 'passwd', 'captcha', 'mFP', 'mFP_parsed',
            'deviceID', 'AuthToken', 'authtoken', 'Cookie', 'cookie', 'set-cookie',
            'username', 'user_name', 'mobNum', 'email', 'adr', 'pradr', 'contacted', 'mbr'}
# Document identifiers: keep the type and rough shape, lose the counterparty's
# real invoice/reference number (a supplier's invoice series is business data).
# Matched case-insensitively: the cash ledger spells the same field both ref_no
# and refNo, and a case-sensitive check let real CIN/CPIN challan references
# through into cli/testdata on 2026-08-21.
DOCKEYS = {'inum', 'ref_no', 'refno', 'irn', 'chksum', 'cin', 'cpin',
           'nt_num', 'doc_num', 'referenceno', 'reference_no', 'arn'}
# Same keys, lowercased, for case-insensitive matching.
DROPKEYS_LC = {k.lower() for k in DROPKEYS}
DOCKEYS_LC = {k.lower() for k in DOCKEYS}
NAMEKEYS_LC = {k.lower() for k in NAMEKEYS}
def gstin_sub(m):
    s = m.group(0); return s[:2] + 'AAAAA0000A' + s[12:]
def walk(v, key=None):
    if isinstance(v, dict):
        return {k: ('<scrubbed>' if k.lower() in DROPKEYS_LC else walk(x, k)) for k, x in v.items()}
    if isinstance(v, list):
        return [walk(x, key) for x in v]
    if isinstance(v, str):
        if key and key.lower() in NAMEKEYS_LC: return 'TEST NAME'
        if key and key.lower() in DOCKEYS_LC: return 'TESTDOC/0001'
        v = GSTIN.sub(gstin_sub, v); v = ARN.sub(lambda m: 'AA' + '0' * 12 + 'X', v)
        v = EMAIL.sub('test@example.com', v); v = PHONE.sub('9000000000', v)
        return v
    if isinstance(v, int) and key in {'mobNum'}: return 9000000000
    return v
if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    raw = open(src).read()
    try: data = json.loads(raw)
    except json.JSONDecodeError:
        # .rec.json dumps may contain stringified bodies; scrub as text
        txt = PHONE.sub('9000000000', EMAIL.sub('test@example.com', ARN.sub('AA000000000000X', GSTIN.sub(gstin_sub, raw))))
        for k in DROPKEYS:
            txt = re.sub(r'("%s"\s*:\s*)"(?:[^"\\]|\\.)*"' % re.escape(k), r'\1"<scrubbed>"', txt, flags=re.I)
        open(dst, 'w').write(txt); sys.exit()
    json.dump(walk(data), open(dst, 'w'), indent=1, ensure_ascii=False)
