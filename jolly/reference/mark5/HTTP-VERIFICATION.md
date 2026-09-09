# MARK V public HTTP verification

Checked 10 September 2026, 02:58:19 IST (9 September 21:28:19 UTC), against
`https://mark5.srv1685505.hstgr.cloud` from the VPS through its public HTTPS name.
Confidence: high for these observed responses. This is a ten-request sample,
not a geographically representative performance benchmark.

| Check | Observed result |
|---|---|
| Ten unauthenticated `GET /v1/dashboard` requests | All HTTP 200 |
| Response body size | 200,362 bytes on all ten reads |
| Read latency | Minimum 20.720 ms; median 22.839 ms; nearest-rank p95 / maximum 133.948 ms |
| Dashboard `If-None-Match` with returned ETag | HTTP 304 |
| Valid HMAC-signed, timestamped `source_changed` event to `/v1/events` | HTTP 202 |
| Identical event ID and raw body delivered again | HTTP 202, exactly the same job ID |
| Event with invalid signature | HTTP 401 |
| Unsigned `POST /v1/refresh` | HTTP 401 |

The valid event requested one authorized source refresh. Its job was **running**
when checked; this report does not claim refresh completion. No approval request,
factory submission, production-document mutation or browser interaction occurred.

HMAC was calculated over `timestamp + "." + raw_body` with SHA-256. Secrets
were read solely inside VPS Python from `/root/mark5/private/service.env` and
were never printed, written to evidence or copied locally. Evidence excludes
request authentication headers and signatures.

Sanitized full evidence, including individual timings and the shared job ID:
VPS `/root/mark5-build/evidence/http-release.json`.
The separate synthetic browser fixture on port 8876 was untouched.
