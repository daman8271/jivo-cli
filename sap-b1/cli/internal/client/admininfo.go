package client

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"

	"sapb1/internal/errs"
)

// adminInfoPath is the Service Layer's read of Administration → System
// Initialization → General Settings. It is an OData *function import*, so the
// wire method is POST — but it changes nothing. It is the only POST in this
// package that is not a write, and it is kept out of write() on purpose: it
// must never appear in the write log as if something had been sent.
const adminInfoPath = "CompanyService_GetAdminInfo"

// AdminInfo is the part of General Settings that decides what an API Add DOES.
//
// EnableApprovalProcedureInDI is the BP-tab checkbox "Enable Approval Procedures
// in DI". SAP consults approval templates for a document arriving through the
// DI API or the Service Layer ONLY when it is on. With it off, every template —
// however well built — is skipped, and SaveDraftToDocument posts the draft
// straight into the books with no approver. Measured 2026-09-02: Oil tYES, Mart
// tNO, Beverages tNO; Mart draft 40128 became live A/P invoice 12210 that way
// while the preview promised an approval request (C-0074).
type AdminInfo struct {
	EnableApprovalProcedureInDI string
	Raw                         map[string]interface{}
}

// GetAdminInfo reads General Settings for the session's company. Read-only: it
// establishes a session, sends one POST with no body, re-logs-in once on a 401,
// and never touches the write log.
func (c *Client) GetAdminInfo(ctx context.Context) (*AdminInfo, error) {
	if err := c.ensureSession(ctx); err != nil {
		return nil, err
	}
	used := c.b1Session
	body, status, err := c.rawFunctionRead(ctx, adminInfoPath)
	if err != nil {
		return nil, err
	}
	if status == http.StatusUnauthorized {
		if err := c.refreshSession(ctx, used); err != nil {
			return nil, err
		}
		body, status, err = c.rawFunctionRead(ctx, adminInfoPath)
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
		return nil, &errs.APIError{Code: code, Msg: fmt.Sprintf("%s: %s", adminInfoPath, msg)}
	}
	var raw map[string]interface{}
	if err := json.Unmarshal(body, &raw); err != nil {
		return nil, fmt.Errorf("%s answered %d but the body is not JSON (%v) — check what is answering for SAP on %s:%d", adminInfoPath, status, err, c.cfg.Host, c.cfg.Port)
	}
	flag, _ := raw["EnableApprovalProcedureInDI"].(string)
	return &AdminInfo{EnableApprovalProcedureInDI: flag, Raw: raw}, nil
}

// rawFunctionRead fires one body-less POST at a read-only function import with
// the READ client (its timeout, no write log, no intent line). The path is a
// package constant, never caller-supplied.
func (c *Client) rawFunctionRead(ctx context.Context, path string) ([]byte, int, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.cfg.BaseURL()+path, nil)
	if err != nil {
		return nil, 0, fmt.Errorf("building request: %w", err)
	}
	req.Header.Set("Accept", "application/json")
	req.Header.Set("Content-Type", "application/json")
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
