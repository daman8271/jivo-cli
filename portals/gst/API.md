# GST portal — verified API contract for the CLI (live-captured 2026-08-21, sessions: Haryana 06…, Rajasthan 08…, Uttar Pradesh 09…)

Everything here was observed through a real browser session and, where marked **replayed**, re-issued as a plain `fetch` from the page with only `Accept`/`Content-Type` headers — i.e. a plain HTTP client with the cookie jar can do it. Raw captures: `fixtures/*.json` (gitignored — they contain live figures and the signatory's phone/email).

## Hosts (one cookie jar, domain `.gst.gov.in`)
`services.gst.gov.in` (login, profile, dashboard) · `return.gst.gov.in` (returns, credit ledger, liability register) · `payment.gst.gov.in` (cash ledger, challans) · `gstr2b.gst.gov.in` (GSTR-2B).

## Session
- Cookies after login: `AuthToken`, `UserName`, `EntityRefId`, `Lang`, `TS0134d082`, `TS01255980` (TS* = F5 BIG-IP/ASM).
- **Referer matters.** A page URL on return./payment. requested with no gst.gov.in Referer → 302 → `services.gst.gov.in/services/error/accessdenied` (seen 4×, including with a valid session). The JSON APIs below were all called from a page context that carries `Referer: https://<host>/...`. Client rule: send `Referer: https://services.gst.gov.in/services/auth/fowelcome` (or the host's dashboard URL) + `Accept: application/json, text/plain, */*` + a browser-like `User-Agent` on every call. If any JSON call 302s to accessdenied, that's the first thing to check.
- Keepalive: `GET payment.gst.gov.in/payment/auth/api/keepalive` (portal calls it itself). Idle timeout not measured (D9).
- Logout: `GET https://services.gst.gov.in/services/logout`.
- Login POST (**captured** from the real XHR, Haryana 17:25): `POST https://services.gst.gov.in/services/authenticate`, headers `Accept: application/json, text/plain, */*`, `Content-Type: application/json;charset=utf-8`, JSON body `{"username":"<user>","password":"<pass>","captcha":"<6 digits>","mFP":"<stringified JSON device fingerprint: {\"VERSION\":\"2.1\",\"MFP\":{\"Browser\":{\"UserAgent\":…,\"Vendor\":…},…}}"}`. Also `"deviceID":null,"type":"username"`. Response is always HTTP 200: success `{"url":null,"message":"auth","successCode":null}` (then the SPA GETs `/services/auth/fowelcome`); captcha failure `{"url":"/","message":null,"errorCode":"SWEB_9000"}` (page: "Enter valid Letters shown"); credential failure shows "Invalid Username or Password. Please try again." (its errorCode not yet captured — D1b). mFP = `{"VERSION":"2.1","MFP":{"Browser":{UserAgent,Vendor,VendorSubID,BuildID,CookieEnabled},"IEPlugins":…,"NetscapePlugins":…,"Screen":{FullHeight,AvlHeight,FullWidth,AvlWidth,ColorDepth,PixelDepth},"System":{Platform,systemLanguage,Timezone}},"ExternalIP":"","MESC":{"mesc":"mi=2;cd=150;id=30;mesc=…"}}` (~560 chars), full sample in `fixtures/login-xhr-full.json`. The full `mFP` blob is in `fixtures/login-xhr-full.json` once captured (D1c) — the CLI should send a fixed, realistic fingerprint captured from a real browser rather than invent one. Failure bodies seen (page text): "Invalid Username or Password. Please try again." (credential) vs "Enter valid Letters shown" (captcha). Captcha: `GET /services/captcha?rnd=<random>` → 182×50 PNG, 6 digits; fresh image each GET; refresh is free.
- No OTP/2FA was demanded on any of 10 successful logins (D10 — keep the handler anyway). **My Profile → Manage API Access** (`services.gst.gov.in/services/auth/manageapiaccess`, D10 verified Haryana): "Enable API Request" = **Yes**, session duration = **30 days** (options 6 hrs / 43200 min = 30 days) — this governs the separate GSP/G2B **API** channel (those sessions start with an OTP), not the web login; no OTP-on-web-login setting exists in My Profile. Do not change it. Dashboard (`fowelcome`) shows "Last logged in on DD/MM/YYYY HH:MM" + "Currently logged in from IP: <ip>".
- **Session-killers (found the hard way, 3 logins burned):** (a) `GET /services/login` with a live session **replaces the AuthToken cookie with a pre-auth placeholder — instant logout**; never touch the login page unless logging in. (b) A no-Referer direct navigation to a `return.` page (→ accessdenied) killed the session once; a later services-host accessdenied did *not* — treat any accessdenied as possibly fatal and verify with `ustatus`. (c) In-app `$location` route changes and same-host page loads are safe.

## Who am I
`GET services.gst.gov.in/services/api/ustatus` → `{gstin, bname, stcd, einvStatus, utype, Llogin, appStatus, cob, regType, isManufacturer, …}` (**replayed**)

## Profile
`POST services.gst.gov.in/services/auth/profile/detail` body `{}` (**replayed**) → `{gstin, lgnm, tradeNam, sts:"Active", rgdt:"01/07/2017", ctb:"Private Limited Company", dty:"Regular", stj, ctj, nba:[…], pradr:{adr}, contacted:{name, mobNum, email}, einvoiceStatus, mbr:[…], …}` — PII inside (`contacted`).

## Returns calendar / status
- `GET return.gst.gov.in/returns/auth/api/filingsnapshot` (also on services.) → last-5-periods grid for GSTR-1/IFF and GSTR-3B: `data.formNames[].retPrds[{monthYearName, filingStatus:"Filed", filingDate, status}]`. ISD registration (07…F2ZX) returns a different/empty shape — handle gracefully.
- `GET return.gst.gov.in/returns/auth/api/dropdown` → FYs and period codes `MMYYYY`.
- `GET return.gst.gov.in/returns/auth/api/rolestatus?rtn_prd=072026` → tiles: `data.user[].returns[{return_ty: GSTR1|GSTR1A|GSTR2B|GSTR3B|GSTR2A, status: FIL|NF, due_dt, tileDisable}]`.
- `GET return.gst.gov.in/returns/auth/api/formdetails?rtn_prd=072026&rtn_typ=GSTR1|GSTR3B|GSTR2A` (**replayed**) → `{status:"FIL", fil_dt:"11-08-2026", arn:"AA090726996333K", due_dt, auth_name:"Inderpal Awal", auth_dg:"Accounts Manager", bn, ln, tn, fy, fm, fp}` — **ARN + filing date per form per period.**

## Filed-returns list (ARN register)
`POST return.gst.gov.in/returns/auth/api/efiledReturns` (**replayed**)
body `{"fy":"2026-27","rfp":"Monthly","qtr":null,"mth":null,"rtntp":"GSTR1"}` — `rfp` is the literal word `Monthly|Quarterly|Annual|Half Yearly` (NOT "M": that gives RET11403 "Invalid API Request"); `rtntp` = `GSTR1|GSTR3B|GSTR9|GSTR9C|…`; nulls → RET13510 "No Record found".
→ `[{rtntype, fy, taxp:"July", arn, dof:"11/08/2026", mof:"ONLINE", filedBy, dg}]` per month. Annual: `{"fy":"2024-25","rfp":"Annual","rtntp":"GSTR9"}` → GSTR-9 ARN. Haryana's filer is GURPREET SINGH (director); UP's is Inderpal Awal (Accounts Manager) — `filedBy` differs per registration.

## GSTR-1 (outward supplies)
Page `return.gst.gov.in/returns/auth/gstr1` (reached from dashboard tile VIEW; loads with `rtn_prd`). APIs (**replayed**, GET):
- `/returns/auth/api/gstr1/userdetails?ctin=<GSTIN>` → `{regName, userType, apprv_dt}`
- `/returns/auth/api/gstr1/totalsummarycount?rtn_prd=072026` → `data.sec_count[{sec_name: B2B|B2BA|CDNR|CDNRA|EXP|EXPA|B2CL|B2CLA|CDNUR|…, err_cnt, pen_cnt, proc_cnt}]`
- **Section APIs (D8a, captured live on Haryana Jul-26, 878 B2B docs; raw: `captures/D8a-gstr1-sections.rec.json`).** The tiles are `<a data-ng-click="page_gstr1_summ('auth/gstr1/<sec>/summary',proc,pen)">`; the handler is an in-app `$location.path()` route change (no full reload) — **unless proc+pen > 500**, in which case the portal shows a modal ("restricted to 500 invoice/record items… use the Offline Utility tool") and never navigates; its OK button just opens the offline-utility help page. The underlying APIs still work regardless of the 500 cap. One list API serves every section — `GET return.gst.gov.in/returns/auth/api/gstr1/invoice` — the query params select the section (**no paging params exist**; the server returns all rows for the query; scope big sections by `ctin`):
  - counts per section: `GET /returns/auth/api/gstr1/totalsummarycount?rtn_prd=072026` → `data.sec_count[{sec_name,err_cnt,pen_cnt,proc_cnt}]`; add `&sec_name=CDNR` → per-counterparty `sec_count[{sec_name,cpty_cnts:[{ctin,trade_name,err_cnt,proc_cnt,pen_cnt}]}]`. **`&sec_name=B2B` consistently returned `GSTN-EXEC1003`** (server-side Java error, 3×) — get B2B ctins elsewhere (e.g. GSTR-2A/e-invoice data) or retry later; not a WAF/auth issue.
  - B2B docs (sec tile "4A, 4B, 6B, 6C"): `invoice?ctin=<recipient>&rtn_prd=072026&sec_name=B2B&uploaded_by=SU` → `data.processedInvoice[{inum, idt:"DD-MM-YYYY", val, invtxval, inviamt, invcamt, invsamt, invcsamt, ctin, flag:"U", irn, irngendate, srctyp:"E-Invoice"}]`. Single doc: add `inum=<inum>_<FY>`.
  - 9B CDNR (registered): same but `sec_name=CDNR` → rows add `{ntty:"C|D", nt_num, nt_dt}`. Empty result = `{"status":0,"error":{"errorCode":"RETWEB_07","message":"No pending invoices found!!"}}` — RETWEB_07 means "no rows for this query", an answer not a failure.
  - 7 B2C (Others): `invoice?rtn_prd=072026&sec_name=B2CS&uploaded_by=OE` → `processedInvoice[{pos, rt, sply_ty:"INTER|INTRA", invtxval, inviamt, invcamt, invsamt, invcsamt}]` (rate × place-of-supply rows).
  - 12 HSN: `invoice?rtn_prd=072026&sec_name=HSN` → `processedInvoice[0].hsn_b2c[]` (and `hsn_b2b[]`) `{num, hsn_sc, desc, uqc, qty, rt, txval, iamt, camt, samt, csamt}`.
  - 13 Documents issued: `invoice?inum=DOC&rtn_prd=072026&sec_name=DOC` → `data.doc_issue.doc_det[{doc_num, doc_typ, docs:[{num, from, to, totnum, cancel, net_issue}]}]`.
  - also fired by the pages: `GET auth/api/rates` (GST rate list), `GET auth/api/common/checkAatoGt5Cr?rtn_prd=`, `GET /usrmstrweb/auth/usermaster/suppliermasters`.
  - "5 - B2C (Large)" tile: absent on this GSTIN (0 docs Jul-26) — its API is presumably `sec_name=B2CL`, unverified.
  - Button "GENERATE SUMMARY" exists — it is a server-side action; the CLI must never click/call it.

## GSTR-3B
Page `return.gst.gov.in/returns/auth/gstr3b` (the dashboard VIEW does a POST to the page URL, then GETs). APIs (**replayed**, GET):
- `/returns/auth/api/gstr3b/summary?rtn_prd=072026` → full 3B (Haryana Jul-26 real: `osup_det.txval` 22,30,98,171.32, `iamt` 60,86,669.17, `camt`=`samt` 49,55,618.79; `isup_rev` 87,85,090 RCM; `inter_sup.unreg_details[{pos,txval,iamt}]` per POS; `itc_elg` block present on filed returns — see `fixtures/HR-gstr3b-summary-072026.json`): `sup_details{osup_det,osup_zero,osup_nil_exmp,isup_rev,osup_nongst}{txval,iamt,camt,samt,csamt}`, `inter_sup`, `intr_ltfee{intr_details,ltfee_details}`, `tt_val{tt_pay,tt_csh_pd,tt_itc_pd}`, `eco_dtls` (ITC table 4 appears on filed returns with data — verify on Haryana).
- `/returns/auth/api/gstr3b/getr1r3bliab?retPeriod=072026` → GSTR-1 vs 3B auto-population: `statustbl{r1frmst,r2bfrmst,…}`, `r3bautopop{r1fildt, r3bgendt, liabitc{sup_details{osup_3_1a{subtotal,det{tbl4a,tbl4b,…}}}}}`
- `/returns/auth/api/gstr3b/showpdf?retPeriod=072026`, `/negativeLiabDetails?rtn_prd=&indicator=next`, `/isgstr1fil?gstin=&rtn_prd=`, `internalapi/getRcmAvl?action=opnbal|clsbal&rtnPrd=`, `internalapi/getRclmAvl?action=opnbal&gstin=&rtnPrd=` (seen, not replayed).

## GSTR-2B (ITC statement) — host gstr2b.gst.gov.in
Page `POST /gstr2b/auth/gstr2b/summary` (tile VIEW). APIs (**replayed**, GET):
- `/gstr2b/auth/api/gstr2b/getuserdtls?rtnprd=072026&fy=2026-27` → `{gstin, lgnm, trdnm}`
- `/gstr2b/auth/api/gstr2b/getdata?rtnprd=072026` → full 2B when generated: `data.itcsumm.itcavl{nonrevsup.b2b{txval,igst,cgst,sgst,cess}, revsup, imports.impg, isdsup, othersup.cdnr}`, `data.docdata.b2b[{ctin, trdnm, supfildt, supprd, inv:[{inum, dt, val, txval, igst, cgst, sgst, cess, pos, rev, itcavl, typ, imsStatus}]}]` — **document-level ITC by supplier GSTIN** (Haryana Jul-26: 31.2 Cr B2B taxable, IGST 1.78 Cr, fixture `HR-gstr2b-getdata-072026.json`); else `{"status_cd":"0","error":{"error_cd":"GTR2B-002", message:"…not generated…"}}` (UP Jul-26). Page has links SUMMARY / ALL TABLES / Downloads.
- **Downloads are NOT server-side generates (D8b, verified in the app bundle + one live replay; raw: `captures/D8b-gstr2b-download.rec.json`).** The buttons "GENERATE JSON FILE TO DOWNLOAD" / "GENERATE EXCEL FILE TO DOWNLOAD" (page `auth/gstr2bdwld`) and "DOWNLOAD GSTR-2B SUMMARY (PDF) / DETAILS (EXCEL)" call `component.downloadJson()/downloadExcel()` which do a plain **`GET /gstr2b/auth/api/gstr2b/getjson?rtnprd=072026`** (add `&fn=<n>` only when the first response carries `data.fc` = file count, i.e. the month is chunked) and assemble the file **client-side** (exceljs/FileSaver/pdfmake). Replayed live: Haryana Jul-26 → 200, one file, ~114 KB, body keys `data.{itcsumm,rtnprd,docdata,gendt,gstin,version,cpsumm}` — same corpus as `getdata`. So the CLI can "download 2B" with this GET alone; nothing is enqueued server-side. The top-nav "Downloads" menu is only the public offline-tools link list. Other bundle-declared 2B APIs (unreplayed): `cutoff`, `getadvsrch`, `getimsadvsrch`, `getinvrate`.

## GSTR-2A
Page `return.gst.gov.in/returns/auth/gstr2/preview`; `formdetails?rtn_typ=GSTR2A`. Section links: "B2B Invoices" → `page('/auth/gstr2/preview/b2bcounterpreview')`, "Amendments to B2B Invoices" → `…/b2bacounterpreview` (in-app routes). APIs (D8c, captured live Haryana Jul-26; raw: `captures/D8c-gstr2a-b2b.rec.json`):
- supplier list: `GET /returns/auth/api/gstr2a/ctin?rtn_prd=072026&section_name=B2B` → `{rc:<total supplier count>, cpty:[{stin, cname, rc:<doc count>, cfs:"Y|N", gstr3BStatus, filingDateGstr1:"11-Aug-26", filingPeriodGstr1:"Jul-26"}]}` (353 suppliers in one response — no paging params observed; the UI notes CSV export caps at 500 records).
- docs per supplier: `GET /returns/auth/api/gstr2a/b2b?rtn_prd=072026&ctin=<stin>` → GSTN-standard `{b2b:[{ctin, inv:[{inum, idt, val, txval, iamt, camt, samt, csamt, inv_typ:"R", pos, rchrg, itms:[{num, itm_det:{rt, txval, iamt, camt, samt, csamt}}]}]}]}`. Amendments presumably `/api/gstr2a/b2ba` (unreplayed).

## Ledgers
- Cash balance: `GET payment.gst.gov.in/payment/auth/api/cashbalance` → `{tot_rng_bal, igst|cgst|sgst|cess:{tx,intr,pen,fee,oth,tot}}` (**replayed**)
- Cash statement: `GET payment.gst.gov.in/payment/auth/api/cashdetls?fdate=01/04/2026&tdate=21/08/2026` → `{fr_dt,to_dt,gstin,tr:[{ret_period, desc, igst/cgst/sgst/cess{…}, igstbal/cgstbal/sgstbal/cessbal{…}, …}]}`; companion `searcharnusngdate?fromdate=&todate=` (challan ARNs; LG9221 when none). Dates `DD/MM/YYYY`.
- Credit (ITC) balance: `GET return.gst.gov.in/returns/auth/api/itcbalance` → `{op_tot, igstTaxBal, cgstTaxBal, sgstTaxBal, cessTaxBal, blockTotBal, opProTotBal, dt}` (`dt` came back "16/02/0027" — ignore).
- Credit statement: `GET return.gst.gov.in/returns/auth/api/itcdtls?fdate=01/04/2026&tdate=21/08/2026` → `{gstin, tr:[{dt, ref_no, desc:"Opening Balance"|…, ret_period, igstTaxAmt, cgstTaxAmt, sgstTaxAmt, cessTaxAmt, igstTaxBal, cgstTaxBal, sgstTaxBal, cessTaxBal, tot_tr_amt, tot_rng_bal}]}`
- Liability register Part-I (return related): page `/returns/auth/ledger/taxdetailedledger` (reached from `/returns/auth/ledger/taxledger` → "Part -1 Return related liabilities"), selects `finyr`+`month` (from) and `finyrend`+`month` (to) → GO fires **`GET return.gst.gov.in/returns/auth/api/retdtl?fdate=MMYYYY&to_dt=MMYYYY&gstin=undefined`** (the SPA literally sends `gstin=undefined`; server resolves from session; period format is `MMYYYY`, multi-month ranges fine, e.g. `fdate=042026&to_dt=072026`) → `{fr_dt, to_dt, frm_dt, gstin, tr:[{ref_no:"AA…", dt:"DD/MM/YYYY", ret_period?, desc:"Other than reverse charge"|…, tr_typ:"Dr|Cr", dschrg_typ, tot_tr_amt, tot_rng_bal, igst/cgst/sgst/cess{tx,intr,fee,pen,oth,tot}, igstbal/cgstbal/sgstbal/cessbal{…}}]}` (D5c; raw: `captures/D5c-liability-part1.rec.json`).
- Liability register Part-II (other than return): page `payment.gst.gov.in/payment/auth/ledger/nrnledgerdetail`, inputs `chlg_frdt`/`chlg_todt` (+ Demand ID, stay-status) → GO fires **`GET payment.gst.gov.in/payment/auth/api/liabdetails?fdate=YYYY-MM-DD&tdate=YYYY-MM-DD&staystatus=&demandid=`** (note ISO dates here, unlike cashdetls) → `{gstin, nrLiabtxList:{demandspecific, transactionsList:[{demandid, nrLiabSubtxList:[{date:"DD-MM-YYYY", referenceNo, taxPeriodFrom:"YYYYMMDD", taxPeriodTo, ledgerType, …per-head amounts}]}]}}` (raw: `captures/D5c-liability-part2.rec.json`).

## Comparison (GSTR-1 vs 3B liability, 3B vs 2B/2A ITC)
Page `return.gst.gov.in/returns/auth/comparison` (D7, captured live; raw: `captures/D7-comparison.rec.json`):
- on load: `GET /returns/auth/api/gstr3bvs1/getuserdetail` → `{gstin, legalName, tradeName, liab_cd:"RUEL", month, fp:"2026", regtype, status:1}`.
- data (one call returns every report/table for the FY): **`GET /returns/auth/api/gstr3bvs1/getdata?form_type=allreports&fy=2026`** — `fy` is the FY **start year** (`2026` = FY 2026-27) → `{status, data:{time, gstin, fy, flag, tablea, tableb, tablec, tablecNew, tabled, tablee, tablef, tableg, allreports}}`. Each `table*` is 13 rows (12 months + total), row shape `{taxPeriod:"Jul-26", dec_liability{iamt,camt,samt,csamt}, actual_liability{…}, liability_diff{…}, cumu_diff{…}, cumul_diff{…}, cumu_diff_pct{…}}`; `allreports[]` = `{taxPeriod, gstr1and3b, gstr2aand3b, gstr2aand3b_itc_rev}`. The page's left menu ("Difference in liability declared and paid", "Tax liability and ITC summary", RCM, import…) only picks which table renders — no further API. Illustrative: Haryana Jul-26 declared = actual liability (zero diff). The report is portal-precomputed ("Report last updated on" ~daily); it loads for the default FY on page entry, so the recorder must be installed before navigation — or just replay the GET.

## Masters
`return.gst.gov.in/master/gstrs/A` (return types + filing day), `/master/fy`, `/master/fy/2026-27` (months), `/master/qtrs/2026-27`, `/master/hy/2026-27`, `/master/allstates`, `services.gst.gov.in/master/states`.

## Still open → Phase 2 follow-ups
D1b credential-failure errorCode (needs a wrong-password attempt — do NOT use Punjab 03, or any live credential, for this) · D9 session idle timeout (absolute lifetime; note the session-killer list above and the cookie observations below are already settled) · GSTR-1 `totalsummarycount?sec_name=B2B` returns GSTN-EXEC1003 (server error, 3×) — retry another day; B2B per-ctin list itself works · B2CL section API (no data on any current GSTIN) · GSTR-2A `b2ba` amendments replay.

## Cookie behaviour across logins (D9 observations, 2026-08-21)
Re-login issues a **new `AuthToken`** (value changes per session); `UserName`/`EntityRefId` are stable per user across sessions; per-host `TS*` (F5) values rotate with page traffic but **not** on a mere JSON API call (verified: 1 call, zero cookie changes); `TS01255980` on `.www.gst.gov.in` stayed constant all day. Nothing else is set or dropped mid-session.

## Plain-client rules (D3, verified)
Live curl matrix, 2026-08-21, against the browse session for Rajasthan `08AACCJ4223F1ZW` (GSTIN echoed in every 200). A plain HTTP client with the cookie jar reaches all the JSON APIs — the WAF keys on **Referer** and **User-Agent**, not on being a browser. Raw table: `captures/D3-waf-matrix.md`.

**Minimal header set that works, per host:**
| host | cookies | Referer (required) | User-Agent | Accept | TS\* cookie |
|---|---|---|---|---|---|
| `services.gst.gov.in` | AuthToken(+UserName,EntityRefId) | **not** required for `/services/api/ustatus`; send host dashboard Referer anyway for uniformity | see UA rule below | optional | not required |
| `return.gst.gov.in` | same | **required** → `https://return.gst.gov.in/returns/auth/dashboard` | any non-blocked | optional | not required |
| `payment.gst.gov.in` | same | **required** → `https://payment.gst.gov.in/payment/auth/ledger/cashledger` | any non-blocked | optional | not required |
| `gstr2b.gst.gov.in` | AuthToken(+UserName,EntityRefId) — no host TS cookie exists | **required** → `https://gstr2b.gst.gov.in/gstr2b/auth/gstr2b/summary` | any non-blocked | optional | n/a |

- **Referer is the gate on return/payment/gstr2b.** Cookies present but Referer missing/blank → **302 → `/services/error/accessdenied`** (not a session problem). Cookies present + host-dashboard Referer → 200. `services /ustatus` alone does not need a Referer. Send the host's dashboard Referer on every call and this never bites.
- The two read-shaped **POSTs** (`return …/efiledReturns`, `services …/profile/detail`) use the identical recipe (cookies + host Referer + `Content-Type: application/json;charset=utf-8`) → both 200.

**TS\* cookies are NOT required.** Every minus-TS request passed on a fresh session (services/return/payment; gstr2b has no TS cookie at all). The auth bearer is **`AuthToken`** (on `.gst.gov.in`, shared by all four hosts, `httpOnly`+`secure`). Persist and resend TS\* if you have them (harmless), but the client must not depend on them.

**User-Agent — do NOT impersonate a real browser (this reverses the earlier assumption):**
- `services.gst.gov.in` **TCP-resets (curl 56) any branded desktop-Chrome UA** (`…Chrome/145.0.0.0 Safari…`, also 120; adding sec-ch-ua client hints does not help — reproduced 6×). It also serves bare `Mozilla/5.0` an ASM **"Request Rejected"**. It accepts: no UA, the **HeadlessChrome** UA, and a tool UA (`gst-portal/1.0 (read-only)`).
- `return`/`payment`/`gstr2b` accepted every UA tried (default curl, Chrome, HeadlessChrome) once session+Referer were valid.
- **Use one UA everywhere: the HeadlessChrome string** `Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/145.0.7632.6 Safari/537.36` — the only UA verified 200 on all four hosts live. Never send a branded desktop-Chrome UA or a bare `Mozilla/5.0`.

**No HTML warm-up GET is needed.** On a valid session the curl client hit each host's JSON API directly (having never loaded any dashboard HTML) and got 200. The plan's optional `client.warm(host)` is unnecessary for reads. (At session end, a warm-up GET + `keepalive` also failed to *revive* an expired session — warming is neither needed nor a recovery path; a dead session must re-login.)

**`filingsnapshot` host:** call it on **`services.gst.gov.in/returns/auth/api/filingsnapshot`** (200 JSON). The same path on `return.gst.gov.in` is F5-ASM **"Request Rejected"** for a plain client under every header combo — do not use the return host for this one endpoint.

**Login prerequisites are fetchable by a plain client (no session):** `GET /services/login` → 200 ~4.8 KB HTML, `Set-Cookie: AuthToken` (pre-auth placeholder) + `TS0134d082`; then `GET /services/captcha?rnd=<r>` with that jar → 200 **PNG 182×50**, `Set-Cookie: CaptchaCookie` (the server-side captcha binding). Carry the `/login`+`/captcha` jar (incl. `CaptchaCookie`) into `POST /services/authenticate`. Use a non-blocked UA for these too (bare `Mozilla/5.0` is ASM-rejected here as well).

**Error → action map (client):** `302 accessdenied` = fix Referer, don't re-login · `403` (return/payment/gstr2b) or `services /ustatus` returning `{}` (2 B) = expired/absent session → re-login · `200` "Request Rejected" HTML = ASM block (wrong host/path, or a blocked UA) · `000`/connection-reset on services = branded-Chrome UA, change it.

**Cookie attributes (D9):** all auth cookies (`AuthToken`, `UserName`, `EntityRefId`, per-host `TS*`) are `httpOnly`+`secure`, sameSite=Lax, **session** (no expiry) — so a `document.cookie` export misses them; `auth import` must use a CDP/network-level export. `Lang` is the only non-httpOnly, non-secure, host-only, dated cookie. Session lifetime itself: observed valid for the run then expired (~idle) around 12:20 UTC; return/payment access appeared to lapse just before services — precise timeout is still D9.
