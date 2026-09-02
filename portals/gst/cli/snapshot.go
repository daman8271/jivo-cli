package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/spf13/cobra"
)

// snapshot pulls a financial year's worth of reads for one or every
// registration and writes them to disk: the raw portal bodies (so a mapping bug
// can be fixed later without a new login) and the normalised records from
// normalise.go (so a reconciliation can diff them against SAP).
//
// Two behaviours matter more than the file layout:
//
//  1. IT NEVER PROMPTS. A snapshot is meant to run after `auth login`, possibly
//     unattended. A GSTIN with no session is recorded as "needs login" and the
//     run moves on; it is never a captcha in the middle of a batch.
//  2. IT NEVER ABORTS ON ONE REGISTRATION. Punjab's password has been wrong
//     since 2026-08-21; a run over --all must still produce the other seven.
//     Every failure is recorded in the manifest with the reason.
//
// Output layout:
//
//	<out>/manifest.json              what was pulled, when, from where, with what result
//	<out>/<gstin>/raw/<name>.json    the portal body, verbatim
//	<out>/<gstin>/records.jsonl      one normalised record per line (spec §3 envelope)

func init() { registerSection(newSnapshotCmd) }

func newSnapshotCmd(app *App) *cobra.Command {
	var fy, out string
	var skipDocs bool
	c := &cobra.Command{
		Use:   "snapshot",
		Short: "Pull a financial year of returns and ledgers to disk (raw JSON + normalised .jsonl)",
		Long: `Pull everything worth reconciling for a financial year and write it to --out.

Runs against --gstin, --state or --all. It never prompts for a captcha: a
registration with no cached session is recorded as "needs login" and skipped, so
log in first (` + "`gst-portal auth login --state <state>`" + `) for each one you want.
A registration whose session has expired mid-run is recorded and the run
continues with the next.

Periods after the current month are not requested — an unfiled future month is
not a finding, it is a calendar.`,
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			if out == "" {
				return errUsage("--out <directory> is required")
			}
			if _, err := parseFY(fy); err != nil {
				return err
			}
			// Unlike doctor, snapshot does NOT default to every registration:
			// it is the most expensive thing this CLI does (hundreds of calls to
			// a statutory portal) and running it estate-wide has to be asked for.
			if len(app.Sel) == 0 {
				return errUsage("snapshot needs a selection: --gstin <GSTIN>, --state <name|code>, or --all")
			}
			return app.runSnapshot(fy, out, skipDocs)
		},
	}
	c.Flags().StringVar(&fy, "fy", "", "financial year, YYYY-YY (e.g. 2026-27)")
	c.Flags().StringVar(&out, "out", "", "output directory (created if missing; must be outside any git checkout)")
	c.Flags().BoolVar(&skipDocs, "skip-documents", false, "skip the per-period GSTR-3B/2B pulls; ledgers and filing status only")
	c.Flags().BoolVar(&app.All, "all", false, "snapshot every configured registration, one at a time")
	return c
}

// snapshotDirMode / snapshotFileMode match session.go: a snapshot is the whole
// pull — turnover, ITC, both ledgers, counterparty-level documents. It is as
// sensitive as the session file and gets the same 0700/0600, not 0755/0644.
const (
	snapshotDirMode  = 0o700
	snapshotFileMode = 0o600
)

// refuseInsideACheckout stops --out from pointing into a git working tree.
// `--out ./snap` inside this repo drops real financial data into a PUBLIC
// checkout as untracked-but-committable files; .gitignore only covers the
// literal out/. Writing outside every checkout is the only rule that holds for
// operator sparse clones too.
func refuseInsideACheckout(root string) error {
	for d := root; ; {
		if _, err := os.Stat(filepath.Join(d, ".git")); err == nil {
			return errUsage("--out %s is inside the git checkout at %s.\n"+
				"A snapshot holds real turnover, ITC and counterparty documents and this repo is public — "+
				"write it somewhere outside every checkout (e.g. ~/gst-snapshots/%s).",
				root, d, filepath.Base(root))
		}
		parent := filepath.Dir(d)
		if parent == d {
			return nil
		}
		d = parent
	}
}

// artefact is one pull's outcome, as recorded in the manifest.
type artefact struct {
	Name     string `json:"name"`
	Endpoint string `json:"endpoint"`
	Period   string `json:"period,omitempty"`
	Status   string `json:"status"` // ok | empty | error
	Note     string `json:"note,omitempty"`
	RawFile  string `json:"raw_file,omitempty"`
	Records  int    `json:"records"`
}

type regReport struct {
	GSTIN     string     `json:"gstin"`
	State     string     `json:"state"`
	StateCode string     `json:"state_code"`
	Status    string     `json:"status"` // ok | needs login | auth failed | partial
	Note      string     `json:"note,omitempty"`
	Records   int        `json:"records"`
	Artefacts []artefact `json:"artefacts"`
}

type manifest struct {
	Src            string      `json:"src"`
	FY             string      `json:"fy"`
	Out            string      `json:"out"`
	StartedAt      string      `json:"started_at"`
	FinishedAt     string      `json:"finished_at"`
	Periods        []string    `json:"periods"`
	Registrations  []regReport `json:"registrations"`
	TotalRecords   int         `json:"total_records"`
	ReadOnlyNotice string      `json:"read_only_notice"`
}

func (a *App) runSnapshot(fy, outDir string, skipDocs bool) error {
	periods, err := fyPeriods(fy)
	if err != nil {
		return err
	}
	periods = periodsUpToNow(periods)

	root, err := filepath.Abs(outDir)
	if err != nil {
		return errConfig("cannot resolve --out %s: %v", outDir, err)
	}
	if err := refuseInsideACheckout(root); err != nil {
		return err
	}
	if err := os.MkdirAll(root, snapshotDirMode); err != nil {
		return errConfig("cannot create %s: %v", root, err)
	}

	m := manifest{
		Src: "gst-portal", FY: fy, Out: root,
		StartedAt: nowIST().Format(time.RFC3339), Periods: periods,
		ReadOnlyNotice: "every artefact here is a READ; this tool cannot file, generate, pay or amend anything",
	}

	for _, reg := range a.Sel {
		rep := a.snapshotOne(reg, fy, periods, root, skipDocs)
		m.TotalRecords += rep.Records
		m.Registrations = append(m.Registrations, rep)
		a.logf("%s %-20s %s (%d records)", rep.GSTIN, rep.State, rep.Status, rep.Records)
	}
	m.FinishedAt = nowIST().Format(time.RFC3339)

	manifestPath := filepath.Join(root, "manifest.json")
	b, err := json.MarshalIndent(m, "", "  ")
	if err != nil {
		return err
	}
	if err := os.WriteFile(manifestPath, append(b, '\n'), snapshotFileMode); err != nil {
		return errConfig("cannot write %s: %v", manifestPath, err)
	}
	if a.JSON || a.Agent {
		return a.emitValue("snapshot", "", "", m, m.TotalRecords)
	}
	a.printf("%s", manifestPath)
	return nil
}

// snapshotOne pulls one registration. It returns rather than errors: a failed
// registration is data about the estate, not a reason to stop.
func (a *App) snapshotOne(reg Registration, fy string, periods []string, root string, skipDocs bool) regReport {
	rep := regReport{GSTIN: reg.GSTIN, State: reg.State, StateCode: reg.StateCode(), Status: "ok"}
	dir := filepath.Join(root, sanitiseGSTIN(reg.GSTIN))

	// No session? Say so and move on — snapshot never prompts.
	s, err := loadSession(reg.GSTIN)
	switch {
	case err != nil:
		rep.Status, rep.Note = "needs login", err.Error()
		return rep
	case s == nil:
		rep.Status = "needs login"
		rep.Note = "no cached session — run `gst-portal auth login --gstin " + reg.GSTIN + "` first"
		return rep
	case !s.authenticated():
		rep.Status = "needs login"
		rep.Note = "only a pre-login jar is cached — finish `auth login --captcha <digits>`"
		return rep
	case s.expired(sessionMaxAge):
		rep.Status = "needs login"
		rep.Note = fmt.Sprintf("cached session is %s old and assumed expired", time.Since(s.SavedAt).Round(time.Second))
		return rep
	}

	if err := os.MkdirAll(filepath.Join(dir, "raw"), snapshotDirMode); err != nil {
		rep.Status, rep.Note = "error", err.Error()
		return rep
	}
	w := &jsonlWriter{path: filepath.Join(dir, "records.jsonl")}
	defer w.close()

	cl := newClient(reg)
	cl.useSession(s)
	env := newEnvelope(reg, "")

	pull := func(label, period, endpoint string, query map[string]string,
		body map[string]any, norm func(json.RawMessage) []record) {

		art := artefact{Name: label, Endpoint: endpointURL(endpoint), Period: period}
		// The session died on an earlier pull. Spending the remaining ~30 calls
		// per registration proving it again is rude to a statutory portal — and
		// over a 12-period FY × 8 registrations it is ~450 pointless requests.
		// The early return after ustatus only ever caught the FIRST call; this
		// catches every later one.
		if rep.Status == "auth failed" {
			art.Status, art.Note = "skipped", "session already failed for this registration"
			rep.Artefacts = append(rep.Artefacts, art)
			return
		}
		var res Result
		var err error
		if body != nil {
			res, err = cl.do(endpoint, nil, nil, body)
		} else {
			res, err = cl.do(endpoint, nil, qsFromMap(query), nil)
		}
		switch {
		case err != nil:
			art.Status, art.Note = "error", err.Error()
			var aerr *authError
			if asAuthError(err, &aerr) && rep.Status == "ok" {
				rep.Status, rep.Note = "auth failed", err.Error()
			} else if rep.Status == "ok" {
				rep.Status = "partial"
			}
		case res.Empty:
			art.Status, art.Note = "empty", res.Note
		default:
			art.Status = "ok"
			file := filepath.Join(dir, "raw", label+".json")
			if err := os.WriteFile(file, indentJSON(res.Raw), snapshotFileMode); err != nil {
				art.Note = "raw not written: " + err.Error()
			} else {
				art.RawFile = relTo(root, file)
			}
			if norm != nil {
				recs := norm(res.Raw)
				art.Records = len(recs)
				rep.Records += len(recs)
				w.write(recs)
			}
		}
		rep.Artefacts = append(rep.Artefacts, art)
	}

	// Who is this, really? Everything else is scoped by the answer.
	isd, whoami := false, ""
	pull("ustatus", "", epUstatus, nil, nil, func(raw json.RawMessage) []record {
		isd = looksISD(raw)
		whoami = ustatusGSTIN(raw)
		return nil
	})
	if rep.Status == "auth failed" {
		return rep // the session is dead; spending 30 more calls proving it is rude
	}
	// A jar that authenticates as somebody else is the most dangerous thing that
	// can happen here: without this check a whole company's ledgers would be
	// written to another company's folder, correctly formatted and entirely
	// wrong. `auth login` makes the same check; a jar can also arrive by
	// `auth import` or by being copied, so snapshot repeats it.
	if whoami != "" && !strings.EqualFold(whoami, reg.GSTIN) {
		_ = os.Remove(filepath.Join(dir, "raw", "ustatus.json"))
		rep.Status = "wrong registration"
		rep.Note = fmt.Sprintf("the cached session belongs to %s, not %s — nothing was pulled; log in again for this registration", whoami, reg.GSTIN)
		rep.Artefacts = nil
		rep.Records = 0
		return rep
	}

	pull("filing-snapshot", "", epFilingSnapshot, nil, nil, nil)

	// Ledgers — the whole FY in one call each.
	start, _ := parseFY(fy)
	end := nowIST()
	if fyEnd := start.AddDate(1, 0, -1); fyEnd.Before(end) {
		end = fyEnd
	}
	fdate, tdate := portalDate(start), portalDate(end)

	pull("ledger-cash-balance", "", epCashBalance, nil, nil,
		func(raw json.RawMessage) []record {
			return normCashBalance(env.withEndpoint(endpointURL(epCashBalance)), raw)
		})
	pull("ledger-cash-statement", "", epCashDetails,
		map[string]string{"fdate": fdate, "tdate": tdate}, nil,
		func(raw json.RawMessage) []record {
			return normCashLedger(env.withEndpoint(endpointURL(epCashDetails)), raw)
		})
	pull("ledger-credit-balance", "", epITCBalance, nil, nil,
		func(raw json.RawMessage) []record {
			return normCreditBalance(env.withEndpoint(endpointURL(epITCBalance)), raw)
		})
	pull("ledger-credit-statement", "", epITCDetails,
		map[string]string{"fdate": fdate, "tdate": tdate}, nil,
		func(raw json.RawMessage) []record {
			return normCreditLedger(env.withEndpoint(endpointURL(epITCDetails)), raw)
		})

	if isd {
		// An ISD registration files GSTR-6, not 1/3B/2B. Asking for them returns
		// portal errors that look like breakage and are not.
		rep.Note = strings.TrimSpace(rep.Note + " ISD registration: GSTR-1/3B/2B were not requested (it files GSTR-6).")
		return rep
	}

	for _, form := range []string{"GSTR1", "GSTR3B"} {
		f := form
		pull("filed-"+f, "", epEfiledReturns, nil,
			map[string]any{"fy": fy, "rfp": "Monthly", "qtr": nil, "mth": nil, "rtntp": f},
			func(raw json.RawMessage) []record {
				return normFiled(env.withEndpoint(endpointURL(epEfiledReturns)), raw)
			})
	}

	for _, p := range periods {
		period := p
		for _, form := range []string{"GSTR1", "GSTR3B"} {
			f := form
			pull("status-"+f+"-"+period, period, epFormDetails,
				map[string]string{"rtn_prd": period, "rtn_typ": f}, nil,
				func(raw json.RawMessage) []record {
					return normFormDetails(env.withEndpoint(endpointURL(epFormDetails)), f, raw)
				})
		}
		if skipDocs {
			continue
		}
		pull("gstr3b-"+period, period, epGSTR3BSummary,
			map[string]string{"rtn_prd": period}, nil,
			func(raw json.RawMessage) []record {
				return normGSTR3B(env.withPeriod(period).withEndpoint(endpointURL(epGSTR3BSummary)), raw)
			})
		pull("gstr2b-"+period, period, epGSTR2BData,
			map[string]string{"rtnprd": period}, nil,
			func(raw json.RawMessage) []record {
				return normGSTR2B(env.withPeriod(period).withEndpoint(endpointURL(epGSTR2BData)), raw)
			})
	}
	return rep
}

// periodsUpToNow drops periods that have not happened yet.
func periodsUpToNow(periods []string) []string {
	now := nowIST()
	out := make([]string, 0, len(periods))
	for _, p := range periods {
		t, err := parsePeriod(p)
		if err != nil || t.After(now) {
			continue
		}
		out = append(out, p)
	}
	return out
}

// ustatusGSTIN reads the GSTIN the portal says this session belongs to.
func ustatusGSTIN(raw json.RawMessage) string {
	var u struct {
		GSTIN string `json:"gstin"`
	}
	if err := json.Unmarshal(raw, &u); err != nil {
		return ""
	}
	return u.GSTIN
}

// looksISD reports whether ustatus describes an Input Service Distributor.
func looksISD(raw json.RawMessage) bool {
	var u struct {
		Utype   string `json:"utype"`
		RegType string `json:"regType"`
		Dty     string `json:"dty"`
	}
	if err := json.Unmarshal(raw, &u); err != nil {
		return false
	}
	for _, s := range []string{u.Utype, u.RegType, u.Dty} {
		if strings.Contains(strings.ToUpper(s), "ISD") ||
			strings.Contains(strings.ToUpper(s), "INPUT SERVICE DISTRIBUTOR") {
			return true
		}
	}
	return false
}

// jsonlWriter appends normalised records, creating the file on first write so a
// registration that produced nothing leaves no empty file behind.
type jsonlWriter struct {
	path string
	buf  []byte
	err  error
}

func (w *jsonlWriter) write(recs []record) {
	for _, r := range recs {
		b, err := json.Marshal(r)
		if err != nil {
			w.err = err
			return
		}
		w.buf = append(w.buf, b...)
		w.buf = append(w.buf, '\n')
	}
}

func (w *jsonlWriter) close() {
	if len(w.buf) == 0 {
		return
	}
	_ = os.WriteFile(w.path, w.buf, snapshotFileMode)
}

// qsFromMap adapts the pull helper's plain map to the client's query builder.
func qsFromMap(m map[string]string) urlValues {
	if len(m) == 0 {
		return nil
	}
	kv := make([]string, 0, len(m)*2)
	for _, k := range sortedKeys(m) {
		kv = append(kv, k, m[k])
	}
	return qs(kv...)
}

func sortedKeys(m map[string]string) []string {
	out := make([]string, 0, len(m))
	for k := range m {
		out = append(out, k)
	}
	sortStrings(out)
	return out
}

func indentJSON(raw json.RawMessage) []byte {
	var v any
	if err := json.Unmarshal(raw, &v); err != nil {
		return raw
	}
	b, err := json.MarshalIndent(v, "", " ")
	if err != nil {
		return raw
	}
	return append(b, '\n')
}

func relTo(root, path string) string {
	if r, err := filepath.Rel(root, path); err == nil {
		return r
	}
	return path
}
