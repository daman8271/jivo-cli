package client

import (
	"context"
	"encoding/json"
	"fmt"
	"net/url"
	"strconv"
	"strings"
	"time"
	"unicode"

	"sapb1/internal/errs"
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
	// CountOnly asks the server how many rows MATCH and for no rows at all:
	// "$top=0&$inlinecount=allpages", carrying only $filter.
	//
	// A count is a question about the SET, not about any row, and $top=1 answered
	// it by hauling one complete ~200-field SAP document back just to read a
	// header — 14,460 bytes to learn a five-digit number. $top=0 is honoured by
	// this Service Layer on every entity set and every company database
	// (verified live on Orders/Invoices/Items/BusinessPartners/JournalEntries
	// across Oil, Mart and Beverages: HTTP 200, correct odata.count, zero rows,
	// ~110-121 bytes).
	//
	// It is a MODE, not a hint: $select, $orderby, $skip and $top are refused
	// alongside it rather than quietly dropped, because there are no rows for a
	// projection or an ordering to apply to, and $inlinecount is computed over
	// the whole filtered set regardless of any offset.
	CountOnly bool
}

func (o QueryOptions) queryString() string {
	q := url.Values{}
	if o.CountOnly {
		if o.Filter != "" {
			q.Set("$filter", o.Filter)
		}
		q.Set("$top", "0")
		q.Set("$inlinecount", "allpages")
		return q.Encode()
	}
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
	// ServerDate is the SAP server's own clock, taken from the HTTP Date
	// response header (of the FINAL page, for QueryAll). ServerDateKnown is
	// false when the server sent no usable Date header, in which case a caller
	// that wants an "as of" stamp must fall back to local time AND say so.
	ServerDate      time.Time `json:"-"`
	ServerDateKnown bool      `json:"-"`
}

// MaxPages caps QueryAll's pagination so a runaway filter can't loop forever.
const MaxPages = 200

// urlStructuralChars are the characters that, appearing in an entity-set name,
// would change the STRUCTURE of the request URL rather than name an entity.
//
// This matters because the request path is built as entitySet + "?" + query
// string. A '#' anywhere in the name turns everything after it — $filter,
// $select, $orderby, $top, $inlinecount — into a URI fragment, which net/http
// never puts on the wire. The request then SUCCEEDS and returns unfiltered,
// unprojected rows: a normal-looking answer to a question nobody asked, which
// is the exact failure class this package exists to prevent. '?' and '&' would
// splice caller text into the query string the same way; '%' would let a name
// smuggle any of them back in percent-encoded; whitespace and control
// characters cannot occur in a real entity-set name and only ever arrive from
// a mangled argument.
const urlStructuralChars = "#?&%"

// ValidateEntitySet rejects an entity-set name that could not be concatenated
// into a request URL without changing its meaning. It is deliberately a hard
// error rather than a silent sanitisation: rewriting "Orders#" into "Orders"
// would answer a different question than the caller asked, which is the same
// defect wearing a different hat.
func ValidateEntitySet(entitySet string) error {
	name := strings.TrimSpace(entitySet)
	if name == "" {
		return &errs.UsageError{Msg: `entity set is required, e.g. "Orders"`}
	}
	for _, r := range name {
		switch {
		case strings.ContainsRune(urlStructuralChars, r):
			return &errs.UsageError{Msg: fmt.Sprintf(
				"invalid entity set %q: %q is not part of an entity-set name, and inside one it would silently drop the query options "+
					"($filter/$select/$orderby/$top) from the request — pass just the entity set (e.g. \"Orders\") and use the filter/select/orderby options",
				entitySet, string(r))}
		case unicode.IsSpace(r):
			return &errs.UsageError{Msg: fmt.Sprintf(
				"invalid entity set %q: entity-set names contain no whitespace — pass just the entity set, e.g. \"Orders\"", entitySet)}
		case r < 0x20 || r == 0x7f:
			return &errs.UsageError{Msg: fmt.Sprintf(
				"invalid entity set %q: it contains a control character", entitySet)}
		}
	}
	return nil
}

// validateCountOnly refuses the option combinations a count-only request cannot
// honour. Dropping them in silence would be the same defect ValidateEntitySet
// exists to stop, one layer up: the caller asked for a projection or an
// ordering, got a number, and had no way to tell that half the request was
// discarded.
func validateCountOnly(o QueryOptions) error {
	if !o.CountOnly {
		return nil
	}
	for _, bad := range []struct {
		name, why string
		set       bool
	}{
		{"Select", "a count returns no rows to project", o.Select != ""},
		{"OrderBy", "a count returns no rows to order", o.OrderBy != ""},
		{"Skip", "$inlinecount totals the whole filtered set, so an offset cannot change it", o.Skip != 0},
		{"Top", "a count-only request fixes $top at 0", o.Top != 0},
		{"PageSize", "a count is a single request and never paginates", o.PageSize != 0},
	} {
		if bad.set {
			return &errs.UsageError{Msg: fmt.Sprintf(
				"QueryOptions.%s cannot be combined with CountOnly: %s", bad.name, bad.why)}
		}
	}
	return nil
}

// entityPath validates entitySet and builds the request path for opts.
func entityPath(entitySet string, opts QueryOptions) (string, error) {
	if err := ValidateEntitySet(entitySet); err != nil {
		return "", err
	}
	if err := validateCountOnly(opts); err != nil {
		return "", err
	}
	path := strings.TrimSpace(entitySet)
	if qs := opts.queryString(); qs != "" {
		path += "?" + qs
	}
	return path, nil
}

// Query fetches a single page of entitySet (e.g. "Orders", "Items",
// "BusinessPartners") using the given options.
func (c *Client) Query(ctx context.Context, entitySet string, opts QueryOptions) (*QueryResult, error) {
	path, err := entityPath(entitySet, opts)
	if err != nil {
		return nil, err
	}
	body, respHeaders, err := c.getWithHeaders(ctx, path, opts.headers())
	if err != nil {
		return nil, err
	}
	qr, err := parseQueryResult(body, entitySet)
	if err != nil {
		return nil, err
	}
	qr.ServerDate, qr.ServerDateKnown = serverDate(respHeaders)
	return qr, nil
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
//
// When opts.Top > 0 it also stops as soon as it holds Top rows, and trims to
// exactly Top. The Service Layer normally carries $top across its nextLinks,
// but that is a server behaviour we do not control: without the client-side
// stop, a server that dropped $top from the nextLink would silently turn
// "give me 45 rows" into a 200-page walk of the whole entity set. The stop
// makes the cost of a bounded request bounded regardless.
func (c *Client) QueryAll(ctx context.Context, entitySet string, opts QueryOptions) (*QueryResult, error) {
	path, err := entityPath(entitySet, opts)
	if err != nil {
		return nil, err
	}
	headers := opts.headers()

	var all []map[string]interface{}
	capped := false
	var count int64
	countKnown := false
	var lastDate time.Time
	lastDateKnown := false

	for page := 0; ; page++ {
		body, respHeaders, err := c.getWithHeaders(ctx, path, headers)
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
		// The freshest stamp wins: it is the moment the last row was read.
		if d, ok := serverDate(respHeaders); ok {
			lastDate, lastDateKnown = d, true
		}

		if opts.Top > 0 && len(all) >= opts.Top {
			all = all[:opts.Top]
			break
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

	return &QueryResult{
		Value:           all,
		Capped:          capped,
		Count:           count,
		CountKnown:      countKnown,
		ServerDate:      lastDate,
		ServerDateKnown: lastDateKnown,
	}, nil
}
