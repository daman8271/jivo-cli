---
tags: [tankhapay, meta, auth, source-of-truth]
---
# TankhaPay — Auth & Access

> **PROVEN live 2026-07-25** against `business.tankhapay.com`. Headless login works with no
> browser and no cookies. One JWT authorizes all four backends.

## The model: bearer token, no cookies

There are **no session cookies** (the Cookie-Editor screenshot confirmed "This page does not have
any cookies"). The SPA stores the whole login response in `localStorage.activeUser` and an HTTP
interceptor attaches the token to every request:

```js
const Dt = localStorage.getItem("activeUser");
if (Dt) {
  let kt = JSON.parse(Dt).token;
  s = s.clone({ setHeaders: { Authorization: `Bearer ${kt}` } });   // every API call
}
```
(Exception: the `employeeLoginByMob` punch endpoint uses `Authorization: Basic base64("tppunch_usr:TPm5q9EF2024")` — irrelevant to the business CLI.)

## Login flow (email + password) — verified

Endpoint: `POST https://business.tankhapay.com/api/login`
Body (before AES): built by the login component as
```json
{
  "email": "shunty@jivo.in",
  "password": "<md5(plaintextPassword) lowercase hex>",
  "recaptchaToken": "",
  "localhost": true,
  "action": "check_login_by_emailid1"
}
```
then AES-128-ECB encrypted and wrapped: `{"encrypted": "<base64 ciphertext>"}` (see [[Encryption-Scheme]]).

Verified facts:
- **Password is MD5-hashed client-side** (`hashStr` = ts-md5 `onePassHasher`; self-test
  `md5("hello")=5d41402a…` confirms standard MD5). `md5("Jivo@9891")=1efecc803a5f94e5d5f7c0e297b116fa`.
- **reCAPTCHA v3 is bypassed** by sending `localhost:true` with `recaptchaToken:""`. The app only
  runs reCAPTCHA when `hostname != localhost/staging`; the server honors the `localhost` flag. **No
  browser needed.** (Site key `6LfBzAgpAAAAAL61hNQkprJ6_015ZG3sTzoYvlUo` is therefore not needed.)
- **`action` must be `check_login_by_emailid1`** for this email account. (`check_login_by_emailid`
  returned "credentials do not match"; the `…id1` variant succeeded. The app picks the variant by
  regex-matching the identifier; for our login use `…id1`.)
- On success the server returns `{"status":"True", "token": "<JWT>", "email_id", "name", "role"(enc),
  "user_id"(enc), "menuhtml", "product_type", ...}`. Failure: `{"status":"False","msg":"…"}` (HTTP 200 either way).

## The JWT

- 3-part `HS256` JWT. Header/signature standard. **Payload** = `{ data:"<AES-ECB blob>", iat, exp, aud[], iss }`.
- `exp - iat = 86400` → **token lives 24h**. No refresh token → **re-login daily**.
- `aud` = `[business, pms, ats, tnd].tankhapay.com` → **one token, all backends** (business + mobapi
  reads accept it; pms/ats/tnd are sibling apps).
- `data` decrypts (AES-128-ECB, same key `0123456789abcdef`) to the full user context:
  `tp_account_id=2719`, `geo_location_id=37`, `ouIds="37,2211,38,40,31,1925"`, `user_type=Business`,
  `userid=shunty@jivo.in`, `emp_code=10000001`, plus role/permission/company fields. **The CLI decodes
  this to fill `accountId`/`geo_location_id`/`ouIds` in read payloads.**
- `role` and `user_id` top-level fields are *also* AES-ECB blobs (role→"2", user_id→"13784").

## Daily headless login (what the CLI does)
1. Read `TPAY_USERNAME`/`TPAY_PASSWORD` from `.env`.
2. `md5(password)` → build the login JSON above → AES-ECB encrypt → `POST /api/login`.
3. On `status:"True"`, save `token` to `.token` (0600, gitignored) with its `exp`.
4. Decode the JWT `data` for account context; cache it alongside the token.
5. Every read: `Authorization: Bearer <token>`, body `{"encrypted": …}`, decrypt `commonData`.
6. If a call 401s or the token is within minutes of `exp`, re-login automatically.

Credentials live only in `.env` (gitignored, 0600). Never printed, never committed, never in the vault.

See [[Encryption-Scheme]] · [[Backends-and-Environment]] · [[Read-Only-Guardrails]] · [[Proven-Login-Recipe]]
