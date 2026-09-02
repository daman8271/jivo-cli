package main

import (
	"encoding/json"
	"math"
	"sort"
	"strconv"
	"strings"
	"time"
)

// normalise.go turns portal bodies into the record shape docs/comparison-spec.md
// specifies, so a later reconciliation can diff them against a HANA query
// without knowing anything about GST's field names.
//
// Three rules, all from the spec:
//   - Amounts are numbers with two decimals, never strings, never crores.
//   - Dates are ISO YYYY-MM-DD. The portal's "-" placeholder becomes null, not
//     "1970-01-01" and not "".
//   - The five tax keys are always taxable_value, igst, cgst, sgst, cess, even
//     when the portal calls them txval/iamt/camt/samt/csamt (GSTR-3B) or
//     txval/igst/cgst/sgst/cess (GSTR-2B) or *TaxAmt (the credit ledger).
//
// Records are map[string]any deliberately: json.Marshal sorts map keys, so the
// .jsonl output is byte-stable and a golden test is meaningful.

// record is one line of output.
type record = map[string]any

// envelope is the per-pull context every record carries (spec §3).
type envelope struct {
	GSTIN     string
	StateCode string
	Period    string         // "" → null (ledgers are not period-scoped)
	FY        string         //
	PulledAt  string         // RFC3339 with the IST offset
	Endpoint  string         // which allowlist row produced it
	Filing    map[string]any // nil → null (ledgers have no filing)
}

func newEnvelope(reg Registration, endpoint string) envelope {
	return envelope{
		GSTIN:     reg.GSTIN,
		StateCode: reg.StateCode(),
		PulledAt:  nowIST().Format(time.RFC3339),
		Endpoint:  endpoint,
	}
}

func (e envelope) withPeriod(period string) envelope {
	e.Period = period
	e.FY = fyOfPeriod(period)
	return e
}

func (e envelope) withEndpoint(endpoint string) envelope {
	e.Endpoint = endpoint
	return e
}

// rec builds one record: the envelope, then the record's own fields.
func (e envelope) rec(form, section, kind string, fields record) record {
	out := record{
		"src":         "gst-portal",
		"gstin":       e.GSTIN,
		"state_code":  e.StateCode,
		"period":      nilIfEmpty(e.Period),
		"fy":          nilIfEmpty(e.FY),
		"form":        form,
		"record_kind": kind,
		"pulled_at":   e.PulledAt,
		"filing":      nilIfEmptyMap(e.Filing),
		"portal_ref":  record{"endpoint": e.Endpoint, "raw_id": nil},
	}
	if section != "" {
		out["section"] = section
	}
	for k, v := range fields {
		out[k] = v
	}
	return out
}

// ---- shared portal shapes --------------------------------------------------

// taxHeads is GSTR-2B's spelling of the five amounts.
type taxHeads struct {
	Txval float64 `json:"txval"`
	IGST  float64 `json:"igst"`
	CGST  float64 `json:"cgst"`
	SGST  float64 `json:"sgst"`
	Cess  float64 `json:"cess"`
}

func (t taxHeads) total() float64 { return t.IGST + t.CGST + t.SGST + t.Cess }

func (t taxHeads) fields() record {
	return record{
		"taxable_value": r2(t.Txval), "igst": r2(t.IGST), "cgst": r2(t.CGST),
		"sgst": r2(t.SGST), "cess": r2(t.Cess),
	}
}

// amtHeads is GSTR-3B's spelling of the same five.
type amtHeads struct {
	Txval float64 `json:"txval"`
	Iamt  float64 `json:"iamt"`
	Camt  float64 `json:"camt"`
	Samt  float64 `json:"samt"`
	Csamt float64 `json:"csamt"`
}

func (a amtHeads) fields(withTaxable bool) record {
	out := record{"igst": r2(a.Iamt), "cgst": r2(a.Camt), "sgst": r2(a.Samt), "cess": r2(a.Csamt)}
	if withTaxable {
		out["taxable_value"] = r2(a.Txval)
	}
	return out
}

// minorHeads is the cash ledger's per-head breakdown (tax/interest/penalty/fee).
type minorHeads struct {
	Tx   float64 `json:"tx"`
	Intr float64 `json:"intr"`
	Pen  float64 `json:"pen"`
	Fee  float64 `json:"fee"`
	Oth  float64 `json:"oth"`
	Tot  float64 `json:"tot"`
}

func (m minorHeads) fields() record {
	return record{"tax": r2(m.Tx), "interest": r2(m.Intr), "penalty": r2(m.Pen),
		"fee": r2(m.Fee), "other": r2(m.Oth), "total": r2(m.Tot)}
}

// ---- FILING ----------------------------------------------------------------

// normFiled converts the filed-returns register (POST efiledReturns) into one
// FILING/status record per period.
func normFiled(e envelope, raw json.RawMessage) []record {
	var rows []struct {
		RtnType  string `json:"rtntype"`
		FY       string `json:"fy"`
		Taxp     string `json:"taxp"`
		ARN      string `json:"arn"`
		DOF      string `json:"dof"`
		MOF      string `json:"mof"`
		FiledBy  string `json:"filedBy"`
		Designat string `json:"dg"`
	}
	if err := json.Unmarshal(raw, &rows); err != nil {
		return nil
	}
	out := make([]record, 0, len(rows))
	for _, r := range rows {
		env := e
		if p := periodOf(r.Taxp, r.FY); p != "" {
			env = e.withPeriod(p)
		} else {
			env.FY = r.FY
		}
		out = append(out, env.rec("FILING", "", "status", record{
			"return_type":  r.RtnType,
			"status":       "FIL",
			"arn":          nilIfEmpty(r.ARN),
			"filed_on":     isoOrNil(r.DOF),
			"due_on":       nil,
			"days_late":    nil,
			"mode":         nilIfEmpty(r.MOF),
			"filed_by":     nilIfEmpty(r.FiledBy),
			"designation":  nilIfEmpty(r.Designat),
			"nil_return":   nil,
			"tax_period":   r.Taxp,
			"source_table": "efiledReturns",
		}))
	}
	return out
}

// normFormDetails converts formdetails (ARN + fil_dt + due_dt for one form in
// one period) into a FILING/status record, with days_late computed.
func normFormDetails(e envelope, form string, raw json.RawMessage) []record {
	var v struct {
		Data struct {
			GSTIN  string `json:"gstin"`
			FP     string `json:"fp"`
			FY     string `json:"fy"`
			Status string `json:"status"`
			FilDt  string `json:"fil_dt"`
			DueDt  string `json:"due_dt"`
			ARN    string `json:"arn"`
		} `json:"data"`
	}
	if err := json.Unmarshal(raw, &v); err != nil || v.Data.Status == "" {
		return nil
	}
	d := v.Data
	env := e
	if d.FP != "" {
		env = e.withPeriod(d.FP)
	}
	rec := record{
		"return_type": form,
		"status":      d.Status,
		"arn":         nilIfEmpty(d.ARN),
		"filed_on":    isoOrNil(d.FilDt),
		"due_on":      isoOrNil(d.DueDt),
		"days_late":   daysLate(d.DueDt, d.FilDt),
	}
	return []record{env.rec("FILING", "", "status", rec)}
}

// daysLate is filing date minus due date in whole days, or nil if either is
// missing. Negative means filed early; the spec wants the signed number.
func daysLate(due, filed string) any {
	d, err1 := parsePortalDate(due)
	f, err2 := parsePortalDate(filed)
	if err1 != nil || err2 != nil {
		return nil
	}
	return int(f.Sub(d).Hours() / 24)
}

// ---- LEDGER_CASH -----------------------------------------------------------

func normCashBalance(e envelope, raw json.RawMessage) []record {
	var v struct {
		TotRngBal float64    `json:"tot_rng_bal"`
		IGST      minorHeads `json:"igst"`
		CGST      minorHeads `json:"cgst"`
		SGST      minorHeads `json:"sgst"`
		Cess      minorHeads `json:"cess"`
	}
	if err := json.Unmarshal(raw, &v); err != nil {
		return nil
	}
	return []record{e.rec("LEDGER_CASH", "", "balance", record{
		"as_of": isoDate(nowIST()),
		"heads": record{
			"igst": v.IGST.fields(), "cgst": v.CGST.fields(),
			"sgst": v.SGST.fields(), "cess": v.Cess.fields(),
		},
		"total": r2(v.TotRngBal),
	})}
}

func normCashLedger(e envelope, raw json.RawMessage) []record {
	var v struct {
		Tr []struct {
			RetPeriod string     `json:"ret_period"`
			Desc      string     `json:"desc"`
			RefNo     string     `json:"ref_no"`
			TrTyp     string     `json:"tr_typ"`
			DptDt     string     `json:"dpt_dt"`
			RptDt     string     `json:"rpt_dt"`
			TotTrAmt  float64    `json:"tot_tr_amt"`
			TotRngBal float64    `json:"tot_rng_bal"`
			IGST      minorHeads `json:"igst"`
			CGST      minorHeads `json:"cgst"`
			SGST      minorHeads `json:"sgst"`
			Cess      minorHeads `json:"cess"`
			IGSTBal   minorHeads `json:"igstbal"`
			CGSTBal   minorHeads `json:"cgstbal"`
			SGSTBal   minorHeads `json:"sgstbal"`
			CessBal   minorHeads `json:"cessbal"`
		} `json:"tr"`
	}
	if err := json.Unmarshal(raw, &v); err != nil {
		return nil
	}
	out := make([]record, 0, len(v.Tr))
	for _, t := range v.Tr {
		date := firstNonDash(t.DptDt, t.RptDt)
		out = append(out, e.rec("LEDGER_CASH", "", "ledger_entry", record{
			"entry_date":  isoOrNil(date),
			"ref_no":      nilIfDash(t.RefNo),
			"ref_type":    cashRefType(t.Desc, t.RefNo),
			"description": t.Desc,
			"txn_type":    strings.ToUpper(nz(t.TrTyp)),
			"entry_class": cashEntryClass(t.Desc),
			"ret_period":  nilIfDash(t.RetPeriod),
			"amount":      r2(t.TotTrAmt),
			"heads":       record{"igst": t.IGST.fields(), "cgst": t.CGST.fields(), "sgst": t.SGST.fields(), "cess": t.Cess.fields()},
			"balance_after": record{"igst": t.IGSTBal.fields(), "cgst": t.CGSTBal.fields(),
				"sgst": t.SGSTBal.fields(), "cess": t.CessBal.fields(), "total": r2(t.TotRngBal)},
		}))
	}
	return out
}

// cashEntryClass classifies a cash-ledger line from its description. The raw
// description is always kept alongside — this is a convenience, not a truth.
func cashEntryClass(desc string) string {
	d := strings.ToLower(desc)
	switch {
	case strings.Contains(d, "opening balance"):
		return "OPENING"
	case strings.Contains(d, "deposit"):
		return "DEPOSIT"
	case strings.Contains(d, "closing balance"):
		return "CLOSING"
	case strings.Contains(d, "refund"):
		return "REFUND"
	case isReversal(d):
		return "REVERSAL"
	case d != "":
		return "UTILISATION"
	}
	return "OTHER"
}

func cashRefType(desc, ref string) any {
	if ref == "" || ref == "-" {
		return nil
	}
	d := strings.ToLower(desc)
	switch {
	case strings.Contains(d, "deposit"):
		return "CHALLAN"
	case strings.HasPrefix(strings.ToUpper(ref), "AA") || strings.HasPrefix(strings.ToUpper(ref), "AB"):
		return "ARN"
	}
	return "OTHER"
}

// ---- LEDGER_CREDIT ---------------------------------------------------------

func normCreditBalance(e envelope, raw json.RawMessage) []record {
	var v struct {
		OpTot      float64 `json:"op_tot"`
		IGSTBal    float64 `json:"igstTaxBal"`
		CGSTBal    float64 `json:"cgstTaxBal"`
		SGSTBal    float64 `json:"sgstTaxBal"`
		CessBal    float64 `json:"cessTaxBal"`
		BlockTotal float64 `json:"blockTotBal"`
	}
	if err := json.Unmarshal(raw, &v); err != nil {
		return nil
	}
	// The body's `dt` field is deliberately ignored: it came back as
	// "16/02/0027" on a live pull. as_of is our own clock.
	return []record{e.rec("LEDGER_CREDIT", "", "balance", record{
		"as_of":   isoDate(nowIST()),
		"igst":    r2(v.IGSTBal),
		"cgst":    r2(v.CGSTBal),
		"sgst":    r2(v.SGSTBal),
		"cess":    r2(v.CessBal),
		"blocked": r2(v.BlockTotal),
		"total":   r2(v.OpTot),
	})}
}

func normCreditLedger(e envelope, raw json.RawMessage) []record {
	var v struct {
		Tr []struct {
			Dt        string  `json:"dt"`
			RefNo     string  `json:"ref_no"`
			Desc      string  `json:"desc"`
			TrTyp     string  `json:"tr_typ"`
			RetPeriod string  `json:"ret_period"`
			IGSTAmt   float64 `json:"igstTaxAmt"`
			CGSTAmt   float64 `json:"cgstTaxAmt"`
			SGSTAmt   float64 `json:"sgstTaxAmt"`
			CessAmt   float64 `json:"cessTaxAmt"`
			IGSTBal   float64 `json:"igstTaxBal"`
			CGSTBal   float64 `json:"cgstTaxBal"`
			SGSTBal   float64 `json:"sgstTaxBal"`
			CessBal   float64 `json:"cessTaxBal"`
			TotTrAmt  float64 `json:"tot_tr_amt"`
			TotRngBal float64 `json:"tot_rng_bal"`
		} `json:"tr"`
	}
	if err := json.Unmarshal(raw, &v); err != nil {
		return nil
	}
	out := make([]record, 0, len(v.Tr))
	for _, t := range v.Tr {
		out = append(out, e.rec("LEDGER_CREDIT", "", "ledger_entry", record{
			"entry_date":  isoOrNil(t.Dt),
			"ref_no":      nilIfDash(t.RefNo),
			"ref_type":    creditRefType(t.RefNo),
			"description": t.Desc,
			"txn_type":    strings.ToUpper(nz(t.TrTyp)),
			"entry_class": creditEntryClass(t.Desc, t.TrTyp),
			"ret_period":  nilIfDash(t.RetPeriod),
			"igst":        r2(t.IGSTAmt),
			"cgst":        r2(t.CGSTAmt),
			"sgst":        r2(t.SGSTAmt),
			"cess":        r2(t.CessAmt),
			"amount":      r2(t.TotTrAmt),
			"balance_after": record{"igst": r2(t.IGSTBal), "cgst": r2(t.CGSTBal),
				"sgst": r2(t.SGSTBal), "cess": r2(t.CessBal), "total": r2(t.TotRngBal)},
		}))
	}
	return out
}

// creditEntryClass maps a credit-ledger line to the spec's entry_class
// vocabulary: AVAILED | UTILISATION | REVERSAL | REFUND | TRANSITION | OTHER
// (plus OPENING for the statement's first row).
func creditEntryClass(desc, trTyp string) string {
	d := strings.ToLower(desc)
	switch {
	case strings.Contains(d, "opening balance"):
		return "OPENING"
	case strings.Contains(d, "closing balance"):
		return "CLOSING"
	case strings.Contains(d, "accrued") || strings.Contains(d, "availed"):
		return "AVAILED"
	case isReversal(d):
		return "REVERSAL"
	case strings.Contains(d, "refund"):
		return "REFUND"
	case strings.Contains(d, "transition") || strings.Contains(d, "trans-1") || strings.Contains(d, "tran-1"):
		return "TRANSITION"
	case strings.EqualFold(trTyp, "Dr"):
		return "UTILISATION"
	case strings.EqualFold(trTyp, "Cr"):
		return "AVAILED"
	}
	return "OTHER"
}

// isReversal has to be careful with one phrase. The credit ledger's ordinary
// set-off lines are described "Other than reverse charge" — a substring match on
// "revers" tags every monthly utilisation as a REVERSAL, which would tell
// Accounts that ITC was given back when in fact it was spent. "reverse charge"
// is about RCM and never means a reversal.
func isReversal(lowerDesc string) bool {
	d := strings.ReplaceAll(lowerDesc, "reverse charge", "")
	return strings.Contains(d, "revers")
}

func creditRefType(ref string) any {
	r := strings.ToUpper(strings.TrimSpace(ref))
	switch {
	case r == "" || r == "-":
		return nil
	case strings.HasPrefix(r, "AA"), strings.HasPrefix(r, "AB"), strings.HasPrefix(r, "AD"):
		return "ARN"
	case strings.Contains(r, "DRC"):
		return "DRC"
	}
	return "OTHER"
}

// ---- GSTR-3B ---------------------------------------------------------------

// gstr3bRows maps table 3.1's five sub-rows to the spec's row names.
var gstr3bRows = []struct{ key, row string }{
	{"osup_det", "a_outward_taxable"},
	{"osup_zero", "b_outward_zero_rated"},
	{"osup_nil_exmp", "c_outward_nil_exempt"},
	{"isup_rev", "d_inward_reverse_charge"},
	{"osup_nongst", "e_non_gst_outward"},
}

// itcAvlRows maps table 4(A)'s `ty` codes to the spec's row names.
var itcAvlRows = map[string]string{
	"IMPG": "A1_import_goods", "IMPS": "A2_import_services",
	"ISRC": "A3_reverse_charge", "ISD": "A4_isd", "OTH": "A5_all_other_itc",
}

var itcRevRows = map[string]string{"RUL": "B1_rules_reversal", "OTH": "B2_other_reversal"}
var itcInelgRows = map[string]string{"RUL": "D1_rules_ineligible", "OTH": "D2_other_ineligible"}

func normGSTR3B(e envelope, raw json.RawMessage) []record {
	var v struct {
		Data struct {
			RetPeriod  string              `json:"ret_period"`
			SupDetails map[string]amtHeads `json:"sup_details"`
			InterSup   struct {
				Unreg []posRow `json:"unreg_details"`
				Comp  []posRow `json:"comp_details"`
				UIN   []posRow `json:"uin_details"`
			} `json:"inter_sup"`
			ItcElg struct {
				ItcAvl   []tyRow  `json:"itc_avl"`
				ItcRev   []tyRow  `json:"itc_rev"`
				ItcNet   amtHeads `json:"itc_net"`
				ItcInelg []tyRow  `json:"itc_inelg"`
			} `json:"itc_elg"`
			InwardSup struct {
				Details []struct {
					Ty     string  `json:"ty"`
					InterS float64 `json:"inter"`
					IntraS float64 `json:"intra"`
				} `json:"isup_details"`
			} `json:"inward_sup"`
			IntrLtfee struct {
				Intr  amtHeads `json:"intr_details"`
				Ltfee amtHeads `json:"ltfee_details"`
			} `json:"intr_ltfee"`
			TtVal struct {
				TtPay   float64 `json:"tt_pay"`
				TtCshPd float64 `json:"tt_csh_pd"`
				TtItcPd float64 `json:"tt_itc_pd"`
			} `json:"tt_val"`
		} `json:"data"`
	}
	if err := json.Unmarshal(raw, &v); err != nil {
		return nil
	}
	d := v.Data
	env := e
	if d.RetPeriod != "" {
		env = e.withPeriod(d.RetPeriod)
	}
	var out []record

	// 3.1 — outward supplies and inward RCM
	for _, r := range gstr3bRows {
		h, ok := d.SupDetails[r.key]
		if !ok {
			continue
		}
		out = append(out, env.rec("GSTR3B", "3.1", "summary", merge(record{"row": r.row}, h.fields(true))))
	}

	// 3.2 — inter-state supplies to the unregistered, composition dealers, UIN
	for _, g := range []struct {
		row  string
		rows []posRow
	}{
		{"unregistered", d.InterSup.Unreg},
		{"composition", d.InterSup.Comp},
		{"uin_holders", d.InterSup.UIN},
	} {
		for _, p := range g.rows {
			out = append(out, env.rec("GSTR3B", "3.2", "summary", record{
				"row": g.row, "pos": p.Pos,
				"taxable_value": r2(p.Txval), "igst": r2(p.Iamt),
				"cgst": 0.0, "sgst": 0.0, "cess": 0.0,
			}))
		}
	}

	// 4 — ITC: available, reversed, net, ineligible
	for _, t := range d.ItcElg.ItcAvl {
		out = append(out, env.rec("GSTR3B", "4", "summary", merge(record{"row": rowName(itcAvlRows, t.Ty)}, t.amtHeads.fields(false))))
	}
	for _, t := range d.ItcElg.ItcRev {
		out = append(out, env.rec("GSTR3B", "4", "summary", merge(record{"row": rowName(itcRevRows, t.Ty)}, t.amtHeads.fields(false))))
	}
	if hasAny(d.ItcElg.ItcNet) {
		out = append(out, env.rec("GSTR3B", "4", "summary", merge(record{"row": "C_net_itc"}, d.ItcElg.ItcNet.fields(false))))
	}
	for _, t := range d.ItcElg.ItcInelg {
		out = append(out, env.rec("GSTR3B", "4", "summary", merge(record{"row": rowName(itcInelgRows, t.Ty)}, t.amtHeads.fields(false))))
	}

	// 5 — exempt / nil-rated / non-GST inward supplies (absent on nil returns)
	for _, s := range d.InwardSup.Details {
		out = append(out, env.rec("GSTR3B", "5", "summary", record{
			"row": strings.ToLower(s.Ty), "inter_state": r2(s.InterS), "intra_state": r2(s.IntraS),
		}))
	}

	// 5.1 — interest and late fee
	out = append(out, env.rec("GSTR3B", "5.1", "summary", merge(record{"row": "interest"}, d.IntrLtfee.Intr.fields(false))))
	out = append(out, env.rec("GSTR3B", "5.1", "summary", merge(record{"row": "late_fee"}, d.IntrLtfee.Ltfee.fields(false))))

	// 6.1 — what was actually paid
	out = append(out, env.rec("GSTR3B", "6.1", "summary", record{
		"row":         "payment",
		"tax_payable": r2(d.TtVal.TtPay),
		"paid_cash":   r2(d.TtVal.TtCshPd),
		"paid_itc":    r2(d.TtVal.TtItcPd),
	}))
	return out
}

type posRow struct {
	Pos   string  `json:"pos"`
	Txval float64 `json:"txval"`
	Iamt  float64 `json:"iamt"`
}

type tyRow struct {
	Ty string `json:"ty"`
	amtHeads
}

func rowName(m map[string]string, ty string) string {
	if v, ok := m[ty]; ok {
		return v
	}
	return strings.ToLower(ty)
}

func hasAny(a amtHeads) bool {
	return a.Iamt != 0 || a.Camt != 0 || a.Samt != 0 || a.Csamt != 0 || a.Txval != 0
}

// ---- GSTR-2B ---------------------------------------------------------------

func normGSTR2B(e envelope, raw json.RawMessage) []record {
	var v struct {
		Data struct {
			RtnPrd  string `json:"rtnprd"`
			ItcSumm struct {
				ItcAvl struct {
					NonRevSup struct {
						B2B  taxHeads `json:"b2b"`
						CDNR taxHeads `json:"cdnr"`
					} `json:"nonrevsup"`
					RevSup struct {
						B2B taxHeads `json:"b2b"`
					} `json:"revsup"`
					Imports struct {
						Impg taxHeads `json:"impg"`
					} `json:"imports"`
					IsdSup struct {
						Isd taxHeads `json:"isd"`
					} `json:"isdsup"`
					OtherSup struct {
						CDNR taxHeads `json:"cdnr"`
					} `json:"othersup"`
				} `json:"itcavl"`
			} `json:"itcsumm"`
			DocData struct {
				B2B []b2bSupplier `json:"b2b"`
			} `json:"docdata"`
		} `json:"data"`
	}
	if err := json.Unmarshal(raw, &v); err != nil {
		return nil
	}
	d := v.Data
	env := e
	if d.RtnPrd != "" {
		env = e.withPeriod(d.RtnPrd)
	}
	var out []record

	avl := d.ItcSumm.ItcAvl
	for _, s := range []struct {
		row string
		h   taxHeads
	}{
		{"b2b_non_reverse_charge", avl.NonRevSup.B2B},
		{"cdnr_non_reverse_charge", avl.NonRevSup.CDNR},
		{"b2b_reverse_charge", avl.RevSup.B2B},
		{"import_of_goods", avl.Imports.Impg},
		{"isd", avl.IsdSup.Isd},
		{"cdnr_other", avl.OtherSup.CDNR},
	} {
		out = append(out, env.rec("GSTR2B", "ITC_AVAILABLE", "summary", merge(record{"row": s.row}, s.h.fields())))
	}

	for _, sup := range d.DocData.B2B {
		for _, inv := range sup.Inv {
			out = append(out, env.rec("GSTR2B", "B2B", "document", merge(record{
				"supplier_gstin":         sup.Ctin,
				"supplier_name":          sup.Trdnm,
				"supplier_filing_period": nilIfEmpty(sup.Supprd),
				"supplier_filed_on":      isoOrNil(sup.Supfildt),
				"inv_num":                inv.Inum,
				"inv_num_norm":           normDocNum(inv.Inum),
				"inv_date":               isoOrNil(inv.Dt),
				"inv_value":              r2(inv.Val),
				"pos":                    nilIfEmpty(inv.Pos),
				"reverse_charge":         strings.EqualFold(inv.Rev, "Y"),
				"doc_type":               nilIfEmpty(inv.Typ),
				"itc_available":          strings.EqualFold(inv.Itcavl, "Y"),
				"itc_unavailable_reason": nilIfEmpty(inv.Rsn),
				"diff_pct":               nil,
				"amended":                false,
			}, inv.taxHeads.fields())))
		}
	}
	return out
}

type b2bSupplier struct {
	Ctin     string   `json:"ctin"`
	Trdnm    string   `json:"trdnm"`
	Supfildt string   `json:"supfildt"`
	Supprd   string   `json:"supprd"`
	Inv      []b2bDoc `json:"inv"`
}

type b2bDoc struct {
	Inum   string  `json:"inum"`
	Dt     string  `json:"dt"`
	Val    float64 `json:"val"`
	Pos    string  `json:"pos"`
	Rev    string  `json:"rev"`
	Itcavl string  `json:"itcavl"`
	Rsn    string  `json:"rsn"`
	Typ    string  `json:"typ"`
	taxHeads
}

// normDocNum is the spec's norm(): uppercase, strip whitespace, collapse the
// separators suppliers use interchangeably, drop leading zeros in numeric
// segments. Both spellings are emitted so a match can be traced back.
func normDocNum(s string) string {
	s = strings.ToUpper(strings.TrimSpace(s))
	s = strings.NewReplacer(" ", "", "\\", "/", "-", "/", "_", "/").Replace(s)
	parts := strings.Split(s, "/")
	for i, p := range parts {
		if p == "" {
			continue
		}
		if allDigits(p) {
			trimmed := strings.TrimLeft(p, "0")
			if trimmed == "" {
				trimmed = "0"
			}
			parts[i] = trimmed
		}
	}
	return strings.Join(parts, "/")
}

func allDigits(s string) bool {
	for _, r := range s {
		if r < '0' || r > '9' {
			return false
		}
	}
	return s != ""
}

// ---- small helpers ---------------------------------------------------------

// r2 rounds to two decimals. The portal returns floats that have already been
// through a JSON round trip; without this, 30158.899999999998 reaches the file.
func r2(v float64) float64 {
	if math.IsNaN(v) || math.IsInf(v, 0) {
		return 0
	}
	return math.Round(v*100) / 100
}

func merge(a, b record) record {
	for k, v := range b {
		a[k] = v
	}
	return a
}

func nz(s string) string { return strings.TrimSpace(s) }

func nilIfEmpty(s string) any {
	if strings.TrimSpace(s) == "" {
		return nil
	}
	return s
}

func nilIfDash(s string) any {
	if t := strings.TrimSpace(s); t == "" || t == "-" {
		return nil
	}
	return strings.TrimSpace(s)
}

func nilIfEmptyMap(m map[string]any) any {
	if len(m) == 0 {
		return nil
	}
	return m
}

func firstNonDash(ss ...string) string {
	for _, s := range ss {
		if t := strings.TrimSpace(s); t != "" && t != "-" {
			return t
		}
	}
	return ""
}

// isoOrNil converts a portal date to ISO, or nil if it is absent/placeholder.
func isoOrNil(s string) any {
	t, err := parsePortalDate(s)
	if err != nil {
		return nil
	}
	return isoDate(t)
}

// monthNames maps the portal's `taxp` (a month name) to its number.
var monthNames = map[string]int{
	"january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
	"july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}

// periodOf turns ("July", "2026-27") into "072026" — the register gives the
// month by name and the FY by label, and every other endpoint wants MMYYYY.
func periodOf(monthName, fy string) string {
	m, ok := monthNames[strings.ToLower(strings.TrimSpace(monthName))]
	if !ok {
		return ""
	}
	start, err := parseFY(fy)
	if err != nil {
		return ""
	}
	y := start.Year()
	if m < 4 {
		y++ // January–March fall in the second calendar year of the FY
	}
	return padMonth(m) + strconv.Itoa(y)
}

func padMonth(m int) string {
	if m < 10 {
		return "0" + strconv.Itoa(m)
	}
	return strconv.Itoa(m)
}

func itoa(n int) string { return strconv.Itoa(n) }

func sortStrings(ss []string) { sort.Strings(ss) }
