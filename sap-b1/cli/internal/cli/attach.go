package cli

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"unicode"

	"github.com/spf13/cobra"

	"sapb1/internal/client"
	"sapb1/internal/errs"
)

// `sapb1 attach` is the one way to put a file on an SAP document from here, and
// the reason it exists is a tick box.
//
// A file uploaded through the Service Layer lands on its Attachments2 line with
// Copy to Target Document = tNO. The file then does not follow the document when
// it is copied onward — GRPO to A/P invoice, draft to posted — and nobody finds
// out until the A/P invoice has no bill on it. Of Oil's API uploads since
// 2026-08-20, 1,488 lines were tNO against 423 tYES. Daman, 2026-09-16 (C-0090):
// every line we attach, any book, any document, carries the tick.
//
// Until now that was a step in a recipe the AI followed by hand (curl the file,
// then PATCH the tick), and a step in a recipe can be skipped. Here it cannot:
// the command uploads, ticks every line of the row, reads the row back, and
// exits non-zero unless every line reads tYES.
//
// The Approve stamp (U_CHK = size in KB, U_CHK2 = 'OK') rides the same PATCH in
// the books whose ATC1 has those fields — Oil and Beverages. Mart has no U_CHK
// columns and refuses the whole PATCH on an unknown field. Which book has them is
// read off the row itself (the Service Layer returns every UDF key on a line,
// null or not), not from a list of company names.
func newAttachCmd() *cobra.Command {
	var yes, dryRun bool
	var row int64

	cmd := &cobra.Command{
		Use:   "attach <file> [<file>...]",
		Short: "Upload file(s) to one attachment row, Copy to Target Document ticked on every line",
		Long: `attach uploads one or more files as the lines of ONE Attachments2 row, then
ticks Copy to Target Document on every line of that row, reads the row back, and
fails unless every line reads tYES and every file it uploaded downloads back
byte-identical. In Oil and Beverages the same PATCH sets the Approve stamp
(U_CHK2 = OK, and U_CHK = size in KB where SAP knows the size) on any line where
it is empty; Mart has no such fields and gets the tick alone.

It prints the row number (AbsoluteEntry). Point the document at it yourself:

  sapb1 patch "Drafts(56551)" --data '{"AttachmentEntry": 178001}'

or put "AttachmentEntry" in the draft's own payload. One row per document —
never point two documents at the same row.

--row N adds the files to existing row N instead of creating one, and re-ticks
every line of it. With no files, --row N only ticks and verifies row N: that is
the recovery after an attach that stopped half way. The row is read and shown
before you confirm.

Each upload and the tick PATCH are separate writes in the write log. The log
records each file's name, size and sha256, never the file itself. --dry-run
shows what would be sent and contacts SAP not at all.

Once a row exists, a failure is never exit 5 or 6 ("nothing happened"):
  exit 8 — the row is there but not finished; the message names the fix
           (usually: sapb1 attach --row N --yes);
  exit 7 — a request's answer never came back; look at the row
           (sapb1 query Attachments2 --filter "AbsoluteEntry eq N") before
           sending any file again.`,
		Example: exampleBlock(
			`sapb1 attach "PICKSHIP-NCR-358-2026-09-02.pdf" --dry-run`,
			`sapb1 attach bill.pdf GRPO-2026086899-bill.pdf --company JIVO_BEVERAGES_HANADB --yes`,
			`sapb1 attach --row 178001 --yes`,
		),
		RunE: func(cmd *cobra.Command, args []string) error {
			return runAttach(cmd, args, row, yes, dryRun)
		},
	}

	cmd.Flags().Int64Var(&row, "row", 0, "add to (or with no files, only re-tick) this existing Attachments2 row instead of creating one")
	cmd.Flags().BoolVar(&yes, "yes", false, "skip the confirmation prompt — required when stdin is not a terminal")
	cmd.Flags().BoolVar(&dryRun, "dry-run", false, "print what WOULD be sent, then exit; contacts SAP not at all")
	return cmd
}

type attachFile struct {
	name    string
	content []byte
}

// attachLine is one line of the row as it read back after the tick.
type attachLine struct {
	LineNum         int64  `json:"lineNum"`
	FileName        string `json:"fileName"`
	CopyToTargetDoc string `json:"copyToTargetDoc"`
	ApproveStamp    string `json:"approveStamp,omitempty"`
}

func runAttach(cmd *cobra.Command, args []string, row int64, yes, dryRun bool) error {
	cfg, err := writeConfig(cmd)
	if err != nil {
		return err
	}
	if cmd.Flags().Changed("row") && row <= 0 {
		return &errs.UsageError{Msg: fmt.Sprintf("--row must be a positive Attachments2 row number, got %d", row)}
	}
	if len(args) == 0 && row == 0 {
		return &errs.UsageError{Msg: "no file given — sapb1 attach <file> [<file>...], or --row N to re-tick an existing row"}
	}

	// Every file is read before anything is sent: a typo in the third name must
	// not leave a row with two lines on it.
	files := make([]attachFile, 0, len(args))
	seen := map[string]string{}
	for _, p := range args {
		info, err := os.Stat(p)
		if err != nil {
			return &errs.UsageError{Msg: fmt.Sprintf("cannot read %q: %v — nothing was sent to SAP", p, err)}
		}
		if info.IsDir() {
			return &errs.UsageError{Msg: fmt.Sprintf("%q is a folder, not a file — nothing was sent to SAP", p)}
		}
		name := filepath.Base(p)
		if strings.IndexFunc(name, unicode.IsControl) >= 0 {
			return &errs.UsageError{Msg: fmt.Sprintf("%q has a control character (a line break or tab) in its name — rename it first; nothing was sent to SAP", p)}
		}
		// The name is the file's only identity on the share, and a line is found
		// again by it. Two files by one name on one row cannot be told apart.
		if prev, dup := seen[strings.ToLower(name)]; dup {
			return &errs.UsageError{Msg: fmt.Sprintf("%q and %q have the same file name — rename one; nothing was sent to SAP", prev, p)}
		}
		seen[strings.ToLower(name)] = p
		b, err := os.ReadFile(p)
		if err != nil {
			return &errs.UsageError{Msg: fmt.Sprintf("cannot read %q: %v — nothing was sent to SAP", p, err)}
		}
		if len(b) == 0 {
			return &errs.UsageError{Msg: fmt.Sprintf("%q is empty (0 bytes) — nothing was sent to SAP", p)}
		}
		files = append(files, attachFile{name: name, content: b})
	}

	target := "a NEW Attachments2 row"
	if row > 0 {
		target = fmt.Sprintf("existing Attachments2 row %d", row)
	}
	var plan strings.Builder
	fmt.Fprintf(&plan, "  company : %s\n", cfg.CompanyDB)
	fmt.Fprintf(&plan, "  user    : %s\n", cfg.User)
	fmt.Fprintf(&plan, "  target  : %s\n", target)
	for _, f := range files {
		fmt.Fprintf(&plan, "  upload  : %s (%s)\n", f.name, humanBytes(len(f.content)))
	}
	fmt.Fprintf(&plan, "  then    : PATCH every line of the row: CopyToTargetDoc = tYES (+ U_CHK/U_CHK2 'OK' where the book has them), read back ticks and bytes\n")

	if dryRun {
		if cfg.JSON {
			type dryFile struct {
				File  string `json:"file"`
				Bytes int    `json:"bytes"`
			}
			out := struct {
				DryRun    bool      `json:"dryRun"`
				CompanyDB string    `json:"companyDb"`
				Row       int64     `json:"row,omitempty"`
				Files     []dryFile `json:"files"`
			}{DryRun: true, CompanyDB: cfg.CompanyDB, Row: row, Files: []dryFile{}}
			for _, f := range files {
				out.Files = append(out.Files, dryFile{f.name, len(f.content)})
			}
			return renderJSONValue(cmd.OutOrStdout(), out)
		}
		fmt.Fprintln(cmd.OutOrStdout(), "DRY RUN — nothing was sent to SAP.")
		fmt.Fprint(cmd.OutOrStdout(), plan.String())
		fmt.Fprintln(cmd.OutOrStdout(), "Re-run the same command with --yes to send it.")
		return nil
	}

	c := client.New(cfg)
	errOut := cmd.ErrOrStderr()
	c.SetErrWriter(errOut)
	ctx := cmd.Context()

	// An existing row is read BEFORE the prompt, so the operator confirms against
	// what is actually on it. A mistyped N would otherwise put a vendor's bill on
	// somebody else's document, and an Attachments2 row cannot be deleted.
	existing := 0
	if row > 0 {
		lines, found, err := fetchAttachmentLines(ctx, c, row)
		if err != nil {
			return err
		}
		if !found {
			return &errs.UsageError{Msg: fmt.Sprintf("Attachments2 row %d does not exist in %s — nothing was sent to SAP", row, cfg.CompanyDB)}
		}
		existing = len(lines)
		names := make([]string, 0, len(lines))
		for _, l := range lines {
			names = append(names, lineFileName(l))
		}
		fmt.Fprintf(&plan, "  row now : %d line(s): %s\n", len(lines), strings.Join(names, ", "))
	}

	fmt.Fprintln(errOut, "About to WRITE to SAP:")
	fmt.Fprint(errOut, plan.String())
	if err := confirmPrompt(cmd, fmt.Sprintf("Type 'yes' to send this write to %s: ", cfg.CompanyDB), yes, stdinIsTTYFunc()); err != nil {
		return err
	}

	created := row == 0
	var uploadErr error
	var failed string
	for _, f := range files {
		res, err := c.UploadAttachment(ctx, row, f.name, f.content)
		if err != nil {
			uploadErr, failed = err, f.name
			break
		}
		if row == 0 {
			n, ok := int64Field(decodeWriteObject(res.Body), "AbsoluteEntry")
			if !ok {
				return &errs.WriteVerifyError{Msg: fmt.Sprintf(
					"SAP accepted the upload of %s (HTTP %d) but did not say which Attachments2 row it created, so the Copy to Target tick could not be set. "+
						"Find the row (%s), then run: sapb1 attach --row <N> --yes",
					f.name, res.Status, findNewRowHint)}
			}
			row = n
		}
	}
	if row == 0 {
		// The first upload failed: there is no row to tick.
		var unknown *errs.WriteOutcomeUnknownError
		if errors.As(uploadErr, &unknown) {
			return &errs.WriteOutcomeUnknownError{Msg: fmt.Sprintf(
				"%v\n  If the upload did land, it made a NEW Attachments2 row, still unticked. Find it (%s), then run: sapb1 attach --row <N> --yes. Do not send %s again until you have looked.",
				uploadErr, findNewRowHint, failed)}
		}
		return uploadErr
	}

	// The tick runs even when a later upload failed, so no line that did land is
	// left tNO.
	lines, stampErr := stampAttachmentRow(ctx, c, cfg.CompanyDB, row)
	if uploadErr == nil && stampErr == nil {
		stampErr = verifyUploadedBytes(ctx, c, row, lines, existing, files)
	}
	if uploadErr != nil || stampErr != nil {
		return attachFailure(row, created, failed, lines, uploadErr, stampErr)
	}

	out := cmd.OutOrStdout()
	if cfg.JSON {
		return renderJSONValue(out, struct {
			CompanyDB     string       `json:"companyDb"`
			AbsoluteEntry int64        `json:"absoluteEntry"`
			Lines         []attachLine `json:"lines"`
		}{cfg.CompanyDB, row, lines})
	}
	fmt.Fprintf(out, "Attachments2 row %d in %s — Copy to Target Document = tYES on all %d line(s), read back:\n", row, cfg.CompanyDB, len(lines))
	for _, l := range lines {
		stamp := ""
		if l.ApproveStamp != "" {
			stamp = "  U_CHK2 " + l.ApproveStamp
		}
		fmt.Fprintf(out, "  line %d  %s  %s%s\n", l.LineNum, l.FileName, l.CopyToTargetDoc, stamp)
	}
	if len(files) > 0 {
		fmt.Fprintf(out, "The %d uploaded file(s) read back byte-identical.\n", len(files))
	}
	fmt.Fprintf(out, "Point the document at it: \"AttachmentEntry\": %d\n", row)
	return nil
}

const findNewRowHint = `sapb1 query Attachments2 --orderby "AbsoluteEntry desc" --top 5`

// attachFailure turns a half-finished attach into ONE error whose exit code says
// what the operator must do next. Once a row exists, something is already in
// SAP, so it is never a plain API or network error (those read "nothing
// happened, fix and re-run", and a re-run would make a second row):
//
//   - 7 if any request's answer never came back — go look before re-sending;
//   - 8 otherwise — the row is there and not finished; the message says how.
//
// The causes are in the message, not the chain: an AuthError in the chain would
// outrank both codes in ExitCodeFor.
func attachFailure(row int64, created bool, failed string, lines []attachLine, uploadErr, stampErr error) error {
	var unknown *errs.WriteOutcomeUnknownError
	isUnknown := errors.As(uploadErr, &unknown) || errors.As(stampErr, &unknown)

	var b strings.Builder
	if uploadErr != nil {
		fmt.Fprintf(&b, "uploading %s to Attachments2 row %d failed: %v\n", failed, row, uploadErr)
		if errors.As(uploadErr, &unknown) {
			fmt.Fprintf(&b, "  %s may or may not have landed. LOOK before sending it again: sapb1 query Attachments2 --filter \"AbsoluteEntry eq %d\"\n", failed, row)
			fmt.Fprintf(&b, "  Then run sapb1 attach --row %d --yes (it ticks anything that landed late), and add only what is really missing: sapb1 attach --row %d <file> --yes\n", row, row)
		} else {
			fmt.Fprintf(&b, "  SAP refused it, so it is not on the row. Add it, and any file after it, with: sapb1 attach --row %d <file> --yes\n", row)
		}
	}
	switch {
	case stampErr != nil:
		fmt.Fprintf(&b, "  Row %d is not finished: %v\n  Run: sapb1 attach --row %d --yes", row, stampErr, row)
	case uploadErr != nil:
		fmt.Fprintf(&b, "  Row %d as read back holds %d line(s), each ticked Copy to Target.", row, len(lines))
	}
	if created {
		fmt.Fprintf(&b, "\n  (Row %d was created by this command.)", row)
	}
	msg := strings.TrimRight(b.String(), "\n")
	if isUnknown {
		return &errs.WriteOutcomeUnknownError{Msg: msg}
	}
	return &errs.WriteVerifyError{Msg: msg}
}

// stampAttachmentRow ticks Copy to Target Document on every line of row, fills
// the Approve stamp where the book has it and it is empty, and reads the row
// back. It returns the lines as they read back, or an error naming every line
// that is not tYES.
//
// Values already on a line are kept: a U_CHK or U_CHK2 somebody set is not ours
// to overwrite (an empty-string U_CHK2 counts as unset). U_CHK is filled from
// the line's FileSize, which SAP carries for API uploads; a line without one
// keeps U_CHK empty, which SAP's own 1120025 guard does not check. When every
// line already carries everything, no PATCH is sent.
func stampAttachmentRow(ctx context.Context, c *client.Client, company string, row int64) ([]attachLine, error) {
	raw, found, err := fetchAttachmentLines(ctx, c, row)
	if err != nil {
		return nil, err
	}
	if !found {
		return nil, fmt.Errorf("Attachments2 row %d does not read back (HTTP 404)", row)
	}

	var patch []map[string]interface{}
	for _, l := range raw {
		n, ok := int64Field(l, "LineNum")
		if !ok {
			return nil, fmt.Errorf("Attachments2 row %d has a line with no LineNum — cannot tick it; look at the row in SAP", row)
		}
		p := map[string]interface{}{"AbsoluteEntry": row, "LineNum": n}
		change := false
		if s, _ := l["CopyToTargetDoc"].(string); s != "tYES" {
			p["CopyToTargetDoc"] = "tYES"
			change = true
		}
		if _, hasStamp := l["U_CHK2"]; hasStamp {
			if s, _ := l["U_CHK2"].(string); s == "" {
				p["U_CHK2"] = "OK"
				change = true
			}
			if l["U_CHK"] == nil {
				if size, ok := int64Field(l, "FileSize"); ok {
					p["U_CHK"] = size
					change = true
				}
			}
		}
		if change {
			patch = append(patch, p)
		}
	}

	if len(patch) > 0 {
		body, err := json.Marshal(map[string]interface{}{"Attachments2_Lines": patch})
		if err != nil {
			return nil, err
		}
		if _, err := c.Update(ctx, "Attachments2("+strconv.FormatInt(row, 10)+")", body); err != nil {
			return nil, fmt.Errorf("the Copy to Target PATCH failed: %w", err)
		}
		if raw, found, err = fetchAttachmentLines(ctx, c, row); err != nil || !found {
			if err == nil {
				err = fmt.Errorf("HTTP 404")
			}
			return nil, fmt.Errorf("reading it back after the PATCH failed: %w", err)
		}
	}

	lines := make([]attachLine, 0, len(raw))
	var bad []string
	for _, l := range raw {
		n, _ := int64Field(l, "LineNum")
		name := lineFileName(l)
		ctd, _ := l["CopyToTargetDoc"].(string)
		al := attachLine{LineNum: n, FileName: name, CopyToTargetDoc: ctd}
		if _, hasStamp := l["U_CHK2"]; hasStamp {
			al.ApproveStamp, _ = l["U_CHK2"].(string)
			if al.ApproveStamp == "" {
				bad = append(bad, fmt.Sprintf("line %d (%s) U_CHK2 is empty", n, name))
			}
		}
		if ctd != "tYES" {
			bad = append(bad, fmt.Sprintf("line %d (%s) CopyToTargetDoc=%q", n, name, ctd))
		}
		lines = append(lines, al)
	}
	if len(bad) > 0 {
		return lines, fmt.Errorf("row %d in %s did not read back ticked: %s", row, company, strings.Join(bad, "; "))
	}
	return lines, nil
}

// verifyUploadedBytes downloads every file this run uploaded and compares it
// with what was sent. The tick proves the row is right; only the bytes prove
// the document will open the right paper. The Service Layer appends lines in
// order, so file i of this run is line existing+i+1.
func verifyUploadedBytes(ctx context.Context, c *client.Client, row int64, lines []attachLine, existing int, files []attachFile) error {
	byNum := map[int64]string{}
	for _, l := range lines {
		byNum[l.LineNum] = l.FileName
	}
	var bad []string
	for i, f := range files {
		ln := int64(existing + i + 1)
		name, ok := byNum[ln]
		if !ok {
			bad = append(bad, fmt.Sprintf("%s: row has no line %d", f.name, ln))
			continue
		}
		got, err := c.DownloadAttachment(ctx, row, name)
		if err != nil {
			bad = append(bad, fmt.Sprintf("%s: downloading line %d (%s) failed: %v", f.name, ln, name, err))
			continue
		}
		if !bytes.Equal(got, f.content) {
			bad = append(bad, fmt.Sprintf("%s: line %d (%s) reads back as %s, not the %s that was sent", f.name, ln, name, humanBytes(len(got)), humanBytes(len(f.content))))
		}
	}
	if len(bad) > 0 {
		return fmt.Errorf("the ticks are set, but the files did not read back as sent — look at the row in SAP before pointing a document at it: %s", strings.Join(bad, "; "))
	}
	return nil
}

// fetchAttachmentLines reads row and returns its Attachments2_Lines. found is
// false when SAP answered 404.
func fetchAttachmentLines(ctx context.Context, c *client.Client, row int64) ([]map[string]interface{}, bool, error) {
	res, err := c.GetEntity(ctx, "Attachments2", row)
	if err != nil {
		return nil, false, err
	}
	if !res.Found {
		return nil, false, nil
	}
	dec := json.NewDecoder(bytes.NewReader(res.Body))
	dec.UseNumber()
	var obj struct {
		Lines []map[string]interface{} `json:"Attachments2_Lines"`
	}
	if err := dec.Decode(&obj); err != nil {
		return nil, true, fmt.Errorf("Attachments2 row %d read back as something that is not a row: %w", row, err)
	}
	if len(obj.Lines) == 0 {
		return nil, true, fmt.Errorf("Attachments2 row %d read back with no lines", row)
	}
	return obj.Lines, true, nil
}

// lineFileName is a line's full file name as the Service Layer finds it again:
// FileName + "." + FileExtension.
func lineFileName(l map[string]interface{}) string {
	name, _ := l["FileName"].(string)
	if ext, _ := l["FileExtension"].(string); ext != "" {
		name += "." + ext
	}
	return name
}

// int64Field reads a whole number out of a decoded object whose numbers were
// kept as json.Number.
func int64Field(obj map[string]interface{}, key string) (int64, bool) {
	if obj == nil {
		return 0, false
	}
	switch v := obj[key].(type) {
	case json.Number:
		n, err := v.Int64()
		return n, err == nil
	case float64:
		return int64(v), v == float64(int64(v))
	}
	return 0, false
}

func humanBytes(n int) string {
	if n < 1024 {
		return fmt.Sprintf("%d bytes", n)
	}
	return fmt.Sprintf("%d KB", (n+1023)/1024)
}
