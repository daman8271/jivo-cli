package cli

import (
	"encoding/json"
	"errors"
	"io"
	"mime"
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"testing"

	"sapb1/internal/errs"
)

// fakeAttachSAP is a Service Layer that keeps real Attachments2 rows, so a test
// can check what the row reads back as, not only what was sent.
type fakeAttachSAP struct {
	logPath    string
	withStamp  bool // the book has U_CHK/U_CHK2 on ATC1 (Oil, Beverages); false = Mart
	ignoreTick bool // accept the PATCH but never change CopyToTargetDoc
	failTick   bool // refuse the tick PATCH
	corrupt    bool // serve different bytes on $value
	// hangUpUpload makes upload number N (1-based) land and then drop the
	// connection before answering — the "outcome unknown" case.
	hangUpUpload int
	refuseUpload int // upload number N is refused with a 400
	logins       int
	content      map[string][]byte // "row/name" -> bytes on the "share"
	next         int64
	rows         map[int64][]map[string]interface{}
	uploads      []string // "METHOD path filename content-type"
	patches      []string // JSON bodies of the tick PATCHes
	requests     int
}

var (
	attachRowPath   = regexp.MustCompile(`^/b1s/v1/Attachments2\((\d+)\)$`)
	attachValuePath = regexp.MustCompile(`^/b1s/v1/Attachments2\((\d+)\)/\$value$`)
)

// uploadFails answers the upload with a refusal when this is the upload the
// test asked to refuse. The count includes the one being refused.
func (f *fakeAttachSAP) uploadFails(w http.ResponseWriter) bool {
	if f.refuseUpload != len(f.uploads)+1 {
		return false
	}
	f.uploads = append(f.uploads, "REFUSED")
	w.WriteHeader(http.StatusBadRequest)
	_, _ = w.Write([]byte(`{"error":{"code":-1,"message":{"value":"refused by the fake"}}}`))
	return true
}

// hangUp closes the connection without an answer: the request was handled,
// the client never hears so.
func hangUp(w http.ResponseWriter) {
	if hj, ok := w.(http.Hijacker); ok {
		if conn, _, err := hj.Hijack(); err == nil {
			_ = conn.Close()
		}
	}
}

func newFakeAttachSAP(t *testing.T, withStamp bool) *fakeAttachSAP {
	t.Helper()
	f := &fakeAttachSAP{withStamp: withStamp, next: 178000, rows: map[int64][]map[string]interface{}{}, content: map[string][]byte{}}
	srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if strings.HasSuffix(r.URL.Path, "/Login") {
			f.logins++
			http.SetCookie(w, &http.Cookie{Name: "B1SESSION", Value: "fake-session"})
			_, _ = w.Write([]byte(`{"SessionId":"fake-session"}`))
			return
		}
		f.requests++
		ct := r.Header.Get("Content-Type")
		switch {
		case r.Method == http.MethodPost && r.URL.Path == "/b1s/v1/Attachments2":
			name, data, ok := f.readFile(t, r)
			if !ok {
				w.WriteHeader(http.StatusBadRequest)
				return
			}
			if f.uploadFails(w) {
				return
			}
			f.next++
			f.rows[f.next] = []map[string]interface{}{f.line(1, name, len(data))}
			f.content[strconv.FormatInt(f.next, 10)+"/"+name] = data
			f.uploads = append(f.uploads, "POST Attachments2 "+name+" "+partType(t, r, ct))
			if f.hangUpUpload == len(f.uploads) {
				hangUp(w)
				return
			}
			w.WriteHeader(http.StatusCreated)
			_ = json.NewEncoder(w).Encode(map[string]interface{}{"AbsoluteEntry": f.next, "Attachments2_Lines": f.rows[f.next]})
		case attachValuePath.MatchString(r.URL.Path):
			n := attachValuePath.FindStringSubmatch(r.URL.Path)[1]
			name := strings.TrimSuffix(strings.TrimPrefix(r.URL.Query().Get("filename"), "'"), "'")
			data, ok := f.content[n+"/"+name]
			if !ok {
				w.WriteHeader(http.StatusNotFound)
				_, _ = w.Write([]byte(`{"error":{"code":406,"message":{"value":"attachment not found"}}}`))
				return
			}
			if f.corrupt {
				data = append([]byte("X"), data...)
			}
			_, _ = w.Write(data)
		case attachRowPath.MatchString(r.URL.Path):
			n, _ := strconv.ParseInt(attachRowPath.FindStringSubmatch(r.URL.Path)[1], 10, 64)
			lines, found := f.rows[n]
			if !found {
				w.WriteHeader(http.StatusNotFound)
				_, _ = w.Write([]byte(`{"error":{"code":-2028,"message":{"value":"No matching records found"}}}`))
				return
			}
			switch {
			case r.Method == http.MethodGet:
				_ = json.NewEncoder(w).Encode(map[string]interface{}{"AbsoluteEntry": n, "Attachments2_Lines": lines})
			case r.Method == http.MethodPatch && strings.HasPrefix(ct, "multipart/form-data"):
				name, data, ok := f.readFile(t, r)
				if !ok {
					w.WriteHeader(http.StatusBadRequest)
					return
				}
				if f.uploadFails(w) {
					return
				}
				f.rows[n] = append(lines, f.line(int64(len(lines)+1), name, len(data)))
				f.content[strconv.FormatInt(n, 10)+"/"+name] = data
				f.uploads = append(f.uploads, "PATCH Attachments2("+strconv.FormatInt(n, 10)+") "+name+" "+partType(t, r, ct))
				if f.hangUpUpload == len(f.uploads) {
					hangUp(w)
					return
				}
				w.WriteHeader(http.StatusNoContent)
			case r.Method == http.MethodPatch:
				body, _ := io.ReadAll(r.Body)
				f.patches = append(f.patches, string(body))
				if f.failTick {
					w.WriteHeader(http.StatusBadRequest)
					_, _ = w.Write([]byte(`{"error":{"code":-5002,"message":{"value":"refused by the fake"}}}`))
					return
				}
				var p struct {
					Lines []map[string]interface{} `json:"Attachments2_Lines"`
				}
				if err := json.Unmarshal(body, &p); err != nil {
					w.WriteHeader(http.StatusBadRequest)
					return
				}
				for _, pl := range p.Lines {
					if !f.withStamp {
						if _, has := pl["U_CHK2"]; has {
							// Mart: an unknown field fails the whole PATCH, as the live server does.
							w.WriteHeader(http.StatusBadRequest)
							_, _ = w.Write([]byte(`{"error":{"code":-1000,"message":{"value":"Property 'U_CHK2' of 'Attachments2_Line' is invalid"}}}`))
							return
						}
					}
				}
				for _, pl := range p.Lines {
					ln := int64(pl["LineNum"].(float64))
					for _, l := range lines {
						if l["LineNum"].(int64) != ln {
							continue
						}
						for k, v := range pl {
							if k == "CopyToTargetDoc" && f.ignoreTick {
								continue
							}
							if k != "AbsoluteEntry" && k != "LineNum" {
								l[k] = v
							}
						}
					}
				}
				w.WriteHeader(http.StatusNoContent)
			default:
				w.WriteHeader(http.StatusMethodNotAllowed)
			}
		default:
			w.WriteHeader(http.StatusNotFound)
		}
	}))
	t.Cleanup(srv.Close)
	u, err := url.Parse(srv.URL)
	if err != nil {
		t.Fatal(err)
	}
	f.logPath = pointCLIAtFake(t, u)
	return f
}

func (f *fakeAttachSAP) line(n int64, name string, size int) map[string]interface{} {
	base := strings.TrimSuffix(name, filepath.Ext(name))
	l := map[string]interface{}{
		"LineNum":         n,
		"FileName":        base,
		"FileExtension":   strings.TrimPrefix(filepath.Ext(name), "."),
		"FileSize":        float64((size + 1023) / 1024),
		"CopyToTargetDoc": "tNO", // what a live API upload lands as
	}
	if f.withStamp {
		l["U_CHK"] = nil
		l["U_CHK2"] = nil
	}
	return l
}

// readFile pulls the one "files" part out of a multipart upload.
func (f *fakeAttachSAP) readFile(t *testing.T, r *http.Request) (string, []byte, bool) {
	t.Helper()
	if err := r.ParseMultipartForm(32 << 20); err != nil {
		t.Errorf("upload was not multipart/form-data: %v", err)
		return "", nil, false
	}
	fhs := r.MultipartForm.File["files"]
	if len(fhs) != 1 {
		t.Errorf("upload carried %d parts under \"files\", want 1", len(fhs))
		return "", nil, false
	}
	fh, err := fhs[0].Open()
	if err != nil {
		t.Errorf("opening the uploaded part: %v", err)
		return "", nil, false
	}
	defer fh.Close()
	data, _ := io.ReadAll(fh)
	return fhs[0].Filename, data, true
}

func partType(t *testing.T, r *http.Request, ct string) string {
	t.Helper()
	if _, params, err := mime.ParseMediaType(ct); err == nil && params["boundary"] != "" {
		return r.MultipartForm.File["files"][0].Header.Get("Content-Type")
	}
	return "?"
}

func writeTempFile(t *testing.T, name string, size int) string {
	t.Helper()
	p := filepath.Join(t.TempDir(), name)
	if err := os.WriteFile(p, []byte(strings.Repeat("x", size)), 0o600); err != nil {
		t.Fatal(err)
	}
	return p
}

func TestAttachUploadsTicksAndStampsEveryLineInOil(t *testing.T) {
	f := newFakeAttachSAP(t, true)
	withTTY(t, false)
	bill := writeTempFile(t, "PICKSHIP-NCR-358.pdf", 5000)
	grpo := writeTempFile(t, "GRPO-2026086899-bill.pdf", 3000)

	stdout, _, err := execWrite(t, "", "attach", bill, grpo, "--yes")
	if err != nil {
		t.Fatalf("attach failed: %v", err)
	}

	want := []string{
		"POST Attachments2 PICKSHIP-NCR-358.pdf application/pdf",
		"PATCH Attachments2(178001) GRPO-2026086899-bill.pdf application/pdf",
	}
	if strings.Join(f.uploads, "\n") != strings.Join(want, "\n") {
		t.Errorf("uploads = %q, want %q", f.uploads, want)
	}
	if len(f.patches) != 1 {
		t.Fatalf("tick PATCHes = %d, want exactly 1 for the whole row", len(f.patches))
	}
	for _, l := range f.rows[178001] {
		if l["CopyToTargetDoc"] != "tYES" || l["U_CHK2"] != "OK" || l["U_CHK"] != l["FileSize"] {
			t.Errorf("line %v read back %v, want tYES + U_CHK = FileSize + U_CHK2 OK", l["LineNum"], l)
		}
	}
	if !strings.Contains(stdout, "row 178001") || !strings.Contains(stdout, "all 2 line(s)") {
		t.Errorf("output should name the row and the line count, got:\n%s", stdout)
	}
}

func TestAttachInMartSendsTheTickAlone(t *testing.T) {
	f := newFakeAttachSAP(t, false)
	withTTY(t, false)
	bill := writeTempFile(t, "4027.pdf", 2000)

	if _, _, err := execWrite(t, "", "attach", bill, "--yes"); err != nil {
		t.Fatalf("attach failed in a book without U_CHK: %v", err)
	}
	if len(f.patches) != 1 || strings.Contains(f.patches[0], "U_CHK") {
		t.Fatalf("Mart PATCH must carry CopyToTargetDoc alone, got %q", f.patches)
	}
	if f.rows[178001][0]["CopyToTargetDoc"] != "tYES" {
		t.Errorf("line did not end tYES: %v", f.rows[178001][0])
	}
}

func TestAttachFailsExit8WhenTheTickDoesNotReadBack(t *testing.T) {
	f := newFakeAttachSAP(t, true)
	f.ignoreTick = true
	withTTY(t, false)
	bill := writeTempFile(t, "bill.pdf", 100)

	_, _, err := execWrite(t, "", "attach", bill, "--yes")
	var verr *errs.WriteVerifyError
	if !errors.As(err, &verr) {
		t.Fatalf("want *errs.WriteVerifyError (exit 8), got %T: %v", err, err)
	}
	if ExitCodeFor(err) != ExitVerifyFailed {
		t.Errorf("exit code = %d, want %d", ExitCodeFor(err), ExitVerifyFailed)
	}
	if !strings.Contains(verr.Msg, "attach --row 178001") {
		t.Errorf("the failure must hand over the recovery command, got: %s", verr.Msg)
	}
}

func TestAttachRowOnlyReticksAnExistingRow(t *testing.T) {
	f := newFakeAttachSAP(t, true)
	withTTY(t, false)
	f.rows[176525] = []map[string]interface{}{
		{"LineNum": int64(1), "FileName": "CASH-VCH-437", "FileSize": 761, "U_CHK": 761, "U_CHK2": "OK", "CopyToTargetDoc": "tNO"},
		{"LineNum": int64(2), "FileName": "GRPO-bill", "FileSize": 115, "U_CHK": nil, "U_CHK2": nil, "CopyToTargetDoc": "tNO"},
	}

	if _, _, err := execWrite(t, "", "attach", "--row", "176525", "--yes"); err != nil {
		t.Fatalf("re-tick failed: %v", err)
	}
	if len(f.uploads) != 0 {
		t.Errorf("--row with no files must upload nothing, uploaded %q", f.uploads)
	}
	if got := f.rows[176525][0]["U_CHK"]; got != 761 {
		t.Errorf("an existing U_CHK must be kept, got %v", got)
	}
	for _, l := range f.rows[176525] {
		if l["CopyToTargetDoc"] != "tYES" || l["U_CHK2"] != "OK" {
			t.Errorf("line %v = %v, want tYES + OK", l["LineNum"], l)
		}
	}
}

func TestAttachSendsNoPatchWhenTheRowIsAlreadyTicked(t *testing.T) {
	f := newFakeAttachSAP(t, false)
	withTTY(t, false)
	f.rows[59273] = []map[string]interface{}{{"LineNum": int64(1), "FileName": "4027", "FileSize": 1661, "CopyToTargetDoc": "tYES"}}

	if _, _, err := execWrite(t, "", "attach", "--row", "59273", "--yes"); err != nil {
		t.Fatalf("attach --row on a ticked row failed: %v", err)
	}
	if len(f.patches) != 0 {
		t.Errorf("nothing to change, but a PATCH was sent: %q", f.patches)
	}
}

func TestAttachDryRunAndRefusalsSendNothing(t *testing.T) {
	bill := filepath.Join(t.TempDir(), "bill.pdf")
	if err := os.WriteFile(bill, []byte("%PDF-1.4"), 0o600); err != nil {
		t.Fatal(err)
	}
	sameName := filepath.Join(t.TempDir(), "BILL.pdf")
	if err := os.WriteFile(sameName, []byte("%PDF-1.4 other"), 0o600); err != nil {
		t.Fatal(err)
	}
	empty := filepath.Join(t.TempDir(), "empty.pdf")
	if err := os.WriteFile(empty, nil, 0o600); err != nil {
		t.Fatal(err)
	}

	cases := []struct {
		name  string
		tty   bool
		args  []string
		usage bool
	}{
		{"dry run", false, []string{"attach", bill, "--dry-run"}, false},
		{"no --yes without a terminal", false, []string{"attach", bill}, true},
		{"missing second file", false, []string{"attach", bill, "/nope/missing.pdf", "--yes"}, true},
		{"empty file", false, []string{"attach", empty, "--yes"}, true},
		{"no file and no row", false, []string{"attach", "--yes"}, true},
		{"negative row", false, []string{"attach", "--row", "-4", "--yes"}, true},
		{"two files by one name", false, []string{"attach", bill, sameName, "--yes"}, true},
		{"wrong answer at the prompt", true, []string{"attach", bill}, true},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			f := newFakeAttachSAP(t, true)
			withTTY(t, tc.tty)
			_, _, err := execWrite(t, "y\n", tc.args...)
			if tc.usage {
				requireUsageError(t, err)
			} else if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}
			if f.requests != 0 || f.logins != 0 {
				t.Errorf("%d request(s) and %d login(s) reached SAP, want none", f.requests, f.logins)
			}
		})
	}
}

func TestAttachLogsTheFileHashNotItsBytes(t *testing.T) {
	f := newFakeAttachSAP(t, true)
	withTTY(t, false)
	secret := "VENDOR-BANK-ACCOUNT-0000111122223333"
	p := filepath.Join(t.TempDir(), "bill.pdf")
	if err := os.WriteFile(p, []byte(secret), 0o600); err != nil {
		t.Fatal(err)
	}

	if _, _, err := execWrite(t, "", "attach", p, "--yes"); err != nil {
		t.Fatalf("attach failed: %v", err)
	}
	data, err := os.ReadFile(f.logPath)
	if err != nil {
		t.Fatal(err)
	}
	log := string(data)
	if strings.Contains(log, secret) {
		t.Fatal("the file's bytes reached the write log")
	}
	for _, want := range []string{`"path":"Attachments2"`, `"sha256":"`, `"file":"bill.pdf"`, `"path":"Attachments2(178001)"`, `"CopyToTargetDoc":"tYES"`} {
		if !strings.Contains(log, want) {
			t.Errorf("write log should contain %s, got:\n%s", want, log)
		}
	}
}

func TestAttachFailsExit8WhenAFileDoesNotReadBackAsSent(t *testing.T) {
	f := newFakeAttachSAP(t, true)
	f.corrupt = true
	withTTY(t, false)

	_, _, err := execWrite(t, "", "attach", writeTempFile(t, "bill.pdf", 900), "--yes")
	if ExitCodeFor(err) != ExitVerifyFailed {
		t.Fatalf("exit = %d (%v), want %d", ExitCodeFor(err), err, ExitVerifyFailed)
	}
	if !strings.Contains(err.Error(), "did not read back as sent") {
		t.Errorf("message should say the bytes differ, got: %v", err)
	}
}

func TestAttachRefusedSecondUploadIsExit8AndTheRowIsTicked(t *testing.T) {
	f := newFakeAttachSAP(t, true)
	f.refuseUpload = 2
	withTTY(t, false)

	_, _, err := execWrite(t, "", "attach", writeTempFile(t, "a.pdf", 10), writeTempFile(t, "b.pdf", 10), "--yes")
	if ExitCodeFor(err) != ExitVerifyFailed {
		t.Fatalf("exit = %d (%v), want 8 — a row exists, so it is never 'nothing happened'", ExitCodeFor(err), err)
	}
	if f.rows[178001][0]["CopyToTargetDoc"] != "tYES" {
		t.Errorf("the line that landed must still be ticked: %v", f.rows[178001][0])
	}
	if !strings.Contains(err.Error(), "attach --row 178001 <file> --yes") {
		t.Errorf("message should hand over the add-the-rest command, got: %v", err)
	}
}

func TestAttachLostAnswerOnSecondUploadIsExit7AndSaysLookFirst(t *testing.T) {
	f := newFakeAttachSAP(t, true)
	f.hangUpUpload = 2
	withTTY(t, false)

	_, _, err := execWrite(t, "", "attach", writeTempFile(t, "a.pdf", 10), writeTempFile(t, "b.pdf", 10), "--yes")
	if ExitCodeFor(err) != ExitWriteUnknown {
		t.Fatalf("exit = %d (%v), want 7", ExitCodeFor(err), err)
	}
	if !strings.Contains(err.Error(), "LOOK before sending it again") {
		t.Errorf("an unknown outcome must say look first, got: %v", err)
	}
	for _, l := range f.rows[178001] {
		if l["CopyToTargetDoc"] != "tYES" {
			t.Errorf("every line that landed must be ticked, line %v = %v", l["LineNum"], l["CopyToTargetDoc"])
		}
	}
}

func TestAttachLostAnswerOnFirstUploadIsExit7WithAWayToFindTheRow(t *testing.T) {
	f := newFakeAttachSAP(t, true)
	f.hangUpUpload = 1
	withTTY(t, false)

	_, _, err := execWrite(t, "", "attach", writeTempFile(t, "a.pdf", 10), "--yes")
	if ExitCodeFor(err) != ExitWriteUnknown {
		t.Fatalf("exit = %d (%v), want 7", ExitCodeFor(err), err)
	}
	if !strings.Contains(err.Error(), `--orderby "AbsoluteEntry desc"`) {
		t.Errorf("message should say how to find the new row, got: %v", err)
	}
	if len(f.patches) != 0 {
		t.Errorf("no row number is known, so nothing may be ticked blind; patches = %q", f.patches)
	}
}

func TestAttachRefusedTickIsExit8NotAnAPIError(t *testing.T) {
	f := newFakeAttachSAP(t, false)
	f.failTick = true
	withTTY(t, false)

	_, _, err := execWrite(t, "", "attach", writeTempFile(t, "a.pdf", 10), "--yes")
	if ExitCodeFor(err) != ExitVerifyFailed {
		t.Fatalf("exit = %d (%v), want 8 — the file is up, so this is not 'nothing happened'", ExitCodeFor(err), err)
	}
	if !strings.Contains(err.Error(), "attach --row 178001 --yes") {
		t.Errorf("message should hand over the re-tick command, got: %v", err)
	}
}

func TestAttachRowThatDoesNotExistIsRefusedBeforeAnyWrite(t *testing.T) {
	f := newFakeAttachSAP(t, true)
	withTTY(t, false)

	_, _, err := execWrite(t, "", "attach", "--row", "777", writeTempFile(t, "a.pdf", 10), "--yes")
	requireUsageError(t, err, "does not exist")
	if len(f.uploads) != 0 || len(f.patches) != 0 {
		t.Errorf("nothing may be written to a row that is not there: uploads %q patches %q", f.uploads, f.patches)
	}
}

func TestAttachRowPreviewShowsWhatIsOnTheRowAndAddsAfterIt(t *testing.T) {
	f := newFakeAttachSAP(t, true)
	withTTY(t, false)
	f.rows[176525] = []map[string]interface{}{
		{"LineNum": int64(1), "FileName": "CASH-VCH-437", "FileExtension": "pdf", "FileSize": float64(761), "U_CHK": float64(761), "U_CHK2": "OK", "CopyToTargetDoc": "tYES"},
	}

	_, stderr, err := execWrite(t, "", "attach", "--row", "176525", writeTempFile(t, "GRPO-bill.pdf", 300), "--yes")
	if err != nil {
		t.Fatalf("attach --row with a file failed: %v", err)
	}
	if !strings.Contains(stderr, "row now : 1 line(s): CASH-VCH-437.pdf") {
		t.Errorf("preview should list the row's current lines, got:\n%s", stderr)
	}
	if got := f.rows[176525]; len(got) != 2 || got[1]["CopyToTargetDoc"] != "tYES" || got[1]["U_CHK2"] != "OK" {
		t.Errorf("row should end with 2 ticked lines, got %v", got)
	}
}

func TestAttachFillsAnEmptyStringApproveStamp(t *testing.T) {
	f := newFakeAttachSAP(t, true)
	withTTY(t, false)
	f.rows[900] = []map[string]interface{}{
		{"LineNum": int64(1), "FileName": "x", "FileExtension": "pdf", "FileSize": float64(5), "U_CHK": float64(5), "U_CHK2": "", "CopyToTargetDoc": "tYES"},
	}

	if _, _, err := execWrite(t, "", "attach", "--row", "900", "--yes"); err != nil {
		t.Fatalf("an empty U_CHK2 must be filled, not reported forever: %v", err)
	}
	if f.rows[900][0]["U_CHK2"] != "OK" {
		t.Errorf("U_CHK2 = %v, want OK", f.rows[900][0]["U_CHK2"])
	}
}

func TestAttachRefusesAControlCharacterInTheName(t *testing.T) {
	f := newFakeAttachSAP(t, true)
	withTTY(t, false)
	p := filepath.Join(t.TempDir(), "bill\r\nX-Evil: 1.pdf")
	if err := os.WriteFile(p, []byte("%PDF"), 0o600); err != nil {
		t.Skipf("this filesystem cannot hold that name: %v", err)
	}

	_, _, err := execWrite(t, "", "attach", p, "--yes")
	requireUsageError(t, err, "control character")
	if f.requests != 0 || f.logins != 0 {
		t.Errorf("nothing may reach SAP")
	}
}
