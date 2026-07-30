package client

import (
	"bytes"
	"context"
	"crypto/tls"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/http/httptrace"
	"strings"
	"sync/atomic"
	"time"

	"sapb1/internal/errs"
)

// WriteResult is the outcome of a successful write. Status is the HTTP status
// the Service Layer returned (201 for a create, 204 for most PATCHes) and Body
// is the raw response body, which is the created object for a create and
// usually empty for a PATCH.
type WriteResult struct {
	Status int
	Body   []byte
}

// Create POSTs payload to entitySet (e.g. "Drafts", "BusinessPartners") and
// returns the created object. Only ever called from an operator-invoked write
// command (`sapb1 draft` / `sapb1 post`), which previews and confirms first.
//
// entitySet must be a bare entity-set name; the caller (internal/cli) validates
// that against the embedded catalog, so an OData action path such as
// "Invoices(9)/Cancel" can never reach this method.
func (c *Client) Create(ctx context.Context, entitySet string, payload []byte) (*WriteResult, error) {
	return c.write(ctx, http.MethodPost, entitySet, payload)
}

// Update PATCHes payload onto a single entity addressed by key, e.g.
// `Orders(123)` or `BusinessPartners('V10000')`. Only ever called from
// `sapb1 patch`, which previews and confirms first.
//
// entityPath must arrive already percent-encoded (see cli.buildKeyPath): what is
// passed here is what goes on the wire and what lands in the audit log, byte for
// byte.
func (c *Client) Update(ctx context.Context, entityPath string, payload []byte) (*WriteResult, error) {
	return c.write(ctx, http.MethodPatch, entityPath, payload)
}

// write performs an authenticated POST/PATCH against path (relative to the
// Service Layer base URL). It mirrors get(): log in first if there is no
// session, and on a 401 re-login exactly once and retry.
//
// The retry is deliberately limited to a 401 that SAP itself answered with.
// Anything that leaves the result in doubt — a timeout, a connection reset after
// the request went out, a bare gateway 502/504 — becomes
// *errs.WriteOutcomeUnknownError and is never replayed, because the write may
// already have committed.
//
// Every attempt is bracketed in the local write log: an "intent" line before the
// request goes out and an "outcome" line after it resolves, so even a killed
// process leaves a record of what was sent.
func (c *Client) write(ctx context.Context, method, path string, payload []byte) (*WriteResult, error) {
	if c.b1Session == "" {
		if !c.LoadCachedSession() {
			if err := c.Login(ctx); err != nil {
				// Nothing was sent, but record the abandoned attempt anyway.
				c.appendWriteLog(logOutcome, method, path, payload, 0, "", err)
				return nil, err
			}
		}
	}

	body, status, err := c.attemptWrite(ctx, method, path, payload)
	if err != nil {
		return nil, err
	}

	if status == http.StatusUnauthorized {
		// Close out this attempt in the log before trying again, so the pair
		// count always matches the number of requests actually sent.
		c.appendWriteLog(logOutcome, method, path, payload, status, "", errSessionExpiredRetry)
		if err := c.Login(ctx); err != nil {
			c.appendWriteLog(logOutcome, method, path, payload, status, "", err)
			return nil, err
		}
		body, status, err = c.attemptWrite(ctx, method, path, payload)
		if err != nil {
			return nil, err
		}
	}

	if status < 200 || status >= 300 {
		code, msg := extractSAPErrorDetail(body)
		var werr error
		switch {
		case status == http.StatusUnauthorized:
			if msg == "" {
				msg = fmt.Sprintf("HTTP %d", status)
			}
			werr = &errs.AuthError{Msg: fmt.Sprintf("authentication failed: %s", msg)}
		case msg == "" && isGatewayStatus(status):
			// A gateway/proxy answered, not SAP. The request may well have reached
			// SAP and committed — we just never got SAP's answer.
			werr = c.outcomeUnknownError(method, path, fmt.Sprintf("HTTP %d from a gateway/proxy, with no SAP error body", status), nil)
		default:
			if msg == "" {
				msg = fmt.Sprintf("HTTP %d", status)
			}
			werr = &errs.APIError{Code: code, Msg: msg}
		}
		c.appendWriteLog(logOutcome, method, path, payload, status, "", werr)
		return nil, werr
	}

	c.appendWriteLog(logOutcome, method, path, payload, status, resultKeyFromBody(body), nil)
	return &WriteResult{Status: status, Body: body}, nil
}

// errSessionExpiredRetry is what the log records for the 401 that triggers the
// one allowed re-login — it is not an error the caller ever sees.
var errSessionExpiredRetry = errors.New("HTTP 401 (session expired) — re-logging in and retrying this write once")

// attemptWrite logs the intent, fires exactly one request, and classifies a
// transport failure as either "never left the building" (*errs.NetworkError,
// safe to re-run) or "may have been committed"
// (*errs.WriteOutcomeUnknownError, do not re-run). Either way the outcome is
// logged before returning.
func (c *Client) attemptWrite(ctx context.Context, method, path string, payload []byte) ([]byte, int, error) {
	c.appendWriteLog(logIntent, method, path, payload, 0, "", nil)

	body, status, sent, err := c.rawWrite(ctx, method, path, payload)
	if err != nil {
		if sent {
			err = c.outcomeUnknownError(method, path, "the response never arrived", err)
		}
		c.appendWriteLog(logOutcome, method, path, payload, 0, "", err)
		return nil, 0, err
	}
	return body, status, nil
}

// outcomeUnknownError builds the one error in this tool whose whole job is to
// change what the reader does next: don't re-run it, go look in SAP.
func (c *Client) outcomeUnknownError(method, path, why string, cause error) error {
	msg := fmt.Sprintf(
		"%s %s on %s: the write request was sent but its outcome is unknown — it MAY have been committed in SAP (%s). "+
			"Check SAP (query the entity / Document Drafts) before re-running this command: a blind retry can create a duplicate",
		method, path, c.cfg.CompanyDB, why,
	)
	if cause != nil {
		msg += fmt.Sprintf(" [%v]", cause)
	}
	return &errs.WriteOutcomeUnknownError{Msg: msg, Err: cause}
}

// rawWrite sends one write request. The returned `sent` flag reports whether the
// request bytes made it onto the network before the failure — that is the line
// between "safe to re-run" and "outcome unknown", so it comes from
// httptrace.WroteRequest rather than from pattern-matching an error string.
//
// NOTE: never add an Idempotency-Key (or similar) header here. Go's net/http
// treats a request carrying one as replayable and will silently retry it after a
// connection error — exactly the double-post everything else in this file works
// to prevent. The absence of that header is load-bearing.
func (c *Client) rawWrite(ctx context.Context, method, path string, payload []byte) ([]byte, int, bool, error) {
	var wrote atomic.Bool
	trace := &httptrace.ClientTrace{
		WroteRequest: func(info httptrace.WroteRequestInfo) {
			if info.Err == nil {
				wrote.Store(true)
			}
		},
	}

	req, err := http.NewRequestWithContext(httptrace.WithClientTrace(ctx, trace), method, c.cfg.BaseURL()+path, bytes.NewReader(payload))
	if err != nil {
		return nil, 0, false, fmt.Errorf("building request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")
	c.attachCookies(req)

	resp, err := c.writeClient().Do(req)
	if err != nil {
		// A timeout counts as "sent" even if WroteRequest never fired: the
		// deadline may have struck while the response was in flight.
		if wrote.Load() || isTimeout(err) || errors.Is(err, context.DeadlineExceeded) {
			return nil, 0, true, err
		}
		return nil, 0, false, classifyTransportErr(err, c.cfg)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		// Headers arrived but the body was cut off: SAP has already acted, we
		// just can't read what it said.
		return nil, 0, true, err
	}
	return body, resp.StatusCode, true, nil
}

// writeClient returns the HTTP client used for writes. It exists separately from
// the read client purely for its longer timeout (see config.WriteTimeout).
func (c *Client) writeClient() *http.Client {
	if c.writeHTTP != nil {
		return c.writeHTTP
	}
	transport := &http.Transport{}
	if c.cfg.Insecure {
		transport.TLSClientConfig = &tls.Config{InsecureSkipVerify: true} // #nosec G402 — user opt-in for self-signed SAP certs
	}
	c.writeHTTP = &http.Client{
		Timeout:   time.Duration(c.cfg.WriteTimeout()) * time.Second,
		Transport: transport,
	}
	return c.writeHTTP
}

// isGatewayStatus reports whether status is the kind a proxy or load balancer in
// front of SAP returns when IT, not SAP, gave up.
func isGatewayStatus(status int) bool {
	switch status {
	case http.StatusBadGateway, http.StatusServiceUnavailable, http.StatusGatewayTimeout:
		return true
	}
	return false
}

// isTimeout reports whether err is a timeout, including the
// "Client.Timeout exceeded while awaiting headers" wrapper net/http produces.
func isTimeout(err error) bool {
	var te interface{ Timeout() bool }
	if errors.As(err, &te) && te.Timeout() {
		return true
	}
	return strings.Contains(err.Error(), "Client.Timeout")
}
