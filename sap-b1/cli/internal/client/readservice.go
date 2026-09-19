package client

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"net/http"

	"sapb1/internal/errs"
)

// readServiceAllowlist is the complete set of Service Layer service operations
// this CLI may call. Every one of them is a READ that the Service Layer happens
// to expose over POST because it takes parameters — none of them mutates
// anything.
//
// It is an allowlist, not a pattern, and it is deliberately tiny. The rule it
// exists beside is the one in validateWriteEntitySet that refuses OData actions:
// MaterialRevaluation(id)/Cancel, MaterialRevaluation(id)/Close,
// Drafts(id)/SaveDraftToDocument, Orders(id)/Close. Those are POSTs too, they
// live in the same service catalog, and they must stay unreachable. So this list
// is checked by exact string match against a fixed map — adding an entry has to
// be a deliberate edit with a test, and nothing the operator types can extend it.
//
// Authorised 2026-09-19 to unblock FIFO revaluation: SAP does not store the
// revaluable-layer state in any readable table (OIVL.OpenQty is not the layer
// remainder — it disagrees with OITW.OnHand on ~30% of items that were never
// disassembled), so this call is the only way to learn which layers a
// MaterialRevaluation may target.
var readServiceAllowlist = map[string]bool{
	"MaterialRevaluationFIFOService_GetMaterialRevaluationFIFO": true,
}

// ReadServiceAllowed reports whether op is a service operation this CLI may
// call. Exported so the CLI layer and its tests can check without duplicating
// the list.
func ReadServiceAllowed(op string) bool {
	return readServiceAllowlist[op]
}

// CallReadService POSTs payload to an allowlisted, read-only service operation
// and returns the raw response body.
//
// It is NOT a write path and must never become one:
//   - the operation name is checked against the allowlist above, by exact match;
//   - nothing is previewed, confirmed or written to the write log, because
//     nothing is being changed;
//   - a 401 is retried exactly once after re-login, and a transport failure is
//     simply an error — there is no outcome-unknown case to worry about,
//     because a read that did not come back changed nothing.
func (c *Client) CallReadService(ctx context.Context, op string, payload []byte) ([]byte, error) {
	if !ReadServiceAllowed(op) {
		return nil, &errs.UsageError{Msg: fmt.Sprintf(
			"%q is not an allowlisted read-only service operation — this CLI calls no other service action, "+
				"and in particular never Cancel, Close or SaveDraftToDocument", op)}
	}

	if err := c.ensureSession(ctx); err != nil {
		return nil, err
	}

	used := c.b1Session
	body, status, err := c.rawReadService(ctx, op, payload)
	if err != nil {
		return nil, err
	}

	if status == http.StatusUnauthorized {
		if err := c.refreshSession(ctx, used); err != nil {
			return nil, err
		}
		body, status, err = c.rawReadService(ctx, op, payload)
		if err != nil {
			return nil, err
		}
	}

	if status < 200 || status >= 300 {
		code, msg := extractSAPErrorDetail(body)
		if msg == "" {
			msg = fmt.Sprintf("HTTP %d", status)
		}
		if status == http.StatusUnauthorized {
			return nil, &errs.AuthError{Msg: fmt.Sprintf("authentication failed: %s", msg)}
		}
		return nil, &errs.APIError{Code: code, Msg: msg}
	}

	return body, nil
}

// rawReadService performs the POST. It uses the read HTTP client (and so the
// read timeout), not writeClient, because this is a read.
func (c *Client) rawReadService(ctx context.Context, op string, payload []byte) ([]byte, int, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.cfg.BaseURL()+op, bytes.NewReader(payload))
	if err != nil {
		return nil, 0, fmt.Errorf("building request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")
	c.attachCookies(req)

	resp, err := c.http.Do(req)
	if err != nil {
		return nil, 0, classifyTransportErr(err, c.cfg)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, 0, fmt.Errorf("reading response body: %w", err)
	}
	return body, resp.StatusCode, nil
}
