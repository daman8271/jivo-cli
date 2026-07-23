package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"
)

// errUnauthorized is returned (wrapped) whenever the API answers 401, so any
// command can print uniform re-login guidance. The access_token is short-lived.
var errUnauthorized = errors.New("unauthorized")

// Client talks to the PartnersBiz v1/v2 API using the header-token auth scheme.
type Client struct {
	cfg Config
	hc  *http.Client
}

func newClient(cfg Config) *Client {
	return &Client{cfg: cfg, hc: &http.Client{Timeout: 90 * time.Second}}
}

// Report is one row of POST /v1/report-requests/.
type Report struct {
	ID        int    `json:"id"`
	Type      string `json:"type"`
	State     string `json:"state"`
	CreatedAt string `json:"created_at"`
	UpdatedAt string `json:"updated_at"`
	Comments  struct {
		Filters  map[string]any `json:"filters"`
		FilePath string         `json:"file_path"`
	} `json:"comments"`
}

// apiEnvelope is the common {status, data} wrapper (proven only for
// report-requests + get-sales-details).
type apiEnvelope struct {
	Status int             `json:"status"`
	Data   json.RawMessage `json:"data"`
}

// forbiddenPath is the read-only guardrail. It hard-errors BEFORE any request
// is sent if the method+path is an out-of-scope write or side-effecting export.
// Defense-in-depth so a future edit cannot accidentally wire a mutation.
func forbiddenPath(method, url string) error {
	m := strings.ToUpper(method)
	// HTTP method allowlist: only GET and POST are ever legitimate here.
	if m != http.MethodGet && m != http.MethodPost {
		return fmt.Errorf("read-only guardrail: HTTP %s is never allowed", m)
	}
	// Any report-generate export except the two sanctioned Sales/SOH exports.
	// Note "/reports/" (generate) is distinct from "/report-requests/" (queue read).
	if strings.Contains(url, "/reports/") &&
		!strings.Contains(url, "/reports/sales-details-excel/") &&
		!strings.Contains(url, "/reports/soh-details-excel/") {
		return fmt.Errorf("read-only guardrail: report-export endpoint %q is out of scope", url)
	}
	// Explicit write / activation paths that must never be constructed.
	blocked := []string{
		"/po-amendment/process/",
		"/asn-details/upsert/",
		"/appointments/create/",
		"/appointments/cancel/",
		"/client-requests/",
		"/courier-partner/validate/",
		"/invoice/upload-s3-resource/",
		"/bulk-upload-request/",
		"/vis/generate-url/",
	}
	for _, b := range blocked {
		if strings.Contains(url, b) {
			return fmt.Errorf("read-only guardrail: write endpoint %q is out of scope", url)
		}
	}
	// Offer/bundle sheet CREATE is a POST-multipart upload; the read of the same
	// resources is always a GET, so only POST is blocked here.
	if m == http.MethodPost {
		for _, b := range []string{"/brands-sheets/", "/bundles_and_combos_bf/"} {
			if strings.Contains(url, b) {
				return fmt.Errorf("read-only guardrail: upload endpoint %q is out of scope", url)
			}
		}
	}
	return nil
}

// setHeaders applies the exact working PartnersBiz auth header set.
func (c *Client) setHeaders(req *http.Request, hasBody bool) {
	req.Header.Set("accept", "application/json, text/plain, */*")
	req.Header.Set("x-api-key", c.cfg.APIKey)
	req.Header.Set("token", c.cfg.Token)
	req.Header.Set("access_token", c.cfg.Token)
	req.Header.Set("x-entity-id", c.cfg.EntityID)
	req.Header.Set("x-entity-type", c.cfg.EntityType)
	req.Header.Set("service", "partnersbiz")
	req.Header.Set("app_client", "partnerbiz-web")
	req.Header.Set("origin", "https://www.partnersbiz.com")
	req.Header.Set("referer", "https://www.partnersbiz.com/")
	req.Header.Set("user-agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36")
	if hasBody {
		req.Header.Set("content-type", "application/json")
	}
}

// do performs an authenticated request and unwraps the {status:1,data} envelope.
// Use ONLY for endpoints whose envelope is proven: report-requests and
// get-sales-details. Everything else must use doRaw.
func (c *Client) do(method, url string, body []byte) (json.RawMessage, error) {
	raw, err := c.doRaw(method, url, body)
	if err != nil {
		return nil, err
	}
	var env apiEnvelope
	if err := json.Unmarshal(raw, &env); err != nil {
		return nil, fmt.Errorf("decode envelope: %w (body: %.200s)", err, raw)
	}
	if env.Status != 1 {
		return nil, fmt.Errorf("%s %s → API status %d (body: %.200s)", method, url, env.Status, raw)
	}
	return env.Data, nil
}

// doRaw performs an authenticated request, checks the HTTP status, and returns
// the raw body with NO envelope assumption. This keeps the CLI honest for the
// many endpoints whose response schema is bundle-confirmed but not verified.
func (c *Client) doRaw(method, url string, body []byte) (json.RawMessage, error) {
	if err := forbiddenPath(method, url); err != nil {
		return nil, err
	}
	var rdr io.Reader
	if body != nil {
		rdr = bytes.NewReader(body)
	}
	req, err := http.NewRequest(method, url, rdr)
	if err != nil {
		return nil, err
	}
	c.setHeaders(req, body != nil)

	resp, err := c.hc.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	raw, _ := io.ReadAll(resp.Body)

	if resp.StatusCode == http.StatusUnauthorized {
		return nil, fmt.Errorf("%s %s → HTTP 401: %w", method, url, errUnauthorized)
	}
	if resp.StatusCode != http.StatusOK {
		snippet := string(raw)
		if len(snippet) > 300 {
			snippet = snippet[:300]
		}
		return nil, fmt.Errorf("%s %s → HTTP %d: %s", method, url, resp.StatusCode, snippet)
	}
	return raw, nil
}

// download fetches an authenticated binary (PDF/ZIP) via GET or POST-to-read
// and writes it to outPath. Returns bytes written.
func (c *Client) download(method, url string, body []byte, outPath string) (int64, error) {
	if err := forbiddenPath(method, url); err != nil {
		return 0, err
	}
	var rdr io.Reader
	if body != nil {
		rdr = bytes.NewReader(body)
	}
	req, err := http.NewRequest(method, url, rdr)
	if err != nil {
		return 0, err
	}
	c.setHeaders(req, body != nil)
	resp, err := c.hc.Do(req)
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()
	if resp.StatusCode == http.StatusUnauthorized {
		return 0, fmt.Errorf("%s %s → HTTP 401: %w", method, url, errUnauthorized)
	}
	if resp.StatusCode != http.StatusOK {
		return 0, fmt.Errorf("%s %s → HTTP %d", method, url, resp.StatusCode)
	}
	f, err := os.Create(outPath)
	if err != nil {
		return 0, err
	}
	defer f.Close()
	return io.Copy(f, resp.Body)
}

// ---- report queue reads (proven, envelope-asserting) --------------------

// ListReports returns the report-request rows (newest first), the shared queue
// for Sales, SOH, Invoices, Scorecard, etc.
func (c *Client) ListReports() ([]Report, error) {
	data, err := c.do(http.MethodPost, c.cfg.Base+"/v1/report-requests/", []byte(`{}`))
	if err != nil {
		return nil, err
	}
	var d struct {
		Reports []Report `json:"reports"`
	}
	if err := json.Unmarshal(data, &d); err != nil {
		return nil, fmt.Errorf("decode reports: %w", err)
	}
	return d.Reports, nil
}

// WaitForReport polls until report id reaches a success state, or errors on a
// terminal failure / timeout.
func (c *Client) WaitForReport(id int, timeout, interval time.Duration) (Report, error) {
	deadline := time.Now().Add(timeout)
	for {
		reports, err := c.ListReports()
		if err != nil {
			return Report{}, err
		}
		for _, r := range reports {
			if r.ID != id {
				continue
			}
			switch strings.ToLower(r.State) {
			case "success", "completed", "done":
				return r, nil
			case "failed", "error", "failure":
				return r, fmt.Errorf("report %d entered terminal state %q", id, r.State)
			}
		}
		if time.Now().After(deadline) {
			return Report{}, fmt.Errorf("timed out after %s waiting for report %d to succeed", timeout, id)
		}
		time.Sleep(interval)
	}
}

// DownloadURL mints a fresh presigned S3 URL for a completed report.
// The double slash in /download//{id}/ is intentional and load-bearing.
func (c *Client) DownloadURL(id int) (string, error) {
	url := fmt.Sprintf("%s/v1/report-requests/download//%d/", c.cfg.Base, id)
	data, err := c.do(http.MethodGet, url, nil)
	if err != nil {
		return "", err
	}
	var d struct {
		DownloadURL string `json:"download_url"`
	}
	if err := json.Unmarshal(data, &d); err != nil {
		return "", fmt.Errorf("decode download_url: %w", err)
	}
	if d.DownloadURL == "" {
		return "", fmt.Errorf("no download_url for report %d (data: %s)", id, data)
	}
	return d.DownloadURL, nil
}

// DownloadTo fetches a presigned S3 URL (no auth headers) and writes it to
// outPath. Returns the number of bytes written.
func (c *Client) DownloadTo(url, outPath string) (int64, error) {
	resp, err := c.hc.Get(url)
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return 0, fmt.Errorf("download → HTTP %d", resp.StatusCode)
	}
	f, err := os.Create(outPath)
	if err != nil {
		return 0, err
	}
	defer f.Close()
	return io.Copy(f, resp.Body)
}

// ---- sanctioned exports (opt-in side-effect: emails the account owner) ---

// generateReport POSTs a report-generate call and returns its request_id.
// Only ever reachable via GenerateSales / GenerateSOH behind an --export flag.
func (c *Client) generateReport(path string, body []byte) (int, error) {
	data, err := c.do(http.MethodPost, c.cfg.Base+path, body)
	if err != nil {
		return 0, err
	}
	var d struct {
		RequestID int `json:"request_id"`
	}
	if err := json.Unmarshal(data, &d); err != nil {
		return 0, fmt.Errorf("decode request_id: %w", err)
	}
	if d.RequestID == 0 {
		return 0, fmt.Errorf("generate returned no request_id (data: %s)", data)
	}
	return d.RequestID, nil
}

// GenerateSales fires the Sales Details export over a date window.
func (c *Client) GenerateSales(from, to string) (int, error) {
	body := []byte(fmt.Sprintf(`{"filters":{"created_at__gte":%q,"created_at__lte":%q}}`, from, to))
	return c.generateReport("/v1/reports/sales-details-excel/", body)
}

// GenerateSOH fires the Stock-on-Hand snapshot export (no date window).
func (c *Client) GenerateSOH() (int, error) {
	return c.generateReport("/v1/reports/soh-details-excel/", []byte(`{}`))
}
