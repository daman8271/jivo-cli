---
tags: [tankhapay, meta, crypto, source-of-truth]
---
# TankhaPay — Request/Response Encryption Scheme

> **This is the crown jewel of the whole study.** Every real API call on the TankhaPay
> Business portal is AES-encrypted at the body level. Reproduce this exactly and the CLI
> can talk to the API directly, with no browser. Get one byte wrong and everything 401s /
> returns garbage. All values below are extracted from the production bundle
> `main.7309d5d32824e620.js` (captured 2026-07-25) and **verified** by reproducing the key
> derivation with OpenSSL.

## TL;DR

| Thing | Value |
|---|---|
| Cipher | **AES-128-ECB, PKCS7 padding** |
| Body key (`ZedriqoTix`) | ASCII string **`0123456789abcdef`** (16 bytes) → `AES.encrypt(text, Utf8.parse(key), {mode:ECB, padding:Pkcs7})` |
| Request body | `POST <url>` with JSON `{ "encrypted": "<base64( AES-ECB(JSON.stringify(payload)) )>" }` |
| Response body | `{ "statusCode": <bool/int>, "commonData": "<base64( AES-ECB(json) )>", ... }` → decrypt `commonData`, then `JSON.parse` |
| Content-Type | `application/json` (unless body is `FormData`) |
| Coverage | **251 of 257** call sites in `main.js` use encrypted POST (`post_enc`). Only ~6 are plain. |

The CLI's `client.go` must: encrypt every outbound payload with AES-128-ECB(`0123456789abcdef`) → wrap as `{"encrypted": ...}`, and decrypt `commonData` on every response with the same key.

## How the key is hidden (and how we recovered it)

The literal key `0123456789abcdef` is **not** stored in the bundle. It is itself an AES ciphertext,
decrypted at app boot:

```js
// EncrypterService (module 4245)
this.ZedriqoTix = this.dec_txt(w.MnF);           // <-- the real ECB body key
dec_txt(m)  { return AES.decrypt(m, atob(w.iZA)).toString(enc.Utf8); }   // CryptoJS passphrase mode
aesEncrypt(m){ return AES.encrypt(m, Utf8.parse(this.ZedriqoTix), {keySize:16, mode:ECB, padding:Pkcs7}).toString(); }
aesDecrypt(m){ return AES.decrypt(m, Utf8.parse(this.ZedriqoTix), {keySize:16, mode:ECB, padding:Pkcs7}).toString(enc.Utf8); }
```

Constants (module 4245, `main.7309d5d32824e620.js`):
- `iZA` (= `di`) = `X2R1bW1heV90ZXN0d2R3ZXIzMnE0MTIzMjE0MTI=`  → `atob()` = passphrase **`_dummay_testwdwer32q412321412`**
- `MnF` (= `j`) = `U2FsdGVkX18reTervTSu9OwsP3egwIyXqE3Ujw3cMenUtb1O/7EBxQRicJg2Z68C`  (CryptoJS `Salted__` ciphertext)

`dec_txt(MnF)` = CryptoJS AES **passphrase mode** decrypt (OpenSSL EVP_BytesToKey, MD5 KDF, AES-256-CBC)
of `MnF` with passphrase `_dummay_testwdwer32q412321412`. Reproduced with OpenSSL:

```
salt   = 2b7937abbd34aef4          (bytes 8..16 of base64-decoded MnF)
key256 = 656c3f71040cb25aaec16b693ed41550801e1080f19f546272bda8ec11d77c55   (EVP_BytesToKey MD5)
iv     = 9e4939f717146ec7df540b91e4a7983b
openssl enc -d -aes-256-cbc -K $key256 -iv $iv  ->  "0123456789abcdef"
```

So **`ZedriqoTix` = `0123456789abcdef`**. That 16-byte ASCII string is the AES-128-ECB key used for
every request/response body. (The outer passphrase layer only matters if the vendor ever rotates
`MnF`; the CLI can hardcode `0123456789abcdef` and re-derive only if a future bundle changes it.)

## Go reference (what the CLI implements)

```go
var bodyKey = []byte("0123456789abcdef") // AES-128 ECB, PKCS7

func encBody(v any) (string, error) {          // -> value for {"encrypted": ...}
    pt, _ := json.Marshal(v)
    ct := aesECBEncryptPKCS7(pt, bodyKey)
    return base64.StdEncoding.EncodeToString(ct), nil
}
func decCommon(commonData string) ([]byte, error) {   // response commonData -> plaintext JSON
    ct, _ := base64.StdEncoding.DecodeString(commonData)
    return aesECBDecryptPKCS7(ct, bodyKey), nil
}
```
ECB = encrypt/decrypt each 16-byte block independently, PKCS7 pad to a 16-byte boundary. No IV.

## A second, unrelated AES key (do NOT confuse)

`EncrypterService` also has an `enc_txt/dec_txt` pair that uses passphrase `atob(iZA)` =
`_dummay_testwdwer32q412321412` (CryptoJS passphrase mode, not ECB). That is only used for the
`ZedriqoTix` bootstrap above and a couple of misc string blobs. **Body traffic uses the ECB key
`0123456789abcdef`, never the passphrase.**

## Gotchas
- `keySize:16` in CryptoJS is **words? no — bytes here**: `Utf8.parse("0123456789abcdef")` yields a
  16-byte WordArray → AES-128. Do not treat the key as a passphrase (no salt/KDF on the body layer).
- Responses that are errors may return `statusCode:false` with a plaintext `message` and **no**
  `commonData`. Guard for a missing/empty `commonData` before decrypting.
- Some responses put the encrypted blob in a field other than `commonData` (e.g. `data`, seen with a
  double-wrap: `aesDecrypt(atob(resp.data))`). Document per-endpoint in the section notes.
- `FormData` uploads (writes — out of scope) skip encryption and skip the JSON Content-Type.

See also [[Auth-and-Access]] · [[Backends-and-Environment]] · [[Read-Only-Guardrails]]
