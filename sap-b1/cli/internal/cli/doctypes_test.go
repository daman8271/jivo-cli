package cli

import (
	"errors"
	"strings"
	"testing"

	"sapb1/internal/errs"
)

// TestResolveDocObjectCode pins the four accepted input shapes (friendly name,
// entity set, enum verbatim, numeric code), case-insensitivity, and the fact
// that the canonical output is always the enum string.
func TestResolveDocObjectCode(t *testing.T) {
	cases := []struct {
		in   string
		want string
	}{
		{"order", "oOrders"},
		{"ORDER", "oOrders"},
		{"Orders", "oOrders"},
		{"oOrders", "oOrders"},
		{"oorders", "oOrders"},
		{"17", "oOrders"},
		{"  order  ", "oOrders"},
		{"quotation", "oQuotations"},
		{"23", "oQuotations"},
		{"invoice", "oInvoices"},
		{"credit-note", "oCreditNotes"},
		{"delivery", "oDeliveryNotes"},
		{"return", "oReturns"},
		{"purchase-order", "oPurchaseOrders"},
		{"PurchaseOrders", "oPurchaseOrders"},
		{"22", "oPurchaseOrders"},
		{"grpo", "oPurchaseDeliveryNotes"},
		{"goods-receipt-po", "oPurchaseDeliveryNotes"},
		{"purchase-return", "oPurchaseReturns"},
		{"purchase-invoice", "oPurchaseInvoices"},
		{"purchase-credit-note", "oPurchaseCreditNotes"},
		{"purchase-quotation", "oPurchaseQuotations"},
		{"540000006", "oPurchaseQuotations"},
		{"down-payment", "oDownPayments"},
		{"purchase-down-payment", "oPurchaseDownPayments"},
		{"204", "oPurchaseDownPayments"},
	}
	for _, tc := range cases {
		got, err := resolveDocObjectCode(tc.in)
		if err != nil {
			t.Errorf("resolveDocObjectCode(%q) errored: %v", tc.in, err)
			continue
		}
		if got != tc.want {
			t.Errorf("resolveDocObjectCode(%q) = %q, want %q", tc.in, got, tc.want)
		}
	}
}

func TestResolveDocObjectCodeUnknown(t *testing.T) {
	for _, in := range []string{"", "   ", "orderz", "oNope", "999999"} {
		_, err := resolveDocObjectCode(in)
		if err == nil {
			t.Errorf("resolveDocObjectCode(%q) should fail", in)
			continue
		}
		var usageErr *errs.UsageError
		if !errors.As(err, &usageErr) {
			t.Errorf("resolveDocObjectCode(%q) = %T, want *errs.UsageError", in, err)
			continue
		}
		// The error must be actionable: list what IS valid.
		if !strings.Contains(usageErr.Msg, "order") || !strings.Contains(usageErr.Msg, "purchase-order") {
			t.Errorf("error for %q should list valid names, got: %s", in, usageErr.Msg)
		}
	}
}

// TestDraftDocTypesAreDistinct guards against a copy-paste slip in the table.
func TestDraftDocTypesAreDistinct(t *testing.T) {
	seen := map[string]string{}
	for _, dt := range draftDocTypes() {
		for _, key := range append([]string{dt.Name, dt.EntitySet, dt.Enum, dt.Code}, dt.Aliases...) {
			k := strings.ToLower(key)
			if prev, dup := seen[k]; dup {
				t.Errorf("duplicate doc-type key %q (%s and %s)", key, prev, dt.Name)
			}
			seen[k] = dt.Name
		}
		if dt.Enum == "" || dt.EntitySet == "" || dt.Code == "" {
			t.Errorf("doc type %q has an empty field: %+v", dt.Name, dt)
		}
	}
}
