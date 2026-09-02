---
title: JIVO org chart
type: moc
org: JIVO
source: "JSAP hierarchy (live), SAP B1, factory app — pulled 2026-08-11"
last_verified: 2026-08-11
status: confirmed
tags: [jivo/moc, jivo/org]
---

# JIVO org chart — the real one

Pulled live from **JSAP**, JIVO's internal ops platform, which carries the HR
hierarchy: **223 employees, 13 active HODs, ~28 departments**. This is the
authority on who reports to whom — SAP has no usable reporting line
(`OHEM.manager` is populated on exactly **one** row company-wide).

> [!warning] JSAP covers Head Office only
> **There is no Production or Factory department in the JSAP tree.** Shop-floor
> people — [[Gautam]], [[Honey Factory]] — exist only in the factory app and in
> SAP. That single fact explains most of the holes below: the roster mixes HO
> staff (who are in the hierarchy) with plant staff (who are not).

---

## The 13 HODs — and how many we actually have

| HOD | Code | Department | In our roster? |
|---|---|---|---|
| **[[Ziyaul\|Ziyaul ji]]** | JWPL0042 | Accounts & Finance + Audit + **IT** | ✅ |
| **[[Shunty Veerji\|Shunty Veerji Accounts]]** | JWPL0035 | Accounts & Finance | ✅ |
| **[[Raju Veerji\|Jasbir Singh Raju]]** | JWPL000C | **Dispatch** | ✅ |
| **[[Gurvinderjeet Singh]]** | JWPL0139 | **EA** | ✅ |
| **[[Avtar Vg]]** | JWPL0014 | Accounts & Finance | ❌ **— and he is [[Preshit Singh]]'s boss** |
| **[[Prabhu]]** | JWPL2217 | **ECom** | ❌ **— boss of both e-com people** |
| Arshdeep Singh | JWPL3005 | — | ❌ |
| Arvinder | JWPL0115 | — | ❌ |
| Bhupinder Singh | JWPL1556 | — | ❌ |
| **Gagan Vg** | JWPL0018 | — | ❌ *(a third Gagan — not [[Gagan PU]])* |
| Karanpreet Vg | JWPL1557 | — | ❌ |
| Nirmal Didi | TEMP0001 | — | ❌ |
| Veerji | TEMP0002 | — | ❌ |

**4 of 13.** Nine department heads are missing from the roster — see
[[MISSING-PEOPLE]].

---

## The subtrees our people sit in

### Accounts & Finance — the biggest cluster
```
Avtar Vg (JWPL0014) ── HOD, Accounts & Finance          ❌ not in roster
└── Preshit Singh (JWPL0030) ── Sub-HOD, A/R            ✅ [[Preshit Singh]]
      └── 14 direct reports:
          Harpreet Singh · Sadaf Sartaj · Sumit Kumar Mehta · Mansi
          Jaspal Singh · Paramjeet Kaur · Amandeep Singh · Krishan Preet
          Gurleen Kaur · Jagpreet Singh · Gurpreet Kaur · Manpreet Kaur (+2)

Ziyaul ji (JWPL0042) ── HOD over THREE departments      ✅ [[Ziyaul]]
├── Accounts & Finance  (3 sub-depts)
├── Audit               (2 sub-depts)
└── IT                  (2 sub-depts, incl. a dedicated SAP unit)

Shunty Veerji Accounts (JWPL0035) ── HOD, Accounts & Finance   ✅ [[Shunty Veerji]]
└── 1 sub-department, 3 executives

Gurpreet Singh(Gopi) (JWPL1601) ── Executive, Accounts & Finance ✅ [[Gurpreet Singh Gopi]]
```

**Four of the ten sit in Accounts & Finance.** That is the centre of gravity of
this roster — not production, not planning.

### E-commerce
```
Prabhu (JWPL2217) ── HOD, ECom                          ❌ not in roster
├── Kamaldeep Singh (JWPL0092) ── Sub-HOD, ECom › Supply Chain  ✅ [[Kamaldeep Singh]]
│     ├── Diljeet Singh
│     ├── Lucky Arora
│     ├── Piyush Kamwal
│     └── Princepreet Singh (JWPL1729)   ← possible [[Prince Bathinda]]?
└── Gagandeep Singh (JWPL2029) ── Sub-HOD, ECom          ✅ [[Gagan PU]]
```

### Dispatch
```
Jasbir Singh Raju (JWPL000C) ── HOD, Dispatch  (reports to nobody)   ✅ [[Raju Veerji]]
└── Rajkumar Tiwari (JWPL0374) ── Dispatch › GRPO
```

### EA
```
Gurvinderjeet Singh (JWPL0139) ── HOD, EA (dept 29)  (reports to nobody)  ✅
└── Bikramjeet Singh (JWPL3069)
```

### Plant — outside JSAP entirely
```
(no JSAP department)
├── Gautam Chanana  ── factory app user 24, EP0987, dept FACTORY    ✅ [[Gautam]]
│     └── 6,003 production orders · zero budget authority
└── Honey Gupta     ── factory app users 60 & 61, warehousemgr@     ✅ [[Honey Factory]]
      └── absent from JSAP org tree and user list
```

---

## Who actually signs things

**The approval chain is one stage deep, and it has no monetary limits.** Routing
is by **budget head**, not by amount — a ₹250 imprest and a ₹6,00,210 labour
contract go to the same single approver with no second signature.

Named approvers, July 2026 (live counts):

| Approver | Approved | Pending | Rejected | In roster? |
|---|---|---|---|---|
| **[[Raju Veerji\|Jasbir Singh]]** | **94** | 21 | 10 | ✅ |
| Ravinder Singh | 47 | 10 | 1 | ❌ |
| Avtar Singh | 46 | 0 | 2 | ❌ |
| **[[Gurvinderjeet Singh\|Gurvinder Singh]]** | 23 | 5 | 2 | ✅ |
| Gurpreet Singh | 4 | 1 | 0 | ❌ |
| Arshdeep Singh | 3 | 4 | 0 | ❌ |
| Karanpreet Singh | 0 | 3 | 1 | ❌ |

Everyone else on the 160-user list is at 0/0/0.

**Only three people hold the `Request Approver` type:** [[Ziyaul]] (`ziaulhaque`),
[[Gurvinderjeet Singh]] (`gurvinder`), and **Prabhjot** (`prabhjot`) — who is not
in the roster. The sole **Request Initiator** is **Shahrukh** (FACTORY) — also
not in the roster.

**Approval types (10):** Budget · BOM · Payment · Advance Payment · IMC ·
Backdate · Credit limit · **Production Order** · QC · Budget Allocation.

**Budget heads (15, = SAP cost centres):** One Time Expense · Back Office ·
NPD1/2/3 · **Factory** · **Delivery Bhakharpur** · Sales · Sales Realise ·
Media Marketing · Salary Confidential · Interest · Delivery Mayapuri ·
**Factory Common** · Transport.

[[Raju Veerji|Jasbir]] owns *Factory*, *Factory Common* and *Delivery Bhakharpur*
— which is to say **he signs for the plant's money**.

---

## Companies and sites

> [!success] "Wellness" — settled
> From SAP's own company table (`OADM`): **two legal entities, three sets of books.**
>
> | SAP database | Legal entity |
> |---|---|
> | `JIVO_OIL_HANADB` | **JIVO WELLNESS PVT LTD** |
> | `JIVO_BEVERAGES_HANADB` | **(Beverage Unit) JIVO WELLNESS PVT LTD** |
> | `JIVO_MART_HANADB` | **JIVO MART PVT LTD** |
>
> So Oil and Beverages are both *Jivo Wellness*; only Mart is separate. Every
> employee code is prefixed **JWPL** = *Jivo Wellness Pvt Ltd*.
>
> [[Honey Factory|Honey]]'s "Wellness FG storage" = the **Oil-company** FG godown
> at Bhakharpur. [[Prince Bathinda|Prince]]'s "Mart FG storage" = the **Mart**
> godown. They are the two entities, not two brands.

**Physical sites:**

| Site | Where | Warehouse codes |
|---|---|---|
| **Bhakharpur plant** | Khasra 20//9/2, Sonipat HR | `BH-*` (~28 codes) |
| **Gupta Godown** | Khasra 21/12/1, Sonipat HR — *a different khasra, a separate site* | `GP-FG`, `GP-FGM`, `GP-ECM`, `GP-PM` … |
| **Mayapuri HO** | A-35/1, New Delhi | `DL-MP`, `DL-FG`, `DL-EC`, `DL-INT` … |
| **Rajouri Garden** | J-3/190 Nehru Market, Delhi | `DL-J3`, `DL-POP` |
| Luhari Jhajjar · Gurugram · Karnataka · Punjab C&F | — | `BH-LR`, `GM-HR`, `KT-*`, `PB-*` |

**JSAP branches (6):** Delhi · **Factory** · Punjab · Himachal Pradesh ·
Haryana Sales · Delhi ISD.

**Production lines — six, plus QC.** They exist in the factory app as *role
accounts*, not people: `EP7890` 10 Head · `EP0986` 6 Head · `EP0985` Clear Pack ·
`EP0983` JP · `EP5678` Pouch Machine · `EP3456` Tin Head · `EP12346` QC.

> [!failure] No person is attached to any production line, anywhere
> `/production-execution/lines/`, `/machines/` and `/line-configs/` all return
> zero rows, and SAP's cost-centre dimensions carry no machine dimension. So the
> question *"who runs which line"* cannot be answered from any system — it has to
> come from [[Gautam]].

---

## Links

[[ROSTER]] · [[MISSING-PEOPLE]] · [[functions/The Five Departments|The Five Departments]]
