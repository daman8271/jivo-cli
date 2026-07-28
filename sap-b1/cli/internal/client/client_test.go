package client

import (
	"context"
	"errors"
	"strings"
	"testing"
	"time"

	"sapb1/internal/config"
	"sapb1/internal/errs"
)

// TestLoginUnreachableIsFriendlyNetworkError verifies that a connection
// failure produces a typed, friendly *errs.NetworkError — never a raw panic
// or bare Go transport error. This intentionally dials 127.0.0.1 on a port
// nothing is listening on; it never touches the real SAP host.
func TestLoginUnreachableIsFriendlyNetworkError(t *testing.T) {
	cfg := &config.Config{
		Host:      "127.0.0.1",
		Port:      1, // reserved port, nothing listens here -> connection refused fast
		CompanyDB: "TESTDB",
		User:      "tester",
		Password:  "irrelevant",
		Timeout:   2,
	}
	c := New(cfg)

	err := c.Login(context.Background())
	if err == nil {
		t.Fatal("expected an error connecting to a closed port, got nil")
	}

	var netErr *errs.NetworkError
	if !errors.As(err, &netErr) {
		t.Fatalf("expected *errs.NetworkError, got %T: %v", err, err)
	}
	if !strings.Contains(netErr.Msg, "127.0.0.1:1") {
		t.Errorf("network error message should mention host:port, got: %s", netErr.Msg)
	}
	if !strings.Contains(netErr.Msg, "VPN") {
		t.Errorf("network error message should carry the VPN/whitelist hint, got: %s", netErr.Msg)
	}
}

// TestLoginMissingConfigIsConfigError verifies Login refuses to even attempt
// a request when required config is missing.
func TestLoginMissingConfigIsConfigError(t *testing.T) {
	cfg := &config.Config{}
	c := New(cfg)

	err := c.Login(context.Background())
	if err == nil {
		t.Fatal("expected config error, got nil")
	}
	var cfgErr *errs.ConfigError
	if !errors.As(err, &cfgErr) {
		t.Fatalf("expected *errs.ConfigError, got %T: %v", err, err)
	}
}

// TestCheckTCPReachableUnreachable exercises the doctor-command helper
// against a closed local port, never against the real SAP host.
func TestCheckTCPReachableUnreachable(t *testing.T) {
	err := CheckTCPReachable("127.0.0.1:1", 2*time.Second)
	if err == nil {
		t.Fatal("expected error dialing a closed port")
	}
	var netErr *errs.NetworkError
	if !errors.As(err, &netErr) {
		t.Fatalf("expected *errs.NetworkError, got %T: %v", err, err)
	}
}

func TestExtractSAPError(t *testing.T) {
	body := []byte(`{"error":{"code":301,"message":{"lang":"en-us","value":"Invalid session"}}}`)
	if got, want := extractSAPError(body), "Invalid session"; got != want {
		t.Errorf("extractSAPError() = %q, want %q", got, want)
	}

	if got := extractSAPError([]byte(`not json`)); got != "" {
		t.Errorf("extractSAPError(garbage) = %q, want empty string", got)
	}

	if got := extractSAPError(nil); got != "" {
		t.Errorf("extractSAPError(nil) = %q, want empty string", got)
	}
}
