package main

import (
	"encoding/json"
	"fmt"
	"math"
	"strings"
)

// inr formats a rupee amount with Indian digit grouping (₹ + lakh/crore suffix).
// Modelled on dsr-cli/internal/cli/domain.go:147-183 so every JIVO tool prints
// money identically.
//
// ONE DELIBERATE DIFFERENCE from dsr-cli: the rupees are derived from the same
// rounded paise as the fraction. dsr-cli truncates the rupees (int64(v)) and
// then rounds the fraction separately, so when the paise round up to ".00" it
// loses a whole rupee and prints ₹99.00 for 99.999 — measured, byte-identical
// code, so the bug is fleet-wide. It is cosmetic (only this stderr line; JSON
// output uses r2()), but it should not be copied forward. dsr-cli needs the
// same fix; that is a separate change in a separate CLI.
//
// NOTE (CRITIQUE §6): on cmd.exe with a non-UTF-8 codepage the ₹ renders as
// mojibake. dsr-cli/sapb1 have the same behaviour and Accounts live with it;
// changing it here would make GST the odd one out. Revisit fleet-wide, not here.
func inr(v float64) string {
	neg := v < 0
	if neg {
		v = -v
	}
	paise := int64(math.Round(v * 100))
	whole := paise / 100
	frac := fmt.Sprintf(".%02d", paise%100)
	s := groupIndian(whole)
	out := "₹" + s + frac
	if v >= 1e7 {
		out += fmt.Sprintf(" (%.2f Cr)", v/1e7)
	} else if v >= 1e5 {
		out += fmt.Sprintf(" (%.2f L)", v/1e5)
	}
	if neg {
		out = "-" + out
	}
	return out
}

// groupIndian groups an integer with the Indian system (last 3, then pairs).
func groupIndian(n int64) string {
	s := fmt.Sprintf("%d", n)
	if len(s) <= 3 {
		return s
	}
	head := s[:len(s)-3]
	tail := s[len(s)-3:]
	var parts []string
	for len(head) > 2 {
		parts = append([]string{head[len(head)-2:]}, parts...)
		head = head[:len(head)-2]
	}
	parts = append([]string{head}, parts...)
	return strings.Join(parts, ",") + "," + tail
}

// maskedSecret renders a PASSWORD. Unlike masked(), it shows nothing at all:
// first-four/last-four is fine for an opaque token, but across JIVO's eight GST
// logins it would have revealed that every password shares a prefix and a
// suffix. A password is either configured or it is not; that is all an operator
// needs from a listing.
func maskedSecret(s string) string {
	if s == "" {
		return "MISSING"
	}
	return "present"
}

// masked renders a NON-SECRET identifier (a username, a token tail) for
// display: first four, ellipsis, last four.
// Anything short enough to guess from a prefix is reported as "present" only
// (portals/blinkit/cli/doctor.go:106-114).
func masked(s string) string {
	if s == "" {
		return "MISSING"
	}
	if len(s) <= 8 {
		return "present"
	}
	return s[:4] + "…" + s[len(s)-4:]
}

// prettyJSON re-indents a raw portal body; non-JSON is passed through as-is.
func prettyJSON(raw json.RawMessage) string {
	var v any
	if err := json.Unmarshal(raw, &v); err != nil {
		return string(raw)
	}
	b, _ := json.MarshalIndent(v, "", "  ")
	return string(b)
}

// bestEffortCount reports a row count for the agent envelope: a top-level array,
// else a common GST list field (one `data` unwrap first), else 1 for an object.
func bestEffortCount(raw json.RawMessage) int {
	var arr []json.RawMessage
	if err := json.Unmarshal(raw, &arr); err == nil {
		return len(arr)
	}
	var obj map[string]json.RawMessage
	if err := json.Unmarshal(raw, &obj); err == nil {
		if d, ok := obj["data"]; ok {
			var a []json.RawMessage
			if json.Unmarshal(d, &a) == nil {
				return len(a)
			}
			var inner map[string]json.RawMessage
			if json.Unmarshal(d, &inner) == nil {
				obj = inner
			}
		}
		// GST's own list keys, most specific first.
		for _, k := range []string{"tr", "formNames", "user", "sec_count", "retPrds", "b2b", "rows", "records", "items", "list", "data"} {
			if v, ok := obj[k]; ok {
				var a []json.RawMessage
				if json.Unmarshal(v, &a) == nil {
					return len(a)
				}
			}
		}
		return 1
	}
	return 0
}
