package client

import "testing"

// TestExtractODataCount covers both encodings the Service Layer uses for
// odata.count (a quoted string per OData v3, or a bare number) plus the
// absent/garbage cases.
func TestExtractODataCount(t *testing.T) {
	cases := []struct {
		name   string
		body   string
		wantN  int64
		wantOK bool
	}{
		{"quoted string", `{"odata.count":"42","value":[]}`, 42, true},
		{"bare number", `{"odata.count":7,"value":[]}`, 7, true},
		{"absent", `{"value":[{"DocEntry":1}]}`, 0, false},
		{"garbage", `not json`, 0, false},
		{"non-numeric", `{"odata.count":"lots"}`, 0, false},
	}
	for _, tc := range cases {
		n, ok := extractODataCount([]byte(tc.body))
		if ok != tc.wantOK || n != tc.wantN {
			t.Errorf("%s: extractODataCount = (%d,%v), want (%d,%v)", tc.name, n, ok, tc.wantN, tc.wantOK)
		}
	}
}

// TestParseQueryResultCount verifies a mock inlinecount response threads the
// server-side total through onto the QueryResult.
func TestParseQueryResultCount(t *testing.T) {
	body := []byte(`{"odata.count":"1234","value":[{"DocEntry":1},{"DocEntry":2}]}`)
	qr, err := parseQueryResult(body, "Orders")
	if err != nil {
		t.Fatalf("parseQueryResult: %v", err)
	}
	if !qr.CountKnown {
		t.Fatal("expected CountKnown=true when odata.count is present")
	}
	if qr.Count != 1234 {
		t.Errorf("Count = %d, want 1234", qr.Count)
	}
	if len(qr.Value) != 2 {
		t.Errorf("rows = %d, want 2", len(qr.Value))
	}
}

func TestParseQueryResultNoCount(t *testing.T) {
	body := []byte(`{"value":[{"DocEntry":1}]}`)
	qr, err := parseQueryResult(body, "Orders")
	if err != nil {
		t.Fatalf("parseQueryResult: %v", err)
	}
	if qr.CountKnown {
		t.Error("expected CountKnown=false when odata.count absent")
	}
}

// TestInlineCountQueryString confirms --count maps onto $inlinecount=allpages.
func TestInlineCountQueryString(t *testing.T) {
	qs := QueryOptions{InlineCount: true}.queryString()
	if qs != "%24inlinecount=allpages" && qs != "$inlinecount=allpages" {
		t.Errorf("queryString = %q, want it to set $inlinecount=allpages", qs)
	}
}
