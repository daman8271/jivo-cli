package cli

import (
	"fmt"
	"sort"
	"strings"

	"sapb1/internal/errs"
)

// A POST that creates a POSTING DOCUMENT is refused here, in code.
//
// CLAUDE.md has said "prefer draft for anything document-shaped" since writes
// were switched on. A preference is not a control. On 2026-08-26 a
// `POST PurchaseInvoices` in the shared write log came back **201** — a live,
// unapproved A/P invoice, straight into the books, no draft, no approver, no
// row in anybody's Approval Status Report. It is in
// queries/*/sap-writes.jsonl and it cannot be undone from here.
//
// So the rule is now enforced rather than requested: this CLI cannot create a
// posting document directly. Every one of these has a draft route
// (`sapb1 draft <doctype>` → a human presses Add, or `sapb1 add-draft` when an
// approval template covers the login), and the draft route is the only route.
//
// What is deliberately NOT here: master data (BusinessPartners, Items,
// ItemGroups, ProjectCodes …) — a new vendor posts nothing to the ledger and
// `post` remains the right tool for it. Drafts, PaymentDrafts, Attachments2 and
// ApprovalTemplates are not here either: a draft IS the safe route, and the
// other two carry no ledger effect.
//
// There is no override flag, for the same reason the add-draft guards have
// none: an operator cannot assert that a live A/P invoice is not a live A/P
// invoice.
func refuseLivePostingDocument(entitySet, method string) error {
	if !strings.EqualFold(method, "POST") {
		return nil
	}
	target, ok := livePostingDocuments()[strings.ToLower(entitySet)]
	if !ok {
		return nil
	}
	return &errs.UsageError{Msg: fmt.Sprintf(
		"refusing to POST %s: that creates a LIVE %s in the books, with no draft and no approver.\n"+
			"  %s\n"+
			"  This is not caution and there is no flag for it. A posted document cannot be deleted, cancelled or un-posted from this CLI — only a human in the SAP B1 client can reverse it, and an unapproved one is invisible to the approver until somebody notices it in the ledger. It has happened once already through this tool (POST PurchaseInvoices → 201, 2026-08-26, in the shared write log).\n"+
			"  `post` is still the right tool for master data: BusinessPartners, Items, ItemGroups, ProjectCodes and friends post nothing to the ledger.",
		entitySet, target.noun, target.instead)}
}

type postingDocTarget struct {
	noun    string
	instead string
}

// postableLive is the one carve-out from the rule above, and it exists because
// SAP itself closed the safe route on one desk.
//
// USER19 (Mahak's GRPO desk) cannot create a GRPO *draft* in JIVO_MART: SAP
// answers `-6006 Modifying this object is not permitted for current user`
// (2026-08-27, in the shared write log). She has never produced a single draft
// in Mart by any route, while producing 148 of them in Oil and Beverages. She
// *can* post a Mart GRPO live — 87 of them from the SAP B1 client, the last on
// 2026-09-02, on the same series and branch the draft was refused on. Only an
// admin in the B1 client can grant the missing draft right; the standard
// authorisation tree is not in the database and not in the Service Layer
// (`UserPermissionTree` in Mart carries 29 nodes, all Uneecops add-on ones).
//
// So for a GRPO the choice is not "draft or live" — it is "live or nothing".
// Daman lifted the block for this one doctype on 2026-09-04.
//
// It stays a deliberately narrow hole. A GRPO receipts stock against a purchase
// order that already exists and was already approved; it is the one document
// here whose amounts are dictated by the PO rather than typed fresh. Everything
// that creates money out of a keystroke — A/P and A/R invoices, credit notes,
// payments, journal entries, free-hand stock movements — is still refused, and
// still has no flag.
//
// It no longer exists in JIVO MART. USER19 has drafted GRPOs in Mart since
// 2026-09-08 (Drafts 40246-40259), so the "live or nothing" premise is gone
// there, and on 2026-09-16 Daman ruled that nothing in Mart is ever posted
// straight to the ledger. refuseLivePostInMart closes every entry of this map
// for that company — including any entry added here later.
var postableLive = map[string]string{
	"purchasedeliverynotes": "GRPO — opened for USER19's Mart desk (-6006 on drafts), Daman 2026-09-04; closed in Mart 2026-09-16",
}

// refuseLivePostInMart is Daman's rule of 2026-09-16: in JIVO MART no entry is
// ever posted directly to the ledger. Every Mart document goes in as a draft.
//
// validateWriteEntitySet has already refused every posting document except the
// postableLive carve-outs, and it cannot see the company, so the carve-outs are
// closed here, where it can. The 13 Mart GRPOs posted live through that
// carve-out on 2026-09-04 (DocEntry 14012-14024) are why this is code and not a
// sentence. There is no flag.
func refuseLivePostInMart(entitySet, method, companyDB string) error {
	if !strings.EqualFold(method, "POST") || !isMartCompany(companyDB) {
		return nil
	}
	if _, carved := postableLive[strings.ToLower(entitySet)]; !carved {
		return nil
	}
	return &errs.UsageError{Msg: fmt.Sprintf(
		"refusing to POST %s in %s: in JIVO MART nothing is ever posted directly to the ledger (Daman, 2026-09-16). Every Mart entry goes in as a DRAFT.\n"+
			"  Use `sapb1 draft grpo --company %s` instead. A person presses Add in SAP B1 → Document Drafts.\n"+
			"  If SAP refuses the draft, stop and say so. Do not look for another route to a live document in Mart. There is no flag for this.",
		entitySet, companyDB, companyDB)}
}

// isMartCompany matches the Mart book however its name was typed on --company
// or in .env.
func isMartCompany(companyDB string) bool {
	return strings.Contains(strings.ToUpper(strings.TrimSpace(companyDB)), "JIVO_MART")
}

// livePostingDocuments is keyed by lower-cased entity set. The marketing
// documents come from draftDocTypes() — anything `sapb1 draft` can make a draft
// of must not be creatable live — plus the payment and ledger documents, which
// have their own safe routes. Minus postableLive.
func livePostingDocuments() map[string]postingDocTarget {
	m := map[string]postingDocTarget{}
	for _, dt := range draftDocTypes() {
		m[strings.ToLower(dt.EntitySet)] = postingDocTarget{
			noun:    dt.Name,
			instead: fmt.Sprintf("Use `sapb1 draft %s` instead — it creates a draft, which moves no stock and touches no ledger until a person presses Add in SAP B1 → Document Drafts.", dt.Name),
		}
	}
	for set, t := range map[string]postingDocTarget{
		"incomingpayments":          {noun: "incoming payment", instead: "Use `sapb1 draft-payment` instead — a payment draft, which a person presses Add on."},
		"vendorpayments":            {noun: "outgoing payment", instead: "Use `sapb1 draft-payment` instead — a payment draft, which a person presses Add on."},
		"checksforpayment":          {noun: "cheque", instead: "A cheque is printed off a posted payment; make the payment draft with `sapb1 draft-payment` and let a person post it."},
		"deposits":                  {noun: "deposit", instead: "A deposit posts to the bank ledger. It is keyed by a person in Banking → Deposits."},
		"journalentries":            {noun: "journal entry", instead: "A journal entry IS the ledger — there is no safe API route to one here. It is keyed by a person in Financials → Journal Entry (a Journal Voucher if it needs review first)."},
		"inventorygenentries":       {noun: "goods receipt", instead: "Use `sapb1 draft grpo` for a receipt against a PO; a free-hand goods receipt is keyed by a person in Inventory → Inventory Transactions."},
		"inventorygenexits":         {noun: "goods issue", instead: "A goods issue writes stock off. It is keyed by a person in Inventory → Inventory Transactions."},
		"stocktransfers":            {noun: "stock transfer", instead: "A stock transfer moves stock between warehouses. It is keyed by a person in Inventory → Inventory Transactions."},
		"inventorytransferrequests": {noun: "stock transfer request", instead: "Keyed by a person in Inventory → Inventory Transactions → Inventory Transfer Request."},
		"inventorycountings":        {noun: "inventory counting", instead: "A counting document adjusts stock on hand. It is keyed by a person in Inventory → Inventory Transactions → Inventory Counting Transactions."},
		// Found 2026-09-16 while closing Mart: the catalog lets `post` create
		// these, each one writes a journal entry, and none was on this list. No
		// write log line has ever touched any of them.
		"inventorypostings":                 {noun: "inventory posting", instead: "An inventory posting writes stock differences to the ledger. It is keyed by a person in Inventory → Inventory Transactions → Inventory Posting."},
		"inventoryopeningbalances":          {noun: "inventory opening balance", instead: "An opening balance posts stock value to the ledger. It is keyed by a person in Inventory → Inventory Transactions."},
		"materialrevaluation":               {noun: "inventory revaluation", instead: "A revaluation re-prices stock in the ledger. It is keyed by a person in Inventory → Inventory Transactions → Inventory Revaluation."},
		"landedcosts":                       {noun: "landed cost", instead: "Landed costs post to stock and the ledger. They are keyed by a person in Purchasing → Landed Costs."},
		"correctioninvoice":                 {noun: "A/R correction invoice", instead: "Keyed by a person in Sales A/R → A/R Correction Invoice."},
		"correctioninvoicereversal":         {noun: "A/R correction invoice reversal", instead: "Keyed by a person in Sales A/R → A/R Correction Invoice Reversal."},
		"correctionpurchaseinvoice":         {noun: "A/P correction invoice", instead: "Keyed by a person in Purchasing A/P → A/P Correction Invoice."},
		"correctionpurchaseinvoicereversal": {noun: "A/P correction invoice reversal", instead: "Keyed by a person in Purchasing A/P → A/P Correction Invoice Reversal."},
		"selfinvoices":                      {noun: "self invoice", instead: "Keyed by a person in the SAP B1 client."},
		"selfcreditmemos":                   {noun: "self credit memo", instead: "Keyed by a person in the SAP B1 client."},
		"purchasetaxinvoices":               {noun: "A/P tax invoice", instead: "Keyed by a person in the SAP B1 client."},
		"salestaxinvoices":                  {noun: "A/R tax invoice", instead: "Keyed by a person in the SAP B1 client."},
		"billofexchangetransactions":        {noun: "bill of exchange transaction", instead: "Keyed by a person in Banking → Bill of Exchange."},
		"assetcapitalization":               {noun: "asset capitalization", instead: "Keyed by a person in Financials → Fixed Assets → Capitalization."},
		"assetcapitalizationcreditmemo":     {noun: "asset capitalization credit memo", instead: "Keyed by a person in Financials → Fixed Assets."},
		"assetmanualdepreciation":           {noun: "manual depreciation", instead: "Keyed by a person in Financials → Fixed Assets → Manual Depreciation."},
		"assetretirement":                   {noun: "asset retirement", instead: "Keyed by a person in Financials → Fixed Assets → Retirement."},
		"assettransfer":                     {noun: "asset transfer", instead: "Keyed by a person in Financials → Fixed Assets → Transfer."},
	} {
		m[set] = t
	}
	for set := range postableLive {
		delete(m, set)
	}
	return m
}

// livePostingDocumentNames is for the help text and the tests: the sorted list
// of entity sets `post` will not create.
func livePostingDocumentNames() []string {
	var out []string
	for k := range livePostingDocuments() {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}
