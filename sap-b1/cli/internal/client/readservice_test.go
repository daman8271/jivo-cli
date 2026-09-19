package client

import "testing"

// TestReadServiceAllowlistIsExactlyOneOperation pins the allowlist's contents.
//
// The point of this test is not that the list is short, it is that growing it is
// a deliberate act. CallReadService is the only place in this CLI that POSTs
// without a preview, a confirmation or a write-log entry, on the grounds that
// everything it can reach is a read. That reasoning holds only for as long as
// the list stays read-only, so a change here should fail this test and make
// whoever made it say why.
func TestReadServiceAllowlistIsExactlyOneOperation(t *testing.T) {
	want := map[string]bool{
		"MaterialRevaluationFIFOService_GetMaterialRevaluationFIFO": true,
	}

	if len(readServiceAllowlist) != len(want) {
		t.Fatalf("read-service allowlist has %d entries, want %d: %v",
			len(readServiceAllowlist), len(want), readServiceAllowlist)
	}
	for op := range want {
		if !readServiceAllowlist[op] {
			t.Errorf("expected %q to be allowlisted", op)
		}
	}
	for op := range readServiceAllowlist {
		if !want[op] {
			t.Errorf("unexpected entry %q in the read-service allowlist — "+
				"if this is a genuine read, add it to this test's want set and say why in the commit", op)
		}
	}
}

// TestReadServiceRefusesMutatingActions is the one that matters. These are all
// real Service Layer operations, they are all POSTs, and they all live in the
// same catalog as the FIFO reader. None of them may ever be reachable: posting,
// cancelling and closing documents is a human's job in the SAP B1 client.
func TestReadServiceRefusesMutatingActions(t *testing.T) {
	forbidden := []string{
		"MaterialRevaluation(263)/Cancel",
		"MaterialRevaluation(263)/Close",
		"Drafts(4321)/SaveDraftToDocument",
		"Orders(1)/Close",
		"Invoices(9)/Cancel",
		"SeriesService_AddSeries",
		"SeriesService_RemoveSeries",
		"SeriesService_UpdateSeries",
		"MaterialRevaluation",
		"BusinessPartners",
		"",
		"MaterialRevaluationFIFOService",
		"materialrevaluationfifoservice_getmaterialrevaluationfifo", // case must match exactly
		"MaterialRevaluationFIFOService_GetMaterialRevaluationFIFO ",
		" MaterialRevaluationFIFOService_GetMaterialRevaluationFIFO",
		"MaterialRevaluationFIFOService_GetMaterialRevaluationFIFO/../SeriesService_AddSeries",
	}

	for _, op := range forbidden {
		if ReadServiceAllowed(op) {
			t.Errorf("ReadServiceAllowed(%q) = true, want false — this operation must stay unreachable", op)
		}
	}
}
