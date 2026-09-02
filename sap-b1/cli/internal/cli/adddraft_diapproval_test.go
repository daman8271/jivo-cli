package cli

import (
	"strings"
	"testing"
)

// GUARD 5b — the 2026-09-02 lesson. Mart draft 40128 was previewed as "will be
// submitted for approval" and SAP posted it live, because Mart's General
// Settings have "Enable Approval Procedures in DI" off and templates are never
// consulted for a Service Layer Add there. The command now reads that flag and
// refuses the SUBMIT click when it is off — dry-run and --yes alike, with
// nothing sent (C-0074).
func TestAddRefusesToSubmitWhereApprovalProceduresAreOffForDI(t *testing.T) {
	for _, flag := range []string{"tNO", "(absent)"} {
		t.Run(flag, func(t *testing.T) {
			f := newFakeAddSAP(t)
			if flag == "tNO" {
				f.diApproval = "tNO"
			} else {
				f.diApproval = "?" // any answer that is not tYES: the guard fails closed
			}
			f.putAddDraft(55126, nil) // dasWithout — click one

			for _, mode := range []string{"--dry-run", "--yes"} {
				_, _, err := execWrite(t, "", "add-draft", "55126", mode)
				if f.addCount() != 0 {
					t.Fatalf("%s: a dasWithout draft in a DI-approval-off company must never be Added, got %d Add(s)", mode, f.addCount())
				}
				if ExitCodeFor(err) != 9 {
					t.Fatalf("%s: expected exit 9, got %d (%v)", mode, ExitCodeFor(err), err)
				}
				for _, want := range []string{"EnableApprovalProcedureInDI", "post it LIVE", "C-0074", "press Add in the SAP B1 client"} {
					if !strings.Contains(err.Error(), want) {
						t.Errorf("%s: refusal must say %q, got:\n%s", mode, want, err)
					}
				}
			}
		})
	}
}

// Click two is untouched by the flag: an approved draft posts by design, and
// the guard must not turn Mart's approved backlog into a refusal.
func TestAddStillPostsAnApprovedDraftWhereDIApprovalIsOff(t *testing.T) {
	f := newFakeAddSAP(t)
	f.diApproval = "tNO"
	f.putAddDraft(55126, map[string]interface{}{"AuthorizationStatus": "dasApproved"})
	f.afterAdd = func(f *fakeAddSAP) { f.mutate("Drafts(55126)", "DocumentStatus", "bost_Close") }
	f.became = []map[string]interface{}{{"DocEntry": 47577, "DocNum": "626074104", "DocTotal": 253110}}

	stdout, _, err := execWrite(t, "", "add-draft", "55126", "--yes")
	if err != nil {
		t.Fatalf("add failed: %v", err)
	}
	if f.addCount() != 1 {
		t.Fatalf("expected exactly 1 Add, got %d", f.addCount())
	}
	if !strings.Contains(stdout, "ADDED in") {
		t.Errorf("an approved draft must still post, got:\n%s", stdout)
	}
}

// With the flag ON (Oil), a dasWithout draft is submitted exactly as before —
// the guard adds one read and changes nothing else.
func TestAddSubmitsWhereDIApprovalIsOnAndReadsTheFlagFirst(t *testing.T) {
	f := newFakeAddSAP(t)
	f.diApproval = "tYES"
	f.putAddDraft(55126, nil)
	f.afterAdd = func(f *fakeAddSAP) { f.mutate("Drafts(55126)", "AuthorizationStatus", "dasPending") }

	stdout, _, err := execWrite(t, "", "add-draft", "55126", "--yes")
	if err != nil {
		t.Fatalf("add failed: %v", err)
	}
	if f.addCount() != 1 {
		t.Fatalf("expected exactly 1 Add, got %d", f.addCount())
	}
	if !strings.Contains(stdout, "submitted for approval") {
		t.Errorf("expected the approval outcome, got:\n%s", stdout)
	}
	reqs := strings.Join(f.requests, "\n")
	if !strings.Contains(reqs, "POST /b1s/v1/CompanyService_GetAdminInfo") {
		t.Errorf("the flag must be READ from SAP before any Add; requests were:\n%s", reqs)
	}
	if strings.Index(reqs, "CompanyService_GetAdminInfo") > strings.Index(reqs, "DraftsService_SaveDraftToDocument") {
		t.Errorf("the flag must be read BEFORE the Add, requests were:\n%s", reqs)
	}
}

// If General Settings cannot be read, the Add cannot be judged: stop with
// nothing sent, and say why.
func TestAddStopsWhenGeneralSettingsCannotBeRead(t *testing.T) {
	f := newFakeAddSAP(t)
	f.adminStatus = 500
	f.putAddDraft(55126, nil)

	_, _, err := execWrite(t, "", "add-draft", "55126", "--yes")
	if err == nil {
		t.Fatal("expected an error when CompanyService_GetAdminInfo fails")
	}
	if f.addCount() != 0 {
		t.Fatalf("nothing may be Added when the settings read fails, got %d", f.addCount())
	}
	for _, want := range []string{"CompanyService_GetAdminInfo", "nothing was attempted"} {
		if !strings.Contains(err.Error(), want) {
			t.Errorf("error must say %q, got:\n%s", want, err)
		}
	}
}
