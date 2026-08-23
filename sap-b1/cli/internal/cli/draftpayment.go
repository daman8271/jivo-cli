package cli

import (
	"fmt"
	"sort"
	"strings"

	"github.com/spf13/cobra"

	"sapb1/internal/client"
	"sapb1/internal/errs"
)

// SAP keeps payment drafts in a DIFFERENT table from marketing-document drafts:
// ODRF holds the drafts behind `sapb1 draft order|invoice|grpo|…`, OPDF holds
// payment drafts. They are separate entity sets in the Service Layer too —
// Drafts vs PaymentDrafts — so a payment could never have been "one more row in
// the doctype table". It needs its own command, which is what this file is.
//
// What carries over unchanged is the safety shape: a PaymentDraft is inert.
// It does not move money, does not hit the bank account and does not touch the
// party ledger until a human opens SAP B1 → Banking → Payment Drafts, reviews
// it and presses Add. The CLI deliberately cannot press Add: the
// PaymentDrafts(id)/SaveDraftToDocument action is an OData action, and
// validateWriteEntitySet refuses every action by design.

// payDirection maps a friendly direction onto the BoPaymentsObjectType enum a
// PaymentDraft carries in its DocObjectCode field. Both enum strings below were
// read back off live JIVO rows, not taken from documentation.
type payDirection struct {
	Name    string   // friendly CLI name
	Aliases []string // extra friendly names
	Enum    string   // BoPaymentsObjectType enum string — what we send
	Code    string   // numeric object type
	Means   string   // one-line plain-English gloss for help text
}

func payDirections() []payDirection {
	return []payDirection{
		{
			Name:    "incoming",
			Aliases: []string{"in", "receipt", "received"},
			Enum:    "bopot_IncomingPayments",
			Code:    "24",
			Means:   "money coming IN — a receipt from a customer",
		},
		{
			Name:    "outgoing",
			Aliases: []string{"out", "vendor", "supplier"},
			Enum:    "bopot_OutgoingPayments",
			Code:    "46",
			Means:   "money going OUT — a payment to a vendor",
		},
	}
}

// payDocTypes is the set of values SAP accepts in a payment's DocType field —
// i.e. what is on the other side of the payment. Confirmed against live rows.
var payDocTypes = map[string]string{
	"rCustomer": "paid by / to a customer (CardCode required)",
	"rSupplier": "paid by / to a vendor (CardCode required)",
	"rAccount":  "straight to a GL account (CardCode must be empty)",
}

// resolvePayObjectCode turns whatever the operator typed — a friendly name
// ("outgoing", "vendor"), the enum verbatim, or the numeric code — into the
// canonical enum string. Matching is case-insensitive.
func resolvePayObjectCode(arg string) (string, error) {
	want := strings.ToLower(strings.TrimSpace(arg))
	if want == "" {
		return "", &errs.UsageError{Msg: "payment direction is required: `sapb1 draft payment incoming` or `sapb1 draft payment outgoing`"}
	}

	for _, pd := range payDirections() {
		if want == strings.ToLower(pd.Name) || want == strings.ToLower(pd.Enum) || want == pd.Code {
			return pd.Enum, nil
		}
		for _, a := range pd.Aliases {
			if want == strings.ToLower(a) {
				return pd.Enum, nil
			}
		}
	}

	return "", &errs.UsageError{Msg: fmt.Sprintf(
		"unknown payment direction %q — use %s (the bopot_ enum or the numeric code work too)",
		arg, payDirectionNames())}
}

func payDirectionNames() string {
	var names []string
	for _, pd := range payDirections() {
		names = append(names, pd.Name)
		names = append(names, pd.Aliases...)
	}
	return strings.Join(names, ", ")
}

// payDirectionTable renders the direction map for `sapb1 draft payment --help`.
func payDirectionTable() string {
	var b strings.Builder
	for _, pd := range payDirections() {
		name := pd.Name
		for _, a := range pd.Aliases {
			name += "|" + a
		}
		fmt.Fprintf(&b, "  %-30s %-26s %s\n", name, pd.Enum, pd.Means)
	}
	return strings.TrimRight(b.String(), "\n")
}

// payDocTypeTable renders the DocType map for help text, in a stable order.
func payDocTypeTable() string {
	keys := make([]string, 0, len(payDocTypes))
	for k := range payDocTypes {
		keys = append(keys, k)
	}
	sort.Strings(keys)

	var b strings.Builder
	for _, k := range keys {
		fmt.Fprintf(&b, "  %-12s %s\n", k, payDocTypes[k])
	}
	return strings.TrimRight(b.String(), "\n")
}

func newDraftPaymentCmd() *cobra.Command {
	var wf writeFlags

	cmd := &cobra.Command{
		Use:   "payment <direction>",
		Short: "Create a PAYMENT draft in SAP (incoming receipt or outgoing payment)",
		Long: `payment creates a row in SAP's PaymentDrafts table (OPDF).

This is the payment equivalent of ` + "`sapb1 draft <doctype>`" + `, and it is a
SEPARATE command for a real reason: SAP stores payment drafts in a different
table from marketing-document drafts, so a payment is not a document type you
can pass to ` + "`sapb1 draft`" + ` — it addresses its own entity set.

The safety shape is identical. A payment draft moves no money, touches no bank
account and posts nothing to the party ledger. It becomes real only when a human
opens SAP B1 → Banking → Payment Drafts, reviews it and presses Add. This CLI
cannot press Add: that is an OData action, and actions are refused by design.

DIRECTION — what the payment does (case-insensitive; enum or numeric code also work):

` + payDirectionTable() + `

DocType — who is on the other side. Put this in your payload:

` + payDocTypeTable() + `

Your payload goes out byte for byte as you wrote it, with DocObjectCode spliced
in if you left it out. Use --dry-run to see the exact request without sending
anything. Otherwise the write is previewed and confirmed (or pass --yes), and
every attempt is appended to the write log.

SERIES: payment series at JIVO are MONTHLY and shared across branches — unlike
A/P invoice series, which are per-branch (correction C-0018). If you omit Series
this command warns rather than guessing, because picking a series is a posting
decision, not a formatting one.`,
		Example: exampleBlock(
			`sapb1 draft payment outgoing --dry-run --data '{"DocType":"rSupplier","CardCode":"VENDA000224","DocDate":"2026-08-22","Series":2600,"TransferSum":4684341}'`,
			`sapb1 draft payment incoming --data '{"DocType":"rCustomer","CardCode":"CUSTA000883","TransferSum":2800000}'`,
			`sapb1 draft payment outgoing --data-file awl-advance.json --yes`,
			`sapb1 draft payment out --company JIVO_MART_HANADB --data-file pay.json --dry-run`,
		),
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			return runDraftPayment(cmd, args[0], wf)
		},
	}

	addWriteFlags(cmd, &wf)
	return cmd
}

func runDraftPayment(cmd *cobra.Command, directionArg string, wf writeFlags) error {
	cfg, err := writeConfig(cmd)
	if err != nil {
		return err
	}

	objectCode, err := resolvePayObjectCode(directionArg)
	if err != nil {
		return err
	}

	payload, obj, err := loadPayload(cmd, wf)
	if err != nil {
		return err
	}

	// Same rule as `draft`: accept DocObjectCode when it agrees, refuse when it
	// contradicts the command line, splice it in when it's absent. Guessing which
	// one the operator meant is not our call.
	if raw, ok := obj["DocObjectCode"]; ok && raw != nil {
		given := formatCell(raw)
		inPayload, err := resolvePayObjectCode(given)
		if err != nil {
			return &errs.UsageError{Msg: fmt.Sprintf("payload has DocObjectCode %q, which is not a payment direction I recognize: %v", given, err)}
		}
		if inPayload != objectCode {
			return &errs.UsageError{Msg: fmt.Sprintf("payment direction mismatch: you asked for %s (%s) but the payload says DocObjectCode %q (%s) — drop one of them",
				directionArg, objectCode, given, inPayload)}
		}
	} else {
		if payload, err = spliceJSONField(payload, "DocObjectCode", objectCode); err != nil {
			return err
		}
	}

	if err := validatePaymentPayload(obj); err != nil {
		return err
	}
	warnPaymentPayload(cmd, obj)

	if wf.dryRun {
		return renderDryRun(cmd, cfg, "POST", "PaymentDrafts", payload)
	}

	if err := confirmWrite(cmd, cfg, "POST", "PaymentDrafts", payload, wf.yes, stdinIsTTYFunc(), true); err != nil {
		return err
	}

	c := client.New(cfg)
	c.SetErrWriter(cmd.ErrOrStderr())
	res, err := c.Create(cmd.Context(), "PaymentDrafts", payload)
	if err != nil {
		return err
	}

	summary := func(created map[string]interface{}) string {
		keys := describeKeys(created)
		if keys == "" {
			keys = fmt.Sprintf("HTTP %d", res.Status)
		}
		return fmt.Sprintf("Payment draft created in %s: %s (%s). Open SAP B1 → Banking → Payment Drafts → review → Add. No money has moved.",
			cfg.CompanyDB, keys, objectCode)
	}

	// In --json mode stdout is SAP's object, so the instruction that actually
	// matters — a human still has to Add this — goes to stderr instead of being
	// dropped.
	if cfg.JSON {
		fmt.Fprintln(cmd.ErrOrStderr(), summary(decodeWriteObject(res.Body)))
	}

	return renderWriteResult(cmd.OutOrStdout(), res, cfg.JSON, summary)
}

// validatePaymentPayload catches the payload shapes SAP will either reject or,
// worse, accept into a draft that a human then has to unpick. Both rules below
// come from live JIVO rows, not from guesswork: every rAccount payment draft in
// the Oil book carries a null CardCode, and every rCustomer/rSupplier one
// carries a CardCode.
func validatePaymentPayload(obj map[string]interface{}) error {
	raw, ok := obj["DocType"]
	if !ok || raw == nil {
		return &errs.UsageError{Msg: fmt.Sprintf(
			"payload has no DocType — a payment has to say who is on the other side. Valid values:\n%s",
			payDocTypeTable())}
	}

	docType := strings.TrimSpace(formatCell(raw))
	canonical := ""
	for k := range payDocTypes {
		if strings.EqualFold(k, docType) {
			canonical = k
			break
		}
	}
	if canonical == "" {
		return &errs.UsageError{Msg: fmt.Sprintf(
			"DocType %q is not one SAP accepts on a payment. Valid values:\n%s",
			docType, payDocTypeTable())}
	}

	cardCode := ""
	if v, ok := obj["CardCode"]; ok && v != nil {
		cardCode = strings.TrimSpace(formatCell(v))
	}

	switch canonical {
	case "rCustomer", "rSupplier":
		if cardCode == "" {
			return &errs.UsageError{Msg: fmt.Sprintf(
				"DocType %s needs a CardCode — a party payment with no party would land against nobody's ledger", canonical)}
		}
	case "rAccount":
		if cardCode != "" {
			return &errs.UsageError{Msg: fmt.Sprintf(
				"DocType rAccount is a straight GL-account payment, but the payload also has CardCode %q — "+
					"use rSupplier/rCustomer to pay a party, or drop CardCode to pay the account", cardCode)}
		}
	}

	return nil
}

// warnPaymentPayload prints non-blocking cautions to stderr before the preview.
// These are judgement calls, not errors: the operator may have a good reason,
// and this command's job is to make sure they SAW it, not to overrule them.
func warnPaymentPayload(cmd *cobra.Command, obj map[string]interface{}) {
	errOut := cmd.ErrOrStderr()

	if v, ok := obj["Series"]; !ok || v == nil {
		fmt.Fprintln(errOut, "note: no Series in the payload — SAP will fall back to its default series for this company.")
		fmt.Fprintln(errOut, "      JIVO payment series are monthly (and shared across branches). Check the series in")
		fmt.Fprintln(errOut, "      use this month before you Add the draft, or pass Series explicitly.")
	}

	// A payment with no money on it is legal JSON and a useless draft. Every
	// amount field SAP offers is optional on its own, so the only sane check is
	// "did you put an amount on ANY of the legs".
	amountLegs := []string{"TransferSum", "CashSum", "BillOfExchangeAmount"}
	hasAmount := false
	for _, k := range amountLegs {
		if v, ok := obj[k]; ok && v != nil && formatCell(v) != "0" {
			hasAmount = true
			break
		}
	}
	if _, ok := obj["PaymentChecks"]; ok {
		hasAmount = true
	}
	if _, ok := obj["PaymentCreditCards"]; ok {
		hasAmount = true
	}
	if !hasAmount {
		fmt.Fprintf(errOut, "note: no amount found on any payment leg (%s, PaymentChecks, PaymentCreditCards) — this draft would carry zero.\n",
			strings.Join(amountLegs, ", "))
	}

	// The allocation question: against specific bills, or on account.
	_, hasInvoices := obj["PaymentInvoices"]
	_, hasAccounts := obj["PaymentAccounts"]
	if !hasInvoices && !hasAccounts {
		fmt.Fprintln(errOut, "note: no PaymentInvoices and no PaymentAccounts — this is an ON-ACCOUNT payment (an advance),")
		fmt.Fprintln(errOut, "      not an allocation against specific open bills. If you meant to settle particular")
		fmt.Fprintln(errOut, "      invoices, add PaymentInvoices with their DocEntry and SumApplied.")
	}
}
