// Copyright 2026 daman8271 and contributors. Licensed under Apache-2.0. See LICENSE.
// Hand-authored: multi-company support for the ji.jivo.in factory API.

package client

import (
	"fmt"
	"os"
	"strings"
)

// DefaultCompany is the Company-Code sent when nothing overrides it.
const DefaultCompany = "JIVO_MART"

// ValidCompanies are the Company-Code values ji.jivo.in accepts:
// JIVO_MART (id 2, retail/dispatch arm), JIVO_OIL (id 1, the manufacturer),
// JIVO_BEVERAGES (id 3).
var ValidCompanies = []string{"JIVO_MART", "JIVO_OIL", "JIVO_BEVERAGES"}

// NormalizeCompany maps user input (mart, oil, bev, jivo_oil, "Jivo Beverages",
// any case) to a canonical Company-Code, erroring on anything unrecognized.
// Empty input resolves to DefaultCompany.
func NormalizeCompany(v string) (string, error) {
	s := strings.ToUpper(strings.TrimSpace(v))
	s = strings.ReplaceAll(s, " ", "_")
	s = strings.ReplaceAll(s, "-", "_")
	if s != "" && !strings.HasPrefix(s, "JIVO_") {
		s = "JIVO_" + s
	}
	switch s {
	case "":
		return DefaultCompany, nil
	case "JIVO_MART":
		return "JIVO_MART", nil
	case "JIVO_OIL":
		return "JIVO_OIL", nil
	case "JIVO_BEVERAGES", "JIVO_BEV", "JIVO_BEVERAGE":
		return "JIVO_BEVERAGES", nil
	}
	return "", fmt.Errorf("unknown company %q (valid: JIVO_MART, JIVO_OIL, JIVO_BEVERAGES; shorthands mart/oil/beverages work)", v)
}

// CompanyCode returns the Company-Code header value for every API request.
// Resolution: JIVO_FACTORY_COMPANY env (the root --company flag sets it after
// validation) -> DefaultCompany. An invalid env value falls back to the
// default here; the root command validates and errors before requests run.
func CompanyCode() string {
	if code, err := NormalizeCompany(os.Getenv("JIVO_FACTORY_COMPANY")); err == nil {
		return code
	}
	return DefaultCompany
}
