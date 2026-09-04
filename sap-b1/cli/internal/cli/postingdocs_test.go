package cli

import (
	"strings"
	"testing"
)

// `post` must not be able to create a document that lands in the books. The
// live case that made this a code rule rather than a CLAUDE.md sentence:
// POST PurchaseInvoices -> 201 on 2026-08-26, in the shared write log.
func TestPostRefusesEveryLivePostingDocument(t *testing.T) {
	for _, set := range []string{
		"PurchaseInvoices", "Invoices", "CreditNotes", "PurchaseCreditNotes",
		"Orders", "PurchaseOrders", "DeliveryNotes",
		"Returns", "PurchaseReturns", "Quotations", "PurchaseQuotations",
		"DownPayments", "PurchaseDownPayments",
		"IncomingPayments", "VendorPayments", "ChecksforPayment", "Deposits",
		"JournalEntries",
		"InventoryGenEntries", "InventoryGenExits", "StockTransfers",
		"InventoryTransferRequests", "InventoryCountings",
	} {
		if _, err := validateWriteEntitySet(set, "POST"); err == nil {
			t.Errorf("post %s was allowed — that creates a live document in the ledger", set)
		}
	}
}

func TestPostRefusalNamesTheSafeRoute(t *testing.T) {
	_, err := validateWriteEntitySet("PurchaseInvoices", "POST")
	if err == nil {
		t.Fatal("post PurchaseInvoices must be refused")
	}
	msg := err.Error()
	for _, want := range []string{"sapb1 draft purchase-invoice", "LIVE", "cannot be deleted, cancelled or un-posted"} {
		if !strings.Contains(msg, want) {
			t.Errorf("refusal is missing %q, so it does not tell the operator what to do instead:\n%s", want, msg)
		}
	}
}

// Case-insensitively, too: OData is case-sensitive but operators are not, and
// the catalog canonicalises the spelling before this guard sees it.
func TestPostRefusalSurvivesOperatorSpelling(t *testing.T) {
	for _, spelling := range []string{"purchaseinvoices", "PURCHASEINVOICES", "PurchaseINVOICES"} {
		if _, err := validateWriteEntitySet(spelling, "POST"); err == nil {
			t.Errorf("post %q slipped through", spelling)
		}
	}
}

// The block is aimed at posting documents only. Master data and the draft
// route must be untouched, or Accounts loses its day job.
func TestPostStillAllowsMasterDataAndDrafts(t *testing.T) {
	for _, set := range []string{"BusinessPartners", "Items", "Drafts", "PaymentDrafts"} {
		if _, err := validateWriteEntitySet(set, "POST"); err != nil {
			t.Errorf("post %s must still work, got: %v", set, err)
		}
	}
}

// PATCH is a different question — patching a draft is the A/P flow's bread and
// butter — so the block must not leak into it.
func TestPatchIsNotAffected(t *testing.T) {
	if _, err := validateWriteEntitySet("Drafts", "PATCH"); err != nil {
		t.Errorf("patch Drafts must still work, got: %v", err)
	}
}

// Every doctype `sapb1 draft` can make a draft of must be on the block list:
// if a draft route exists, the live route is never the right one. The only
// exemptions are the ones postableLive names out loud, because for those the
// draft route is not actually available (SAP refuses it for the desk that needs
// it) — see the comment on postableLive.
func TestEveryDraftableDocTypeIsBlockedLive(t *testing.T) {
	blocked := map[string]bool{}
	for _, name := range livePostingDocumentNames() {
		blocked[name] = true
	}
	for _, dt := range draftDocTypes() {
		set := strings.ToLower(dt.EntitySet)
		if _, exempt := postableLive[set]; exempt {
			continue
		}
		if !blocked[set] {
			t.Errorf("%s has a draft route (`sapb1 draft %s`) but `post` would still create it live", dt.EntitySet, dt.Name)
		}
	}
}

// The GRPO carve-out, asserted both ways: it is open, and it did not drag
// anything else open with it. A/P invoices are the document that made this a
// code rule (C-0034) — if they ever come unblocked, this test fails first.
func TestGRPOIsThePostableException(t *testing.T) {
	for _, spelling := range []string{"PurchaseDeliveryNotes", "purchasedeliverynotes", "PURCHASEDELIVERYNOTES"} {
		if _, err := validateWriteEntitySet(spelling, "POST"); err != nil {
			t.Errorf("post %q must be allowed — SAP refuses the draft route for Mart's GRPO desk; got: %v", spelling, err)
		}
	}
	if len(postableLive) != 1 {
		t.Errorf("postableLive has grown to %d entries (%v) — every addition reopens a live ledger route and needs Daman's word, not a refactor", len(postableLive), postableLive)
	}
	for _, set := range []string{"PurchaseInvoices", "Invoices", "CreditNotes", "JournalEntries", "VendorPayments"} {
		if _, err := validateWriteEntitySet(set, "POST"); err == nil {
			t.Errorf("post %s came unblocked alongside the GRPO carve-out — that is the C-0034 accident again", set)
		}
	}
}
