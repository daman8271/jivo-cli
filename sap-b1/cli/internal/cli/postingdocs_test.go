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
		"InventoryPostings", "InventoryOpeningBalances", "LandedCosts",
		"CorrectionInvoice", "CorrectionInvoiceReversal",
		"CorrectionPurchaseInvoice", "CorrectionPurchaseInvoiceReversal",
		"SelfInvoices", "SelfCreditMemos", "PurchaseTaxInvoices", "SalesTaxInvoices",
		"BillOfExchangeTransactions",
		"AssetCapitalization", "AssetCapitalizationCreditMemo", "AssetManualDepreciation",
		"AssetRetirement", "AssetTransfer",
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
			t.Errorf("post %q must still pass the company-blind check (the carve-out is closed per company, by refuseLivePostInMart); got: %v", spelling, err)
		}
	}
	// Two carve-outs, both on Daman's explicit word: GRPO (2026-09-04) and
	// MaterialRevaluation (2026-09-19). The count is pinned on purpose — a
	// third one must be a deliberate edit to this line, with a reason written
	// next to it in postableLive, not something a refactor slides in.
	if len(postableLive) != 2 {
		t.Errorf("postableLive has grown to %d entries (%v) — every addition reopens a live ledger route and needs Daman's word, not a refactor", len(postableLive), postableLive)
	}
	for _, set := range []string{"PurchaseInvoices", "Invoices", "CreditNotes", "JournalEntries", "VendorPayments"} {
		if _, err := validateWriteEntitySet(set, "POST"); err == nil {
			t.Errorf("post %s came unblocked alongside the GRPO carve-out — that is the C-0034 accident again", set)
		}
	}
}

// Daman, 2026-09-16: in JIVO MART nothing is ever posted directly to the ledger.
// Every carve-out postableLive opens elsewhere is shut in Mart, however the
// company name was typed. The 13 live Mart GRPOs of 2026-09-04 (DocEntry
// 14012-14024) went in through exactly this hole.
func TestMartClosesEveryCarveOut(t *testing.T) {
	if len(postableLive) == 0 {
		t.Fatal("postableLive is empty — this test no longer proves anything; drop refuseLivePostInMart's carve-out logic together with it")
	}
	for set := range postableLive {
		for _, db := range []string{"JIVO_MART_HANADB", "jivo_mart_hanadb", "  JIVO_MART_HANADB "} {
			if err := refuseLivePostInMart(set, "POST", db); err == nil {
				t.Errorf("post %s in %q was allowed — nothing in Mart may be posted straight to the ledger", set, db)
			}
		}
	}
}

func TestMartRefusalNamesTheDraftRoute(t *testing.T) {
	err := refuseLivePostInMart("PurchaseDeliveryNotes", "POST", "JIVO_MART_HANADB")
	if err == nil {
		t.Fatal("post PurchaseDeliveryNotes in Mart must be refused")
	}
	for _, want := range []string{"JIVO MART", "DRAFT", "sapb1 draft grpo", "no flag"} {
		if !strings.Contains(err.Error(), want) {
			t.Errorf("Mart refusal is missing %q:\n%s", want, err)
		}
	}
}

// The Mart rule must not leak into the other two books, into PATCH, or into
// master data in Mart itself.
func TestMartRuleStaysInMart(t *testing.T) {
	for _, db := range []string{"JIVO_OIL_HANADB", "JIVO_BEVERAGES_HANADB", "TESTDB"} {
		if err := refuseLivePostInMart("PurchaseDeliveryNotes", "POST", db); err != nil {
			t.Errorf("%s: the Mart rule refused a non-Mart company: %v", db, err)
		}
	}
	if err := refuseLivePostInMart("PurchaseDeliveryNotes", "PATCH", "JIVO_MART_HANADB"); err != nil {
		t.Errorf("PATCH is not a new entry and must not be refused here: %v", err)
	}
	for _, set := range []string{"BusinessPartners", "Items", "Drafts", "PaymentDrafts", "Attachments2"} {
		if err := refuseLivePostInMart(set, "POST", "JIVO_MART_HANADB"); err != nil {
			t.Errorf("post %s in Mart must still work, got: %v", set, err)
		}
	}
}

// End to end through the real command: the refusal is wired into `post`, it
// fires before --dry-run and before --yes, and not one request reaches SAP.
func TestPostCommandRefusesLiveGRPOInMart(t *testing.T) {
	f := newFakeSAP(t)
	withTTY(t, false)
	for _, extra := range []string{"--yes", "--dry-run"} {
		_, _, err := execWrite(t, "", "post", "PurchaseDeliveryNotes", "--company", "JIVO_MART_HANADB", extra,
			"--data", `{"CardCode":"VENDA000001"}`)
		requireUsageError(t, err, "JIVO MART", "sapb1 draft grpo")
	}
	if f.hits != 0 {
		t.Fatalf("%d request(s) reached SAP; a refused Mart post must send nothing", f.hits)
	}
	// And the same command against Oil is untouched by the Mart rule.
	if _, _, err := execWrite(t, "", "post", "PurchaseDeliveryNotes", "--company", "JIVO_OIL_HANADB", "--dry-run",
		"--data", `{"CardCode":"VENDA000001"}`); err != nil {
		t.Errorf("post PurchaseDeliveryNotes --dry-run in Oil was refused; the Mart rule leaked: %v", err)
	}
}


// MaterialRevaluation was opened on Daman's instruction, 2026-09-19. It is the
// one posting document with no draft form in SAP, so the usual "use the draft
// instead" is not an option for it. These two tests pin what was opened and
// what was deliberately left shut, so neither drifts by accident.
func TestPostAllowsMaterialRevaluationOutsideMart(t *testing.T) {
	for _, spelling := range []string{"MaterialRevaluation", "materialrevaluation", "MATERIALREVALUATION"} {
		if _, err := validateWriteEntitySet(spelling, "POST"); err != nil {
			t.Errorf("post %q was refused, but the revaluation carve-out is open: %v", spelling, err)
		}
	}
}

func TestMartStillRefusesMaterialRevaluation(t *testing.T) {
	for _, company := range []string{"JIVO_MART_HANADB", "jivo_mart_hanadb", " JIVO_MART_HANADB "} {
		err := refuseLivePostInMart("MaterialRevaluation", "POST", company)
		if err == nil {
			t.Errorf("Mart accepted a live revaluation in %q — nothing in Mart posts straight to the ledger", company)
			continue
		}
		if !strings.Contains(err.Error(), "DRAFT") {
			t.Errorf("Mart refusal does not point at the draft route:\n%s", err)
		}
	}
	// ...and the other two books are not caught by the Mart rule.
	for _, company := range []string{"JIVO_OIL_HANADB", "JIVO_BEVERAGES_HANADB"} {
		if err := refuseLivePostInMart("MaterialRevaluation", "POST", company); err != nil {
			t.Errorf("%s was refused by the Mart rule: %v", company, err)
		}
	}
}
