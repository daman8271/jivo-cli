package main

import "testing"

// TestForbiddenPathBlocksWrites asserts the guardrail refuses the mis-tagged
// writes (extractor said READ, call sites say WRITE) and all non-GET/POST methods.
func TestForbiddenPathBlocksWrites(t *testing.T) {
	blocked := []string{
		"https://business.tankhapay.com/api/master/saveDesignation",
		"https://business.tankhapay.com/api/master/saveDepartmentUnit",
		"https://business.tankhapay.com/api/dashboard/insert_birthday_wishes",
		"https://business.tankhapay.com/api/dashboard/send_wishes_email",
		"https://business.tankhapay.com/api/dashboard/enable_desable_alert",
		"https://business.tankhapay.com/api/master/update_employer_mobile_email",
		"https://business.tankhapay.com/api/master/bulk_insert_holiday_master",
		"https://business.tankhapay.com/api/master/mapEmployee",
		"https://business.tankhapay.com/api/Report/disburseLiability",
		"https://business.tankhapay.com/api/Report/deleteLiabilityReportApi",
		"https://business.tankhapay.com/api/Report/CloseFinancialYear",
		"https://business.tankhapay.com/api/Report/reprocess_today_checkinout",
		"https://business.tankhapay.com/api/Report/SubmitEsicForBusiness",
		"https://business.tankhapay.com/api/Report/sendSalaryPdf",
		"https://business.tankhapay.com/api/refresh_account_details",
		"https://business.tankhapay.com/api/verify_OTP",
		"https://business.tankhapay.com/api/verify_user_otp",
	}
	for _, u := range blocked {
		if err := forbiddenPath("POST", u); err == nil {
			t.Errorf("expected BLOCK, was allowed: %s", u)
		}
	}
	for _, m := range []string{"PUT", "PATCH", "DELETE", "OPTIONS"} {
		if err := forbiddenPath(m, "https://business.tankhapay.com/api/get_x"); err == nil {
			t.Errorf("expected method %s to be blocked", m)
		}
	}
}

// TestForbiddenPathAllowsReads asserts genuine reads pass — including the noun
// false-friends (payout, punch, sync, process, disbursment) that a naive scan
// would wrongly kill.
func TestForbiddenPathAllowsReads(t *testing.T) {
	allowed := []string{
		"https://business.tankhapay.com/api/dashboard/get_tpay_dashboard_data",
		"https://business.tankhapay.com/api/getPayoutTransactionsDetails",
		"https://business.tankhapay.com/api/getAttendancePunchData",
		"https://business.tankhapay.com/api/get_Last_sync_stataus",
		"https://business.tankhapay.com/api/get_process_biomatric_data",
		"https://business.tankhapay.com/api/Report/DisbursmentReportApi",
		"https://business.tankhapay.com/api/Report/SalarySlip",
		"https://business.tankhapay.com/api/Report/liabilityReportCombined",
		"https://mobapi.tankhapay.com/api/TpTaxesApi/GetHomeLoanDetails",
		"https://business.tankhapay.com/api/manageEmployee",
	}
	for _, u := range allowed {
		if err := forbiddenPath("POST", u); err != nil {
			t.Errorf("expected ALLOW, was blocked: %s → %v", u, err)
		}
	}
}
