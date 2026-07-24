package main

import (
	"fmt"
	"time"
)

// istLoc is Asia/Kolkata; Zepto date windows are IST wall-clock.
var istLoc = mustLoadIST()

func mustLoadIST() *time.Location {
	l, err := time.LoadLocation("Asia/Kolkata")
	if err != nil {
		// fixed +05:30 fallback if the tz database is unavailable
		return time.FixedZone("IST", 5*3600+30*60)
	}
	return l
}

// defaultSalesRange returns (from, to) as YYYY-MM-DD: from = 1st of the current
// IST month, to = yesterday (T-1) — the convention the portal's own report
// requests use for the Sales window.
func defaultSalesRange(now time.Time) (string, string) {
	n := now.In(istLoc)
	from := time.Date(n.Year(), n.Month(), 1, 0, 0, 0, 0, istLoc)
	to := n.AddDate(0, 0, -1)
	return from.Format("2006-01-02"), to.Format("2006-01-02")
}

// istDayBounds returns the UTC-ISO start/end of a given IST day (00:00:00 →
// 23:59:59), the format the ads-bff analytics reports expect.
func istDayBounds(day time.Time) (string, string) {
	d := day.In(istLoc)
	start := time.Date(d.Year(), d.Month(), d.Day(), 0, 0, 0, 0, istLoc)
	end := time.Date(d.Year(), d.Month(), d.Day(), 23, 59, 59, 0, istLoc)
	return start.Format("2006-01-02 15:04:05"), end.Format("2006-01-02 15:04:05")
}

// yyyymmdd formats an IST date; helper for building query params.
func yyyymmdd(t time.Time) string {
	return t.In(istLoc).Format("2006-01-02")
}

// mustRange is a tiny helper for commands that accept optional --from/--to and
// default to the sales range; returns an error string if only one is set.
func resolveRange(from, to string) (string, string, error) {
	if (from == "") != (to == "") {
		return "", "", fmt.Errorf("provide both --from and --to (YYYY-MM-DD), or neither")
	}
	if from == "" {
		f, t := defaultSalesRange(time.Now())
		return f, t, nil
	}
	return from, to, nil
}
