# RM stock in hand vs Fac Req — LO req nikalta hai

Shift ki RM sheet do (Date / Shift / RM code / oil ka naam / qty), aur ye SAP se
**live loose-oil stock** utha kar wahi Excel bana deta hai jo Lovepreet haath se
banata tha — **Stock in hand | Fac Req | LO req** — aur neeche short wali list.

Built **2026-09-02** for Lovepreet, 01.09.2026 ki shift-1 sheet se.

## Chalane ka tarika

Sheet ko `in/` me daalo (xlsx, csv, ya bas rows paste karke .txt), phir:

```bash
acc\rm-stock\run.cmd
```

Ya seedha:

```bash
python3 acc/rm-stock/check.py acc/rm-stock/in/2026-09-01-shift1.txt
```

Excel `out/rm-stock-<date>.xlsx` me aata hai, aur short wali list terminal par
bhi print hoti hai.

| Command | Kya karta hai |
|---|---|
| `check.py sheet.xlsx` | default — BH-LO godown, JIVO Oil, Fac Req = doosri number column |
| `check.py sheet.xlsx --req-col 1` | Fac Req peeli (pehli) column se lo |
| `check.py -` | rows stdin se (paste karke Ctrl-Z / Ctrl-D) |
| `check.py sheet.xlsx --all-warehouses` | saare godown ka stock jodkar |
| `check.py sheet.xlsx -w BH-PP` | kisi aur godown ka |
| `check.py sheet.xlsx --company mart` | Mart / Bev ki books |
| `check.py sheet.xlsx -o naam.xlsx` | apna file naam |
| `check.py sheet.xlsx --itr` | transfer request ka payload bana kar dikhata hai |
| `check.py sheet.xlsx --itr --send` | wo request DRAFT me save kar deta hai |
| `check.py sheet.xlsx --itr --send --live` | draft ke bajaye seedha live request |

## Hisaab

```
Stock in hand   =  SAP OITW."OnHand", godown BH-LO
Fac Req         =  sheet ki doosri number column, RM code ke total par jodi hui
LO req          =  Stock in hand − Fac Req      (minus = itna arrange karna hai)
```

Sheet par **do number columns** hoti hain — peeli (indent) aur uske baad **Fac
Req**. Hisaab **Fac Req** par hota hai, peeli par nahi. Agar kabhi ulta ho jaye
to `--req-col 1` lagao.

## Sheet kis shakl me bhi ho, chal jayegi

Columns ki position fix nahi hai. Har row me se **RM code** dhoondta hai
(`RM0000001`), uske baad ka text = item ka naam, uske baad ke numbers qty maane
jaate hain (doosra = Fac Req). Header row, S.No, hidden columns — koi farak nahi
padta.

## Jo cheez ye pakadta hai (aur aankh se nahi dikhti)

**Ek RM code sheet par kai baar hota hai.** 01.09.2026 ko `RM0000001` teen baar
tha — EL 24,000 + EV 7,700 + POM 600 = **32,300**, aur BH-LO me 30,814.17 L pada
tha → **LO req −1,485.83**. Har line alag se stock ke andar dikhti hai; kami
sirf **code ke total** par dikhti hai. Isiliye ye hamesha code ke total par
jodta hai.

## Excel me teen tab

| Tab | Kya hai |
|---|---|
| **STOCK vs REQ** | wahi layout — poori list, phir neeche "ye arrange karna hai" + total short |
| **SHEET** | aapki original rows, saath me SAP ke numbers |
| **BY GODOWN** | kaunsa stock kis godown me pada hai (+ committed / on order) |

## Numbers kahan se aate hain

| Excel column | SAP |
|---|---|
| Stock in hand / Cumulative Qty | `OITW."OnHand"` — godown-wise stock (default `BH-LO`, Bhakharpur Loose Oil) |
| Committed | `OITW."IsCommited"` — jo already kisi order/production ko reserve hai |
| On order | `OITW."OnOrder"` — PO par aa raha hai |
| Description | `OITM."ItemName"` — SAP ka apna naam (sheet ka EL/EV/POM alag ho sakta hai) |
| UOM | `OITM."InvntryUom"` — loose oil LTR me hai |

Company default **JIVO Oil** (`JIVO_OIL_HANADB`).

> **Stock = OnHand.** Committed alag tab me dikhta hai, ghataya nahi jata —
> RM0000002 ka committed (23,585 L) stock (3,744 L) se bahut zyada hai, to usse
> ghatane par har cheez short dikhne lagti. Physical stock hi paimana hai;
> committed sirf tension ka ishara hai.

## Inventory Transfer Request (SAP me daalna)

Wahi sheet se transfer request bhi ban jaati hai — **BH-LO → BH-PC**, ek line
per RM code, quantity = Fac Req, aur **Remark (Comments) me sheet ki date +
shift** jaisi keyed hai (`01.09.2026 Shift 1`).

```bash
python3 acc/rm-stock/check.py <sheet> --itr          # payload dikhata hai, bhejta kuch nahi
python3 acc/rm-stock/check.py <sheet> --itr --send   # DRAFT save karta hai
```

| Field | Value |
|---|---|
| Series | us mahine ki live series, `NNM1` se khud (Sep-2026 = 2649 / ITFR0926) |
| DocDate | aaj ki date — **sheet ki date remark me jaati hai, DocDate me nahi** |
| Comments | sheet ki date + shift, jaisi sheet me likhi hai |
| From → To | `BH-LO` → `BH-PC` (`--itr-from` / `--itr-to` se badal sakte ho) |
| Lines | har RM code, Fac Req quantity (code ke total par) |

Shape DocEntry **2708** (DocNum 926656501, 02-Sep-2026, USER06) se li gayi hai —
jo Lovepreet ne khud haath se banayi thi.

**Duplicate check apne aap hota hai.** Bhejne se pehle **dono** jagah dekhta hai
— `OWTQ` (live) aur `ODRF` (drafts, ObjType 1250000001) — usi sheet ki date
Comments me hai kya. Mil gayi to DocEntry/DocNum dikha kar **rok deta hai**.
Genuinely doosri chahiye to `--force-duplicate`.

> **Draft me jata hai, live nahi.** `--send` `POST /Drafts` karta hai
> (`DocObjectCode 1250000001`) — bilkul jaise Lovepreet ke apne ITR jaate hain
> (ODRF me is type ke 714 drafts; unka last DocEntry 55862 → DocNum 926656501).
> **Kuch post nahi hota** jab tak koi SAP B1 me Document Drafts kholkar **Add**
> na dabaye. Wo check aapka hai.
>
> `sapb1 draft` se ye nahi hota — uski doctype list me sirf 15 marketing
> documents hain, `InventoryTransferRequests` ko wo mana kar deta hai. Isliye
> yahan wahi andar ka raasta use hota hai jo `draft` khud use karta hai:
> `sapb1 post Drafts` + `DocObjectCode`. Live chahiye to `--live` — tab request
> seedha ban jaati hai (`POST /InventoryTransferRequests`), koi draft nahi.
> Har attempt `queries/USER06/sap-writes.jsonl` me log hota hai.
>
> **From warehouse draft me nahi jata (02-Sep-2026 ko pakda).** `POST /Drafts`
> ka type `Document` hai aur usme from-warehouse ka field hi nahi hai — na
> header par, na line par. `FromWarehouseCode` bhejo to SAP **201/204 deta hai
> aur chup chaap gira deta hai** (DocEntry 55914 par POST se aur PATCH se, dono
> se try kiya). To draft me **From = SAP ka default (BH-PF)** aayega, To = BH-PC
> theek. **Add dabane se pehle SAP B1 me From = BH-LO kar lo.** Script ye
> warning khud print karti hai. `--live` par ye dikkat nahi —
> `/InventoryTransferRequests` `StockTransfer` type hai, wo `FromWarehouse`
> leta hai.
>
> **Lines ka key draft path me `DocumentLines` hai**, `StockTransferLines`
> nahi. Galat key = header ban jata hai aur lines gayab (DocEntry 55912 aise hi
> khaali bana tha, delete kiya gaya).
>
> **Exit 7 aaye to dobara na chalao** — request SAP tak pahunch gayi thi, jawab
> nahi aaya. SAP B1 → Inventory → Inventory Transfer Request me dekho ki bani
> hai ya nahi.

## Kya padhta hai, kya likhta hai

**Padhna** poora `hana-sql` se — jo `SELECT`/`WITH` ke alawa kuch nahi chalne
deta aur read-only transaction me chalta hai. Stock, series, duplicate check —
sab read.

**Likhna sirf ek jagah:** `--itr --send` par ek transfer request **draft**
(`sapb1 post Drafts`). Uske bina ye script SAP me kuch nahi bhejti — `--itr`
akela sirf payload print karta hai. Draft se kuch post nahi hota jab tak koi Add
na dabaye; `--live` maange to hi live jaata hai. Ye CLAUDE.md RULE 0 ke andar
hai (Accounts operator ka apna kaam), aur kuch bhi bina maange nahi likhta.

## Agar kuch na chale

| Dikhega | Matlab |
|---|---|
| `hana-sql failed` | HANA tak route nahi — office network dekho, `connections/hana.env` hona chahiye |
| `no RM lines found` | sheet me RM code wali row nahi mili — code `RM0000001` shakl me hona chahiye |
| `NOT IN SAP` | wo code SAP ke item master me hai hi nahi — code galat likha gaya |
| `row N: ... no quantity` | us line par number nahi mila, wo line chhod di gayi |
