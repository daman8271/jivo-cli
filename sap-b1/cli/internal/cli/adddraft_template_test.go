package cli

import (
	"strings"
	"testing"

	"sapb1/internal/config"
)

// Guard 5c: the login must be an originator on an Always-terms template for the
// doctype, or the Add is refused — because SAP's answer to "no template" is to
// post the document live.

func templatePreflight(action addAction) *addPreflight {
	dt := addDocTypes["oPurchaseInvoices"]
	return &addPreflight{
		DocEntry: 55126,
		Action:   action,
		Type:     dt,
	}
}

func TestTemplateGuardPassesForAVerifiedOriginator(t *testing.T) {
	// USER39 on Oil is template 103, read out of OWTM/WTM3/WTM1 on 2026-09-03.
	pf := templatePreflight(actionSubmit)
	checkAddApprovalTemplate(pf, &config.Config{CompanyDB: "JIVO_OIL_HANADB", User: "USER39"})
	if len(pf.Problems) != 0 {
		t.Fatalf("USER39 submitting an A/P invoice in Oil is template 103's originator; guard refused anyway: %v", pf.Problems)
	}
}

func TestTemplateGuardRefusesDivjotsLoginInOil(t *testing.T) {
	// The case this guard exists for. USER08 is on no Always-terms template, so
	// SAP would find none and post the invoice into the books unapproved.
	pf := templatePreflight(actionSubmit)
	checkAddApprovalTemplate(pf, &config.Config{CompanyDB: "JIVO_OIL_HANADB", User: "USER08"})
	if len(pf.Problems) != 1 {
		t.Fatalf("USER08 is on no template for an A/P invoice in Oil — expected exactly one refusal, got %d: %v", len(pf.Problems), pf.Problems)
	}
	p := pf.Problems[0]
	if p.Guard != "template" {
		t.Errorf("guard name = %q, want \"template\"", p.Guard)
	}
	for _, want := range []string{"USER08", "103", "USER39", "posts it LIVE"} {
		if !strings.Contains(p.Msg, want) {
			t.Errorf("refusal does not mention %q, so the operator cannot act on it:\n%s", want, p.Msg)
		}
	}
	if strings.Contains(strings.ToLower(p.Msg), "--force") {
		t.Error("the refusal must not advertise an override; there is none")
	}
}

func TestTemplateGuardRefusesAnUnknownCompany(t *testing.T) {
	// Fail closed: a company this repo has never read a template out of is not
	// evidence of safety.
	pf := templatePreflight(actionSubmit)
	checkAddApprovalTemplate(pf, &config.Config{CompanyDB: "SOME_OTHER_DB", User: "USER39"})
	if len(pf.Problems) != 1 {
		t.Fatalf("an unverified company must refuse, got %d problems", len(pf.Problems))
	}
}

func TestTemplateGuardIsSilentOnTheApprovedClick(t *testing.T) {
	// dasApproved is click two: a human has already approved it, and no
	// template has anything left to say.
	pf := templatePreflight(actionPost)
	checkAddApprovalTemplate(pf, &config.Config{CompanyDB: "JIVO_OIL_HANADB", User: "USER08"})
	if len(pf.Problems) != 0 {
		t.Fatalf("posting an already-approved draft must not be touched by the template guard: %v", pf.Problems)
	}
}

func TestTemplateGuardAcceptsTheBoxAssertion(t *testing.T) {
	// The day an admin adds USER08 to template 103, the box says so in its .env
	// and nothing has to be rebuilt.
	t.Setenv(approvalOriginatorEnv, "103")
	pf := templatePreflight(actionSubmit)
	checkAddApprovalTemplate(pf, &config.Config{CompanyDB: "JIVO_OIL_HANADB", User: "USER08"})
	if len(pf.Problems) != 0 {
		t.Fatalf("%s=103 asserts the grant; guard refused anyway: %v", approvalOriginatorEnv, pf.Problems)
	}
}

func TestEveryVerifiedTemplateRowNamesItsEvidence(t *testing.T) {
	for _, row := range verifiedApprovalTemplates() {
		if row.CompanyDB == "" || row.ObjectCode == "" || row.WtmCode == "" || len(row.Originators) == 0 {
			t.Errorf("incomplete template row %+v — a row without a company, doctype, code and originators cannot be re-verified", row)
		}
	}
}
