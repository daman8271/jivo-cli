package main

import (
	"fmt"
	"strconv"
	"strings"
	"time"
)

// istLoc is Asia/Kolkata. Every GST date is IST wall-clock; the portal has no
// timezone in any of its date fields.
var istLoc = mustLoadIST()

func mustLoadIST() *time.Location {
	l, err := time.LoadLocation("Asia/Kolkata")
	if err != nil {
		// fixed +05:30 fallback if the tz database is unavailable (Windows)
		return time.FixedZone("IST", 5*3600+30*60)
	}
	return l
}

// parsePeriod parses a GST return period code, `MMYYYY` (RECON.md:28 — the
// portal's own dropdown emits these, e.g. 072026 = July 2026).
func parsePeriod(p string) (time.Time, error) {
	if len(p) != 6 {
		return time.Time{}, errUsage("period %q is not MMYYYY (e.g. 072026 for July 2026)", p)
	}
	// strconv.Atoi accepts a leading sign, so "+72026" would parse as July 2026
	// and then go on the wire as rtn_prd=%2B72026. A period code is six digits.
	for _, r := range p {
		if r < '0' || r > '9' {
			return time.Time{}, errUsage("period %q is not MMYYYY (e.g. 072026 for July 2026)", p)
		}
	}
	mm, err1 := strconv.Atoi(p[:2])
	yyyy, err2 := strconv.Atoi(p[2:])
	if err1 != nil || err2 != nil || mm < 1 || mm > 12 || yyyy < 2017 || yyyy > 2099 {
		return time.Time{}, errUsage("period %q is not MMYYYY (e.g. 072026 for July 2026)", p)
	}
	return time.Date(yyyy, time.Month(mm), 1, 0, 0, 0, 0, istLoc), nil
}

// formatPeriod renders a month as the portal's MMYYYY code.
func formatPeriod(t time.Time) string { return t.In(istLoc).Format("012006") }

// parseFY parses an Indian financial year label "2026-27" and returns its April
// start. The second half must be the first half + 1 — "2026-28" is not a FY.
func parseFY(fy string) (time.Time, error) {
	parts := strings.Split(fy, "-")
	if len(parts) != 2 || len(parts[0]) != 4 || len(parts[1]) != 2 {
		return time.Time{}, errUsage("financial year %q is not YYYY-YY (e.g. 2026-27)", fy)
	}
	y, err := strconv.Atoi(parts[0])
	if err != nil {
		return time.Time{}, errUsage("financial year %q is not YYYY-YY (e.g. 2026-27)", fy)
	}
	end, err := strconv.Atoi(parts[1])
	if err != nil || (y+1)%100 != end {
		return time.Time{}, errUsage("financial year %q is not YYYY-YY with consecutive years (e.g. 2026-27)", fy)
	}
	return time.Date(y, time.April, 1, 0, 0, 0, 0, istLoc), nil
}

// fyPeriods expands a financial year into its 12 MMYYYY period codes,
// April → March.
func fyPeriods(fy string) ([]string, error) {
	start, err := parseFY(fy)
	if err != nil {
		return nil, err
	}
	out := make([]string, 0, 12)
	for i := 0; i < 12; i++ {
		out = append(out, formatPeriod(start.AddDate(0, i, 0)))
	}
	return out, nil
}

// fyOfPeriod reports the financial year a period belongs to (April–March).
func fyOfPeriod(period string) string {
	t, err := parsePeriod(period)
	if err != nil {
		return ""
	}
	y := t.Year()
	if t.Month() < time.April {
		y--
	}
	return fmt.Sprintf("%d-%02d", y, (y+1)%100)
}

// parsePortalDate accepts both spellings the portal uses: `dd/mm/yyyy`
// (itcdtls, cashdetls, efiledReturns.dof) and `dd-mm-yyyy` (formdetails.fil_dt).
func parsePortalDate(s string) (time.Time, error) {
	s = strings.TrimSpace(s)
	for _, layout := range []string{"02/01/2006", "02-01-2006"} {
		if t, err := time.ParseInLocation(layout, s, istLoc); err == nil {
			return t, nil
		}
	}
	return time.Time{}, errUsage("date %q is not dd/mm/yyyy or dd-mm-yyyy", s)
}

// parseISODate parses the CLI's own date flags, YYYY-MM-DD, in IST.
func parseISODate(s string) (time.Time, error) {
	t, err := time.ParseInLocation("2006-01-02", strings.TrimSpace(s), istLoc)
	if err != nil {
		return time.Time{}, errUsage("date %q is not YYYY-MM-DD", s)
	}
	return t, nil
}

// isoDate renders a date as YYYY-MM-DD (the envelope + flag format).
func isoDate(t time.Time) string { return t.In(istLoc).Format("2006-01-02") }

// portalDate renders a date as dd/mm/yyyy (what the ledger query params want).
func portalDate(t time.Time) string { return t.In(istLoc).Format("02/01/2006") }

// nowIST is a variable so tests can pin the clock.
var nowIST = func() time.Time { return time.Now().In(istLoc) }
