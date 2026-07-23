package main

import "time"

// istLoc is the reporting timezone. Blinkit data is reckoned in IST, and the
// fleet crons run on IST, so all default date math is anchored here.
var istLoc = mustLoadIST()

func mustLoadIST() *time.Location {
	loc, err := time.LoadLocation("Asia/Kolkata")
	if err != nil {
		// Fixed +05:30 fallback if the tzdata is unavailable.
		return time.FixedZone("IST", 5*3600+30*60)
	}
	return loc
}

// defaultSalesRange returns the default window relative to now:
// from = first day of now's month, to = T-1 (yesterday). Dates are
// formatted YYYY-MM-DD in IST.
func defaultSalesRange(now time.Time) (from, to string) {
	n := now.In(istLoc)
	monthStart := time.Date(n.Year(), n.Month(), 1, 0, 0, 0, 0, istLoc)
	yesterday := n.AddDate(0, 0, -1)
	return monthStart.Format("2006-01-02"), yesterday.Format("2006-01-02")
}

// today returns today's date in IST as YYYY-MM-DD.
func today(now time.Time) string {
	return now.In(istLoc).Format("2006-01-02")
}
