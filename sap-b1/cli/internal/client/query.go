package client

import (
	"context"
	"encoding/json"
	"fmt"
	"net/url"
	"strconv"
	"strings"
)

// QueryOptions maps directly onto the standard OData query options the
// Service Layer supports.
type QueryOptions struct {
	Select      string
	Filter      string
	Top         int
	Skip        int
	OrderBy     string
	PageSize    int  // sent as the "Prefer: odata.maxpagesize=N" header
	InlineCount bool // request "$inlinecount=allpages" so the server returns odata.count
}

func (o QueryOptions) queryString() string {
	q := url.Values{}
	if o.Select != "" {
		q.Set("$select", o.Select)
	}
	if o.Filter != "" {
		q.Set("$filter", o.Filter)
	}
	if o.Top > 0 {
		q.Set("$top", strconv.Itoa(o.Top))
	}
	if o.Skip > 0 {
		q.Set("$skip", strconv.Itoa(o.Skip))
	}
	if o.OrderBy != "" {
		q.Set("$orderby", o.OrderBy)
	}
	if o.InlineCount {
		q.Set("$inlinecount", "allpages")
	}
	return q.Encode()
}

func (o QueryOptions) headers() map[string]string {
	h := map[string]string{}
	if o.PageSize > 0 {
		h["Prefer"] = fmt.Sprintf("odata.maxpagesize=%d", o.PageSize)
	}
	return h
}

// QueryResult is one page of an OData response.
type QueryResult struct {
	Value    []map[string]interface{} `json:"value"`
	NextLink string                   `json:"odata.nextLink,omitempty"`
	// Capped is set by QueryAll (never by Query) to indicate pagination
	// stopped because MaxPages was reached, not because data ran out.
	Capped bool `json:"-"`
	// Count and CountKnown carry the server-side total from odata.count when
	// the request asked for it (InlineCount) and the server honored it.
	// CountKnown is false when the server ignored $inlinecount.
	Count      int64 `json:"-"`
	CountKnown bool  `json:"-"`
}

// MaxPages caps QueryAll's pagination so a runaway filter can't loop forever.
const MaxPages = 200

// Query fetches a single page of entitySet (e.g. "Orders", "Items",
// "BusinessPartners") using the given options.
func (c *Client) Query(ctx context.Context, entitySet string, opts QueryOptions) (*QueryResult, error) {
	path := entitySet
	if qs := opts.queryString(); qs != "" {
		path += "?" + qs
	}
	body, err := c.get(ctx, path, opts.headers())
	if err != nil {
		return nil, err
	}
	return parseQueryResult(body, entitySet)
}

// parseQueryResult unmarshals one OData page body into a QueryResult and, if
// present, extracts the odata.count total (which the Service Layer returns as
// either a JSON number or a quoted string).
func parseQueryResult(body []byte, entitySet string) (*QueryResult, error) {
	var qr QueryResult
	if err := json.Unmarshal(body, &qr); err != nil {
		return nil, fmt.Errorf("parsing response from %s: %w", entitySet, err)
	}
	if n, ok := extractODataCount(body); ok {
		qr.Count = n
		qr.CountKnown = true
	}
	return &qr, nil
}

// extractODataCount pulls the "odata.count" value out of an OData response
// body. The Service Layer may encode it as a bare number or a quoted string,
// so both are handled. Returns ok=false when the key is absent or unparseable.
func extractODataCount(body []byte) (int64, bool) {
	var m map[string]json.RawMessage
	if err := json.Unmarshal(body, &m); err != nil {
		return 0, false
	}
	raw, ok := m["odata.count"]
	if !ok {
		return 0, false
	}
	s := strings.TrimSpace(strings.Trim(string(raw), `"`))
	n, err := strconv.ParseInt(s, 10, 64)
	if err != nil {
		return 0, false
	}
	return n, true
}

// QueryAll follows odata.nextLink until the result set is exhausted or
// MaxPages is hit, whichever comes first, and returns the combined rows.
func (c *Client) QueryAll(ctx context.Context, entitySet string, opts QueryOptions) (*QueryResult, error) {
	path := entitySet
	if qs := opts.queryString(); qs != "" {
		path += "?" + qs
	}
	headers := opts.headers()

	var all []map[string]interface{}
	capped := false
	var count int64
	countKnown := false

	for page := 0; ; page++ {
		body, err := c.get(ctx, path, headers)
		if err != nil {
			return nil, err
		}
		qr, err := parseQueryResult(body, entitySet)
		if err != nil {
			return nil, err
		}
		all = append(all, qr.Value...)
		// The server-side total comes on the first page; keep it.
		if page == 0 && qr.CountKnown {
			count = qr.Count
			countKnown = true
		}

		if qr.NextLink == "" {
			break
		}
		if page+1 >= MaxPages {
			capped = true
			break
		}
		path = qr.NextLink
	}

	return &QueryResult{Value: all, Capped: capped, Count: count, CountKnown: countKnown}, nil
}
