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

// livePostingDocuments is keyed by lower-cased entity set. The marketing
// documents come from draftDocTypes() — anything `sapb1 draft` can make a draft
// of must not be creatable live — plus the payment and ledger documents, which
// have their own safe routes.
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
	} {
		m[set] = t
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
