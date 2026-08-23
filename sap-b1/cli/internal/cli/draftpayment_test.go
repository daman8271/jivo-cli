package cli

import (
	"errors"
	"strings"
	"testing"

	"sapb1/internal/errs"
)

// TestResolvePayObjectCode pins the accepted input shapes and the fact that the
// canonical output is always the bopot_ enum string — the spelling read back off
// live JIVO PaymentDrafts rows.
func TestResolvePayObjectCode(t *testing.T) {
	cases := []struct {
		in   string
		want string
	}{
		{"incoming", "bopot_IncomingPayments"},
		{"INCOMING", "bopot_IncomingPayments"},
		{"in", "bopot_IncomingPayments"},
		{"receipt", "bopot_IncomingPayments"},
		{"received", "bopot_IncomingPayments"},
		{"bopot_IncomingPayments", "bopot_IncomingPayments"},
		{"bopot_incomingpayments", "bopot_IncomingPayments"},
		{"24", "bopot_IncomingPayments"},
		{"  incoming  ", "bopot_IncomingPayments"},
		{"outgoing", "bopot_OutgoingPayments"},
		{"out", "bopot_OutgoingPayments"},
		{"vendor", "bopot_OutgoingPayments"},
		{"supplier", "bopot_OutgoingPayments"},
		{"bopot_OutgoingPayments", "bopot_OutgoingPayments"},
		{"46", "bopot_OutgoingPayments"},
	}
	for _, tc := range cases {
		got, err := resolvePayObjectCode(tc.in)
		if err != nil {
			t.Errorf("resolvePayObjectCode(%q) errored: %v", tc.in, err)
			continue
		}
		if got != tc.want {
			t.Errorf("resolvePayObjectCode(%q) = %q, want %q", tc.in, got, tc.want)
		}
	}
}

func TestResolvePayObjectCodeRejects(t *testing.T) {
	for _, in := range []string{"", "   ", "order", "invoice", "17", "oOrders", "nonsense"} {
		_, err := resolvePayObjectCode(in)
		if err == nil {
			t.Errorf("resolvePayObjectCode(%q) should have errored", in)
			continue
		}
		var ue *errs.UsageError
		if !errors.As(err, &ue) {
			t.Errorf("resolvePayObjectCode(%q) error should be a UsageError, got %T", in, err)
		}
	}
}

// TestPaymentDirectionsAreNotDocTypes is the guard against someone "helpfully"
// merging payments back into the doctype table. They address different SAP
// tables (OPDF vs ODRF) and the two resolvers must stay disjoint.
func TestPaymentDirectionsAreNotDocTypes(t *testing.T) {
	for _, pd := range payDirections() {
		if _, err := resolveDocObjectCode(pd.Name); err == nil {
			t.Errorf("%q resolves as a marketing doctype — payments must not leak into `draft <doctype>`", pd.Name)
		}
		if _, err := resolveDocObjectCode(pd.Enum); err == nil {
			t.Errorf("%q resolves as a marketing doctype", pd.Enum)
		}
	}
	// ...and no doctype may resolve as a payment direction.
	for _, dt := range draftDocTypes() {
		if _, err := resolvePayObjectCode(dt.Name); err == nil {
			t.Errorf("doctype %q resolves as a payment direction", dt.Name)
		}
	}
}

func TestValidatePaymentPayload(t *testing.T) {
	cases := []struct {
		name    string
		obj     map[string]interface{}
		wantErr string // substring; "" means it must pass
	}{
		{
			name: "supplier payment with CardCode",
			obj:  map[string]interface{}{"DocType": "rSupplier", "CardCode": "VENDA000224"},
		},
		{
			name: "customer receipt with CardCode",
			obj:  map[string]interface{}{"DocType": "rCustomer", "CardCode": "CUSTA000883"},
		},
		{
			name: "GL payment with no CardCode",
			obj:  map[string]interface{}{"DocType": "rAccount"},
		},
		{
			name: "GL payment with explicit null CardCode",
			obj:  map[string]interface{}{"DocType": "rAccount", "CardCode": nil},
		},
		{
			name:    "no DocType at all",
			obj:     map[string]interface{}{"CardCode": "VENDA000224"},
			wantErr: "no DocType",
		},
		{
			name:    "DocType SAP does not accept",
			obj:     map[string]interface{}{"DocType": "rVendor", "CardCode": "V1"},
			wantErr: "not one SAP accepts",
		},
		{
			name:    "supplier payment missing CardCode",
			obj:     map[string]interface{}{"DocType": "rSupplier"},
			wantErr: "needs a CardCode",
		},
		{
			name:    "customer receipt with blank CardCode",
			obj:     map[string]interface{}{"DocType": "rCustomer", "CardCode": "   "},
			wantErr: "needs a CardCode",
		},
		{
			name:    "GL payment that also names a party",
			obj:     map[string]interface{}{"DocType": "rAccount", "CardCode": "VENDA000224"},
			wantErr: "straight GL-account payment",
		},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			err := validatePaymentPayload(tc.obj)
			if tc.wantErr == "" {
				if err != nil {
					t.Fatalf("expected payload to pass, got: %v", err)
				}
				return
			}
			if err == nil {
				t.Fatalf("expected an error containing %q, got nil", tc.wantErr)
			}
			var ue *errs.UsageError
			if !errors.As(err, &ue) {
				t.Fatalf("error should be a UsageError, got %T", err)
			}
			if !strings.Contains(err.Error(), tc.wantErr) {
				t.Fatalf("error %q does not contain %q", err.Error(), tc.wantErr)
			}
		})
	}
}

// TestDocTypeCaseInsensitive — SAP's own spelling is rSupplier; operators type
// all sorts of things and the validator should accept the value, not the casing.
func TestValidatePaymentPayloadDocTypeCasing(t *testing.T) {
	for _, dt := range []string{"rsupplier", "RSUPPLIER", "rSupplier", " rSupplier "} {
		obj := map[string]interface{}{"DocType": dt, "CardCode": "VENDA000224"}
		if err := validatePaymentPayload(obj); err != nil {
			t.Errorf("DocType %q should be accepted: %v", dt, err)
		}
	}
}
