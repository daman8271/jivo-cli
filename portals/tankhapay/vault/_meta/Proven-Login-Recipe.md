---
tags: [tankhapay, meta, recipe, verified]
---
# TankhaPay — Proven Login & Read Recipe

> Copy-paste reproducible. **Verified live 2026-07-25.** Uses only `openssl` + `curl` + `python3`
> (no pip). The CLI reimplements this in Go. Credentials come from `.env` — never inline them.

## 0. Constants
```
BODY KEY (AES-128-ECB) : 0123456789abcdef   (hex 30313233343536373839616263646566)
LOGIN URL              : https://business.tankhapay.com/api/login
ACTION                 : check_login_by_emailid1
```

## 1. Login → token
```bash
set -a; . ./.env; set +a                      # TPAY_USERNAME / TPAY_PASSWORD
KEYHEX=$(printf '0123456789abcdef' | xxd -p)
PWMD5=$(printf '%s' "$TPAY_PASSWORD" | md5 -q)     # md5sum on Linux: | md5sum | cut -d' ' -f1
PAYLOAD=$(printf '{"email":"%s","password":"%s","recaptchaToken":"","localhost":true,"action":"check_login_by_emailid1"}' "$TPAY_USERNAME" "$PWMD5")
ENC=$(printf '%s' "$PAYLOAD" | openssl enc -aes-128-ecb -K "$KEYHEX" -nosalt -a -A)
curl -s -X POST "$TPAY_API"login -H 'Content-Type: application/json' \
     --data-binary "$(printf '{"encrypted":"%s"}' "$ENC")" -o login.json
python3 -c "import json;print(json.load(open('login.json'))['token'])" > .token   # status:"True"
```

## 2. Decode JWT context (accountId / geo / ouIds)
```bash
python3 - <<'PY'
import json,base64,subprocess
d=json.loads(base64.urlsafe_b64decode(open('.token').read().split('.')[1]+'=='))
ct=base64.b64decode(d['data'])
inner=json.loads(subprocess.run(['openssl','enc','-d','-aes-128-ecb','-K',
  '30313233343536373839616263646566','-nosalt'],input=ct,capture_output=True).stdout)
print(inner['tp_account_id'], inner['geo_location_id'], inner['ouIds'])   # 2719 37 37,2211,38,40,31,1925
PY
```

## 3. Authenticated encrypted read (example: dashboard summary)
```bash
TOKEN=$(cat .token); KEYHEX=$(printf '0123456789abcdef' | xxd -p)
BODY='{"action":"get_employee_list","accountId":2719,"geo_location_id":37,"ouIds":"37,2211,38,40,31,1925"}'
ENC=$(printf '%s' "$BODY" | openssl enc -aes-128-ecb -K "$KEYHEX" -nosalt -a -A)
curl -s -X POST "${TPAY_API}dashboard/get_tpay_dashboard_data" \
     -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
     --data-binary "$(printf '{"encrypted":"%s"}' "$ENC")" -o out.json
# decrypt commonData:
python3 - <<'PY'
import json,base64,subprocess
d=json.load(open('out.json')); ct=base64.b64decode(d['commonData'])
print(subprocess.run(['openssl','enc','-d','-aes-128-ecb','-K',
 '30313233343536373839616263646566','-nosalt'],input=ct,capture_output=True).stdout.decode())
PY
```
**Verified output:** `[{"total_employees":"593","today_s_attendance":"109","new_employees":"3","cur_monthyr":"Jul-2026",...}]`
— matches the live dashboard screenshot exactly.

## Helper (already in scratchpad during study)
Encrypt any body: `printf '%s' "$JSON" | openssl enc -aes-128-ecb -K $(printf '0123456789abcdef'|xxd -p) -nosalt -a -A`
Decrypt any blob: `base64 -D <<<"$BLOB" | openssl enc -d -aes-128-ecb -K $(printf '0123456789abcdef'|xxd -p) -nosalt`

See [[Auth-and-Access]] · [[Encryption-Scheme]]
