# 2026-09-15 — Bhawani was getting two approval requests per A/P draft (Oil fixed)

**Who:** Daman, from Divjot's screen (Approval Status Report, JIVO MART, 13:58).

**Finding (live, manager, all three books):** an A/P invoice Added from the SAP client by
USER08 (Divjot) or USER39 (Muqeem) matched the Always template (Oil 103 / Mart 48 / Bev 68)
*and* the condition-based "USER03 AP" templates (Oil 40 + 41, Mart 17, Bev 1 + 2). Every one
of those routes to stage USER03 = Bhawani, so SAP raised one request per template and the
draft posted only when all were approved. Pending doubles at 14:20: Oil 23, Mart 20, Bev 2.
The CLI's Service Layer Add consults only the Always template, so it was never the doubling
route; the SAP-client Add is.

**Done (Oil):** 103 now covers A/P Invoice + A/P Credit Memo; USER08 and USER39 removed from
40 (34→32 originators) and 41 (39→37). Write log: `queries/daman/sap-writes.jsonl` 14:2x.
**Waiting for Daman:** the same change in Mart (17, 48) and Beverages (1, 2, 68).

**For Bhawani — Oil drafts that still carry two open requests; approve both on each:**
    23 Oil A/P invoice drafts with two open requests (103 + 40/41):
      56224  2026-06-03  USER08  ARNAV TRANSPORT SERVICE             Rs    12,000.00  
      56786  2026-09-09  16  TPAC PACKAGING INDIA PVT LTD II     Rs    40,181.00  Based On Goods Receipt PO 2026096618 |
      56787  2026-09-09  16  TPAC PACKAGING INDIA PVT LTD II     Rs    27,832.00  Based On Goods Receipt PO 2026096617 |
      56789  2026-09-09  16  ECHO PLAST INDIA                    Rs   177,465.00  Based On Goods Receipt PO 2026096614 |
      56791  2026-09-08  16  BABAJI UDYOG PVT. LTD.              Rs   150,570.00  Based On Goods Receipt PO 2026096596 |
      56836  2026-08-11  USER08  DELHI PUNJAB TRANSPORT CO           Rs   164,235.00  Based On Goods Receipt PO 2026076979. 
      56840  2026-09-05  USER08  PIONEER PET SWASTIC PET INDUSTRIES  Rs 1,080,253.00  Based On Goods Receipt PO 2026096532 |
      56876  2026-09-01  USER39  ARVINDER SINGH IMPREST JWPL0115 FA  Rs     5,778.00  Based On Goods Receipt PO 2026086899. 
      56877  2026-08-27  USER39  ARVINDER SINGH IMPREST JWPL0115 FA  Rs     2,400.00  Based On Purchase Orders 220826125.G.
      56889  2026-08-27  USER39  ARVINDER SINGH IMPREST JWPL0115 FA  Rs     6,510.00  Based On Goods Receipt PO 2026086824. 
      56910  2026-08-31  USER08  ARVINDER SINGH IMPREST JWPL0115 FA  Rs     7,403.00  
      56911  2026-09-02  USER08  ARVINDER SINGH IMPREST JWPL0115 FA  Rs     1,050.00  
      57060  2026-08-01  USER39  KHANNA HIMANSHU & ASSOCIATES        Rs    50,000.00  
      57061  2026-09-12  USER39  KHANNA HIMANSHU & ASSOCIATES        Rs     7,500.00  
      57063  2026-09-12  USER39  PARSH ALL INDCO PROFESSIONAL WORKF  Rs    12,400.00  
      57078  2026-09-02  USER39  ARNAV TRANSPORT SERVICE             Rs    68,727.00  Based On Goods Receipt PO 2026086766. 
      57110  2026-09-07  USER08  SHAHID ALI-CONTRACTOR               Rs    51,975.00  
      57113  2026-08-31  USER08  TATA AIG GENERAL INSURANCE CO LTD   Rs    42,991.00  BEING INSURANCE EXPENSE & PREPAID EXPE
      57114  2026-09-02  USER08  TATA AIG GENERAL INSURANCE CO LTD   Rs    70,600.00  BEING INSURANCE EXPENSE & PREPAID EXPE
      57115  2026-09-02  USER08  TATA AIG GENERAL INSURANCE CO LTD   Rs    78,407.00  BEING INSURANCE EXPENSE & PREPAID EXPE
      57117  2026-08-27  USER08  TATA AIG GENERAL INSURANCE CO LTD   Rs    18,042.00  BEING INSURANCE EXPENSE & PREPAID EXPE
      57132  2026-09-02  USER08  ARNAV TRANSPORT SERVICE             Rs     3,740.00  BILTY NO 7430 Based On Goods Receipt P
      57138  2026-08-01  USER08  SUSHIL KUMAR SINGH IT 20000 IMPRES  Rs     3,024.00  
      total Rs 2,083,083.00

Skills updated: jivo-add-and-new (side-effect section rewritten), jivo-service-contractor-invoice (USER08 on the Always templates). CLI: comment in approvaltemplates.go.
