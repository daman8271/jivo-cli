package cli

import (
	"fmt"
	"strings"

	"sapb1/internal/errs"
)

// docType maps one marketing document onto the three names SAP uses for it:
// the OData entity set you'd read it from, the BoObjectTypes enum string, and
// the numeric object type behind that enum.
//
// A Draft carries the type of the document it will become in its
// DocObjectCode field, so `sapb1 draft order` has to translate "order" into
// something the Service Layer accepts. The enum STRING is what we send —
// that's the documented representation the Service Layer emits and accepts for
// BoObjectTypes — but the numeric code is accepted on input too, so an
// operator who read it off a SAP screen or an older report isn't stuck.
type docType struct {
	Name      string   // friendly CLI name, e.g. "order"
	Aliases   []string // extra friendly names, e.g. "goods-receipt-po"
	EntitySet string   // OData entity set, e.g. "Orders"
	Enum      string   // BoObjectTypes enum string, e.g. "oOrders" — what we send
	Code      string   // numeric object type, e.g. "17"
}

// draftDocTypes is the set of document types `sapb1 draft` can create. Sales
// documents first, then purchasing, then down payments — the order they're
// listed in help.
func draftDocTypes() []docType {
	return []docType{
		{Name: "quotation", EntitySet: "Quotations", Enum: "oQuotations", Code: "23"},
		{Name: "order", EntitySet: "Orders", Enum: "oOrders", Code: "17"},
		{Name: "delivery", EntitySet: "DeliveryNotes", Enum: "oDeliveryNotes", Code: "15"},
		{Name: "return", EntitySet: "Returns", Enum: "oReturns", Code: "16"},
		{Name: "invoice", EntitySet: "Invoices", Enum: "oInvoices", Code: "13"},
		{Name: "credit-note", EntitySet: "CreditNotes", Enum: "oCreditNotes", Code: "14"},
		{Name: "purchase-quotation", EntitySet: "PurchaseQuotations", Enum: "oPurchaseQuotations", Code: "540000006"},
		{Name: "purchase-order", EntitySet: "PurchaseOrders", Enum: "oPurchaseOrders", Code: "22"},
		{Name: "grpo", Aliases: []string{"goods-receipt-po"}, EntitySet: "PurchaseDeliveryNotes", Enum: "oPurchaseDeliveryNotes", Code: "20"},
		{Name: "purchase-return", EntitySet: "PurchaseReturns", Enum: "oPurchaseReturns", Code: "21"},
		{Name: "purchase-invoice", EntitySet: "PurchaseInvoices", Enum: "oPurchaseInvoices", Code: "18"},
		{Name: "purchase-credit-note", EntitySet: "PurchaseCreditNotes", Enum: "oPurchaseCreditNotes", Code: "19"},
		{Name: "down-payment", EntitySet: "DownPayments", Enum: "oDownPayments", Code: "203"},
		{Name: "purchase-down-payment", EntitySet: "PurchaseDownPayments", Enum: "oPurchaseDownPayments", Code: "204"},
	}
}

// resolveDocObjectCode turns whatever the operator typed — a friendly name
// ("order", "grpo"), the entity set ("Orders"), the enum verbatim ("oOrders"),
// or the numeric code ("17") — into the canonical enum string to put in a
// Draft's DocObjectCode. Matching is case-insensitive.
func resolveDocObjectCode(arg string) (string, error) {
	want := strings.ToLower(strings.TrimSpace(arg))
	if want == "" {
		return "", &errs.UsageError{Msg: "document type is required, e.g. `sapb1 draft order` — valid types: " + docTypeNames()}
	}

	for _, dt := range draftDocTypes() {
		if want == strings.ToLower(dt.Name) ||
			want == strings.ToLower(dt.EntitySet) ||
			want == strings.ToLower(dt.Enum) ||
			want == dt.Code {
			return dt.Enum, nil
		}
		for _, a := range dt.Aliases {
			if want == strings.ToLower(a) {
				return dt.Enum, nil
			}
		}
	}

	return "", &errs.UsageError{Msg: fmt.Sprintf("unknown document type %q — valid types: %s (the entity set, the oXxx enum, or the numeric code work too)", arg, docTypeNames())}
}

// docTypeNames lists the friendly names for help text and error messages.
func docTypeNames() string {
	var names []string
	for _, dt := range draftDocTypes() {
		names = append(names, dt.Name)
		names = append(names, dt.Aliases...)
	}
	return strings.Join(names, ", ")
}

// docTypeTable renders the doc-type map as aligned lines for `sapb1 draft --help`.
func docTypeTable() string {
	var b strings.Builder
	for _, dt := range draftDocTypes() {
		name := dt.Name
		for _, a := range dt.Aliases {
			name += "|" + a
		}
		fmt.Fprintf(&b, "  %-22s %-22s %s\n", name, dt.EntitySet, dt.Enum)
	}
	return strings.TrimRight(b.String(), "\n")
}
