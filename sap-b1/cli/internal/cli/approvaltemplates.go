package cli

import (
	"fmt"
	"os"
	"sort"
	"strings"

	"sapb1/internal/config"
)

// GUARD 5c — the originator guard.
//
// Guard 5b asks whether the COMPANY routes an API Add to approval at all
// (Enable Approval Procedures in DI). This one asks the next question, and it
// is the question that was missing on 2026-09-03: does an Always-terms template
// name THIS LOGIN as an originator for THIS document type?
//
// It matters because of how SAP behaves when the answer is no. It does not
// refuse, and it does not ask. It finds no template, decides the document needs
// no approval, and posts it straight into the books — live, unapproved, with
// nobody in the Approval Status Report. Nothing in this repo can undo that.
//
// Measured live on 2026-09-03 (Oil, Mart, Beverages):
//
//	SELECT T0."WtmCode", T0."Name", T3."TransType",
//	       (SELECT STRING_AGG(U."USER_CODE", ',') FROM WTM1 X
//	          JOIN OUSR U ON U."USERID" = X."UserID"
//	         WHERE X."WtmCode" = T0."WtmCode") AS ORIGINATORS
//	  FROM OWTM T0 JOIN WTM3 T3 ON T3."WtmCode" = T0."WtmCode"
//	 WHERE T0."Active" = 'Y' AND T0."Conds" = 'N' AND T3."TransType" = 18
//
// Oil 103, Mart 48, Beverages 68 — all named "API AP AUTO (USER39)", all
// Always terms, approver USER03 (BHAWANI), A/P invoice only.
//
// Re-measured 2026-09-10 with the same query, after Daman asked for Divjot to
// get Add & New too ("we dont wnana post to ledger but directly to bhawani").
// USER08 (DIVJOT, USERID 17 in all three books) was PATCHed onto all three
// templates alongside USER39 (MUQEEM, USERID 53 in Oil/Mart, 50 in Bev), so
// each now reads:
//
//	Oil  103 -> USER39,USER08   approver USER03
//	Mart  48 -> USER39,USER08   approver USER03
//	Bev   68 -> USER39,USER08   approver USER03
//
// So an A/P invoice submitted by EITHER of those two reaches Bhawani, and the
// same submit by USER07, USER19 or any other login still posts live — which is
// why the rest of this guard stays exactly as it was. Query-based templates —
// Conds='Y', e.g. Oil 6 "SCHEME FACTORY", which does list every USERnn — are
// skipped entirely for a DI/Service Layer Add and cannot save it.
//
// Re-measured 2026-09-15 (manager, all three books) after Daman found Bhawani
// receiving TWO requests per A/P invoice draft. An Add from the SAP client
// consults every template, and the condition-based "USER03 AP" ones (Oil 40 and
// 41, Mart 17, Bev 1 and 2) also named USER08/USER39 and also route to USER03 —
// so one draft raised one request per matching template, and posted only when
// all were approved (23 Oil, 20 Mart, 2 Bev drafts sat like that). Fixed in
// Oil that day: 103 now also covers atdtApCreditMemo, and USER08/USER39 were
// removed from 40 and 41 (B1S-ReplaceCollectionsOnPatch, logged in
// queries/daman/sap-writes.jsonl). The table below is unchanged by that — it
// speaks for oPurchaseInvoices, the only kind add-draft accepts — and the
// Service Layer Add was never the doubling route: it consults only the Always
// template.
//
// 2026-09-16, Oil only: USER07 (HARSH, USERID 16 in all three books) was added
// to 103 on Daman's word ("do it for Harsh also") and removed from 40 and 41,
// read back the same minute — Oil 103 now names USER39, USER08, USER07. Mart 48
// and Bev 68 are unchanged. The Vishal and Shahrukh desks that use USER07 are
// still drafts-only through desks.json, which refuses before this guard runs.
//
// Why the table lives here in code and not in a live read: the Service Layer
// refuses ApprovalTemplates to an operator login ("[SAP -3000] The logged-on
// user does not have permission to use this object" — verified under USER39 on
// 2026-09-03), so there is no fact to read at run time under the very login
// that needs checking. A guard that cannot read its fact must fail closed, and
// failing closed for everyone would have taken Muqeem's working desk down with
// Divjot's then-broken one. So the evidenced list is compiled in, and it is
// overridable by one env assertion for the day an admin widens a template
// before this table is rebuilt — which is how Divjot's desk ran until the
// binaries shipped on 2026-09-10.
type approvalTemplate struct {
	CompanyDB   string
	ObjectCode  string // DocObjectCode as SAP spells it, e.g. "oPurchaseInvoices"
	WtmCode     string
	Name        string
	Originators []string
}

// verifiedApprovalTemplates is the Always-terms, active templates this repo has
// actually read out of SAP, with the originators they actually name. Add a row
// only with the query above in hand.
func verifiedApprovalTemplates() []approvalTemplate {
	return []approvalTemplate{
		{CompanyDB: "JIVO_OIL_HANADB", ObjectCode: "oPurchaseInvoices", WtmCode: "103", Name: "API AP AUTO (USER39)", Originators: []string{"USER39", "USER08", "USER07"}},
		{CompanyDB: "JIVO_MART_HANADB", ObjectCode: "oPurchaseInvoices", WtmCode: "48", Name: "API AP AUTO (USER39)", Originators: []string{"USER39", "USER08"}},
		{CompanyDB: "JIVO_BEVERAGES_HANADB", ObjectCode: "oPurchaseInvoices", WtmCode: "68", Name: "API AP AUTO (USER39)", Originators: []string{"USER39", "USER08"}},
	}
}

// approvalOriginatorEnv is the one override, and it is a statement of fact
// about SAP, not a permission: "an admin has added this login to template N".
// It is set once per box in the .env next to the binary, never per run, and the
// refusal message below tells the operator exactly which query proves it. Set
// it wrongly and the Add posts live — which is precisely what it must be read
// as asserting.
const approvalOriginatorEnv = "SAPB1_APPROVAL_TEMPLATE"

// checkAddApprovalTemplate refuses a SUBMIT whose login is on no Always-terms
// template for this document type. Untouched for dasApproved (click two): the
// approval has already been given there, and no template has anything to say.
func checkAddApprovalTemplate(pf *addPreflight, cfg *config.Config) {
	if pf.Action != actionSubmit {
		return
	}

	objCode := strings.TrimSpace(pf.Type.ObjectCode)
	user := strings.TrimSpace(cfg.User)

	// The box asserts a template an admin has since widened. Take it and move
	// on: it is a claim about SAP made by whoever provisioned this checkout, and
	// it is as visible as the .env file it sits in.
	if strings.TrimSpace(os.Getenv(approvalOriginatorEnv)) != "" {
		return
	}

	var (
		matched  bool
		known    []approvalTemplate
		anyForCo bool
	)
	for _, t := range verifiedApprovalTemplates() {
		if !strings.EqualFold(t.CompanyDB, cfg.CompanyDB) {
			continue
		}
		anyForCo = true
		if !strings.EqualFold(t.ObjectCode, objCode) {
			continue
		}
		known = append(known, t)
		for _, o := range t.Originators {
			if strings.EqualFold(o, user) {
				matched = true
			}
		}
	}
	if matched {
		return
	}

	pf.Problems = append(pf.Problems, draftProblem{
		Guard: "template",
		Msg: fmt.Sprintf(
			"refusing to add %s(%d) in %s: %s is not an originator on any approval template this repo has verified for this document type (%s).\n"+
				"  %s\n"+
				"  This is the dangerous case, which is why there is no flag for it: SAP does not refuse an Add it finds no template for. It decides the document needs no approval and posts it LIVE into the books, unapproved, with nothing in anybody's Approval Status Report — and nothing here can undo that.\n"+
				"  Leave the draft where it is. Attach the bill, then have a person open Purchasing → Document Drafts in the SAP B1 client and press Add — that route DOES consult the template.\n"+
				"  To fix it properly, an admin adds %s as an originator on the Always-terms template for this document type (Administration → Approval Procedures → Approval Templates → Originators). Then re-verify with the OWTM/WTM3/WTM1 query in approvaltemplates.go and either add the row there or set %s=<WtmCode> in this box's .env.",
			kindAddDraft.EntitySet, pf.DocEntry, cfg.CompanyDB, blankAs(user, "this login"), pf.Type.Noun,
			describeKnownTemplates(known, anyForCo, cfg.CompanyDB, pf.Type.Noun),
			blankAs(user, "the login"), approvalOriginatorEnv),
	})
}

// describeKnownTemplates says what IS on file, so the refusal reads as a fact
// about SAP rather than a tool being difficult.
func describeKnownTemplates(known []approvalTemplate, anyForCo bool, companyDB, noun string) string {
	if len(known) == 0 {
		if anyForCo {
			return fmt.Sprintf("No Always-terms template covering %s in %s is on file here at all — only other document types are.", noun, companyDB)
		}
		return fmt.Sprintf("No approval template in %s has been verified by this repo yet, for any document type.", companyDB)
	}
	var parts []string
	for _, t := range known {
		who := append([]string(nil), t.Originators...)
		sort.Strings(who)
		parts = append(parts, fmt.Sprintf("%s %q names %s", t.WtmCode, t.Name, strings.Join(who, ", ")))
	}
	return "On file for this document type: template " + strings.Join(parts, "; ") + " — and nobody else."
}
